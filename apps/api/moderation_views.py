"""Moderation API（带 OpenAPI 文档）"""

import logging
import time

from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.blog.models import Comment
from apps.core.error_codes import ErrorCodes, api_error_payload
from apps.forum.models import Reply, Topic
from moderation.services import approve_instance, reject_instance

ERROR_SCHEMA = {
    'type': 'object',
    'properties': {
        'error_code': {'type': 'string'},
        'error': {'type': 'string'},
        'message': {'type': 'string'},
    },
    'required': ['error_code', 'error', 'message'],
}


def _is_moderator(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def _get_content_model(content_type):
    return {
        'comment': Comment,
        'topic': Topic,
        'reply': Reply,
    }.get(content_type)


def _check_rate_limit(request):
    """每用户每分钟限流。"""
    limit = getattr(settings, 'MODERATION_API_RATE_LIMIT_PER_MIN', 120)
    user_id = getattr(request.user, 'id', None) or 'anon'
    from django.utils import timezone

    bucket = timezone.now().strftime('%Y%m%d%H%M')
    key = f'moderation:rate:{user_id}:{bucket}'

    count = cache.get(key, 0)
    if count >= limit:
        _metric_incr('rate_limited')
        logger.warning('moderation_api_rate_limited user=%s count=%s limit=%s', user_id, count, limit)
        return False

    cache.set(key, count + 1, 60)
    _metric_incr('requests_total')
    _record_user_hotspot(user_id)
    return True


def _enter_concurrency_guard(request):
    """每用户并发上限保护。"""
    max_conc = getattr(settings, 'MODERATION_API_MAX_CONCURRENCY', 20)
    user_id = getattr(request.user, 'id', None) or 'anon'
    key = f'moderation:conc:{user_id}'

    current = cache.get(key, 0)
    if current >= max_conc:
        _metric_incr('concurrency_limited')
        logger.warning('moderation_api_concurrency_limited user=%s current=%s limit=%s', user_id, current, max_conc)
        return None

    new_current = current + 1
    cache.set(key, new_current, 120)
    _record_peak_concurrency(user_id, new_current)
    return key


def _leave_concurrency_guard(key):
    if not key:
        return
    current = cache.get(key, 0)
    if current <= 1:
        cache.delete(key)
    else:
        cache.set(key, current - 1, 120)


def _metric_incr(name: str, delta: int = 1):
    """轻量计数器（按分钟桶），用于限流/并发命中可观测。"""
    from django.utils import timezone

    bucket = timezone.now().strftime('%Y%m%d%H%M')
    key = f'moderation:metric:{name}:{bucket}'
    count = cache.get(key, 0)
    cache.set(key, count + delta, 3600)


def _record_user_hotspot(user_id):
    """记录用户维度热点（分钟桶）。"""
    from django.utils import timezone

    bucket = timezone.now().strftime('%Y%m%d%H%M')
    key = f'moderation:metric:user:{user_id}:{bucket}'
    count = cache.get(key, 0)
    cache.set(key, count + 1, 3600)


def _record_peak_concurrency(user_id, current: int):
    """记录分钟级并发峰值。"""
    from django.utils import timezone

    bucket = timezone.now().strftime('%Y%m%d%H%M')
    global_key = f'moderation:metric:peak_concurrency:{bucket}'
    user_key = f'moderation:metric:peak_concurrency:user:{user_id}:{bucket}'

    global_peak = cache.get(global_key, 0)
    if current > global_peak:
        cache.set(global_key, current, 3600)

    user_peak = cache.get(user_key, 0)
    if current > user_peak:
        cache.set(user_key, current, 3600)


@extend_schema(
    operation_id='api_moderation_approve',
    summary='审核通过（JSON API）',
    tags=['moderation'],
    responses={
        200: OpenApiResponse(
            description='审核通过成功',
            response={
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'status': {'type': 'string', 'example': 'approved'},
                    'id': {'type': 'integer'},
                },
                'required': ['success', 'status', 'id'],
            },
        ),
        400: OpenApiResponse(
            description='内容类型错误',
            response=ERROR_SCHEMA,
            examples=[OpenApiExample('Invalid type', value=api_error_payload(ErrorCodes.MODERATION_INVALID_CONTENT_TYPE))],
        ),
        403: OpenApiResponse(
            description='权限不足',
            response=ERROR_SCHEMA,
            examples=[OpenApiExample('Permission denied', value=api_error_payload(ErrorCodes.MODERATION_PERMISSION_DENIED))],
        ),
        404: OpenApiResponse(
            description='对象不存在',
            response=ERROR_SCHEMA,
            examples=[OpenApiExample('Content not found', value=api_error_payload(ErrorCodes.MODERATION_CONTENT_NOT_FOUND))],
        ),
        429: OpenApiResponse(
            description='限流/并发保护触发',
            response=ERROR_SCHEMA,
            examples=[
                OpenApiExample('Rate limited', value=api_error_payload(ErrorCodes.MODERATION_API_RATE_LIMITED)),
                OpenApiExample('Concurrency limited', value=api_error_payload(ErrorCodes.MODERATION_API_CONCURRENCY_LIMITED)),
            ],
        ),
        500: OpenApiResponse(
            description='审核失败',
            response=ERROR_SCHEMA,
            examples=[OpenApiExample('Approve failed', value=api_error_payload(ErrorCodes.MODERATION_APPROVE_FAILED))],
        ),
    },
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def moderation_approve_api(request, content_type: str, content_id: int):
    start = time.perf_counter()
    user_id = getattr(request.user, 'id', None) or 'anon'

    if not _is_moderator(request.user):
        _metric_incr('permission_denied')
        return Response(api_error_payload(ErrorCodes.MODERATION_PERMISSION_DENIED), status=status.HTTP_403_FORBIDDEN)

    if not _check_rate_limit(request):
        return Response(api_error_payload(ErrorCodes.MODERATION_API_RATE_LIMITED), status=status.HTTP_429_TOO_MANY_REQUESTS)

    guard_key = _enter_concurrency_guard(request)
    if guard_key is None:
        return Response(api_error_payload(ErrorCodes.MODERATION_API_CONCURRENCY_LIMITED), status=status.HTTP_429_TOO_MANY_REQUESTS)

    try:
        model = _get_content_model(content_type)
        if model is None:
            _metric_incr('invalid_content_type')
            return Response(api_error_payload(ErrorCodes.MODERATION_INVALID_CONTENT_TYPE), status=status.HTTP_400_BAD_REQUEST)

        content = model.objects.filter(id=content_id).first()
        if content is None:
            _metric_incr('content_not_found')
            return Response(api_error_payload(ErrorCodes.MODERATION_CONTENT_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)

        approve_instance(content, request.user, note='')
        _metric_incr('approve_success')
        return Response({'success': True, 'status': 'approved', 'id': content_id}, status=status.HTTP_200_OK)
    except Exception:
        _metric_incr('approve_failed')
        logger.exception('moderation_approve_failed user=%s type=%s id=%s', user_id, content_type, content_id)
        return Response(api_error_payload(ErrorCodes.MODERATION_APPROVE_FAILED), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        _leave_concurrency_guard(guard_key)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info('moderation_approve_done user=%s type=%s id=%s elapsed_ms=%s', user_id, content_type, content_id, elapsed_ms)


@extend_schema(
    operation_id='api_moderation_reject',
    summary='审核拒绝（JSON API）',
    tags=['moderation'],
    request={
        'type': 'object',
        'properties': {
            'review_note': {'type': 'string', 'description': '审核备注'},
        },
    },
    responses={
        200: OpenApiResponse(
            description='审核拒绝成功',
            response={
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'status': {'type': 'string', 'example': 'rejected'},
                    'id': {'type': 'integer'},
                },
                'required': ['success', 'status', 'id'],
            },
        ),
        400: OpenApiResponse(
            description='内容类型错误',
            response=ERROR_SCHEMA,
            examples=[OpenApiExample('Invalid type', value=api_error_payload(ErrorCodes.MODERATION_INVALID_CONTENT_TYPE))],
        ),
        403: OpenApiResponse(
            description='权限不足',
            response=ERROR_SCHEMA,
            examples=[OpenApiExample('Permission denied', value=api_error_payload(ErrorCodes.MODERATION_PERMISSION_DENIED))],
        ),
        404: OpenApiResponse(
            description='对象不存在',
            response=ERROR_SCHEMA,
            examples=[OpenApiExample('Content not found', value=api_error_payload(ErrorCodes.MODERATION_CONTENT_NOT_FOUND))],
        ),
        429: OpenApiResponse(
            description='限流/并发保护触发',
            response=ERROR_SCHEMA,
            examples=[
                OpenApiExample('Rate limited', value=api_error_payload(ErrorCodes.MODERATION_API_RATE_LIMITED)),
                OpenApiExample('Concurrency limited', value=api_error_payload(ErrorCodes.MODERATION_API_CONCURRENCY_LIMITED)),
            ],
        ),
        500: OpenApiResponse(
            description='审核拒绝失败',
            response=ERROR_SCHEMA,
            examples=[OpenApiExample('Reject failed', value=api_error_payload(ErrorCodes.MODERATION_REJECT_FAILED))],
        ),
    },
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def moderation_reject_api(request, content_type: str, content_id: int):
    start = time.perf_counter()
    user_id = getattr(request.user, 'id', None) or 'anon'

    if not _is_moderator(request.user):
        _metric_incr('permission_denied')
        return Response(api_error_payload(ErrorCodes.MODERATION_PERMISSION_DENIED), status=status.HTTP_403_FORBIDDEN)

    if not _check_rate_limit(request):
        return Response(api_error_payload(ErrorCodes.MODERATION_API_RATE_LIMITED), status=status.HTTP_429_TOO_MANY_REQUESTS)

    guard_key = _enter_concurrency_guard(request)
    if guard_key is None:
        return Response(api_error_payload(ErrorCodes.MODERATION_API_CONCURRENCY_LIMITED), status=status.HTTP_429_TOO_MANY_REQUESTS)

    try:
        model = _get_content_model(content_type)
        if model is None:
            _metric_incr('invalid_content_type')
            return Response(api_error_payload(ErrorCodes.MODERATION_INVALID_CONTENT_TYPE), status=status.HTTP_400_BAD_REQUEST)

        content = model.objects.filter(id=content_id).first()
        if content is None:
            _metric_incr('content_not_found')
            return Response(api_error_payload(ErrorCodes.MODERATION_CONTENT_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)

        review_note = request.data.get('review_note', '') if hasattr(request.data, 'get') else ''
        reject_instance(content, request.user, note=review_note)
        _metric_incr('reject_success')
        return Response({'success': True, 'status': 'rejected', 'id': content_id}, status=status.HTTP_200_OK)
    except Exception:
        _metric_incr('reject_failed')
        logger.exception('moderation_reject_failed user=%s type=%s id=%s', user_id, content_type, content_id)
        return Response(api_error_payload(ErrorCodes.MODERATION_REJECT_FAILED), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        _leave_concurrency_guard(guard_key)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info('moderation_reject_done user=%s type=%s id=%s elapsed_ms=%s', user_id, content_type, content_id, elapsed_ms)
