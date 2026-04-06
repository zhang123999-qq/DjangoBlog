"""
API 异常处理器

统一处理所有异常，返回一致的响应格式
"""

import logging
from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """
    自定义异常处理器

    统一处理所有异常，返回一致的响应格式:
    {
        "code": 4xx/5xx,
        "message": "错误信息",
        "success": false,
        "errors": {...}  # 可选
    }
    """
    # 先处理 Django 原生异常（Http404 等）
    if isinstance(exc, Http404):
        return Response({
            "code": 404,
            "message": "资源不存在",
            "success": False,
        }, status=status.HTTP_404_NOT_FOUND)

    # 调用 DRF 默认处理器
    response = drf_exception_handler(exc, context)

    if response is not None:
        # DRF 异常
        return _handle_drf_exception(exc, response, context)
    else:
        # Django 异常或其他异常
        return _handle_django_exception(exc, context)


def _handle_drf_exception(
    exc: APIException,
    response: Response,
    context: Dict[str, Any]
) -> Response:
    """处理 DRF 异常"""

    # 获取错误消息
    message = _get_error_message(exc)

    # 构建响应体
    body = {
        "code": response.status_code,
        "message": message,
        "success": False,
    }

    # 添加详细错误信息
    if hasattr(exc, 'detail') and exc.detail:
        if isinstance(exc.detail, dict):
            body["errors"] = exc.detail
        elif isinstance(exc.detail, list):
            body["errors"] = {"detail": exc.detail}

    # 记录日志
    _log_exception(exc, context, response.status_code)

    return Response(body, status=response.status_code)


def _handle_django_exception(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """处理 Django 异常"""

    # Http404
    if isinstance(exc, Http404):
        return Response({
            "code": 404,
            "message": "资源不存在",
            "success": False,
        }, status=status.HTTP_404_NOT_FOUND)

    # Django ValidationError
    if isinstance(exc, DjangoValidationError):
        errors = exc.message_dict if hasattr(exc, 'message_dict') else {"detail": exc.messages}
        return Response({
            "code": 400,
            "message": "数据验证失败",
            "success": False,
            "errors": errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    # 其他未处理异常
    logger.exception(
        f"未处理的异常: {exc.__class__.__name__}: {str(exc)}",
        extra={
            "view": context.get('view').__class__.__name__ if context.get('view') else None,
            "request": str(context.get('request')),
        }
    )

    return Response({
        "code": 500,
        "message": "服务器内部错误",
        "success": False,
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_error_message(exc) -> str:
    """获取错误消息"""

    # 特定异常的消息
    messages = {
        NotAuthenticated: "未授权，请先登录",
        AuthenticationFailed: "认证失败",
        PermissionDenied: "无权限访问",
        NotFound: "资源不存在",
        Throttled: "请求过于频繁，请稍后再试",
        Http404: "资源不存在",
    }

    for exc_class, msg in messages.items():
        if isinstance(exc, exc_class):
            return msg

    # ValidationError
    if isinstance(exc, ValidationError):
        return "数据验证失败"

    # 使用默认消息
    if hasattr(exc, 'detail') and exc.detail:
        if isinstance(exc.detail, str):
            return exc.detail
        elif isinstance(exc.detail, dict):
            # 取第一个错误消息
            for key, value in exc.detail.items():
                if isinstance(value, list) and value:
                    return f"{key}: {value[0]}"
                return str(value)

    return "请求失败"


def _log_exception(exc: Exception, context: Dict[str, Any], status_code: int):
    """记录异常日志"""

    view = context.get('view')
    request = context.get('request')

    log_data = {
        "exception": exc.__class__.__name__,
        "message": str(exc),
        "status_code": status_code,
        "view": view.__class__.__name__ if view else None,
        "method": request.method if request else None,
        "path": request.path if request else None,
    }

    # 4xx 警告，5xx 错误
    if status_code >= 500:
        logger.error("API 异常: %(exception)s - %(message)s", log_data, exc_info=True)
    elif status_code >= 400:
        logger.warning("API 异常: %(exception)s - %(message)s", log_data)


# 自定义异常类
class BusinessError(APIException):
    """业务异常基类"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "业务处理失败"
    default_code = "business_error"


class ResourceNotFound(BusinessError):
    """资源不存在"""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "资源不存在"
    default_code = "resource_not_found"


class PermissionDeniedError(BusinessError):
    """权限不足"""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "权限不足"
    default_code = "permission_denied"


class RateLimitedError(BusinessError):
    """请求限流"""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "请求过于频繁"
    default_code = "rate_limited"
