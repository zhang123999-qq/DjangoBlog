"""编辑器/通用上传 API（安全加固版 v4：可选异步隔离扫描）"""

import logging
import socket
import struct
import uuid
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.decorators import api_view, parser_classes, permission_classes, throttle_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.core.error_codes import ErrorCodes, api_error_payload

logger = logging.getLogger(__name__)


class UploadRateThrottle(UserRateThrottle):
    scope = 'upload'


IMAGE_ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
}
IMAGE_ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

FILE_ALLOWED_EXTENSIONS = {
    'pdf', 'txt', 'md', 'csv', 'json',
    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'zip', '7z', 'rar',
    'jpg', 'jpeg', 'png', 'gif', 'webp',
}

DANGEROUS_FILE_EXTENSIONS = {
    'exe', 'dll', 'bat', 'cmd', 'ps1', 'sh', 'com', 'msi', 'scr',
    'php', 'phtml', 'jsp', 'asp', 'aspx', 'cgi', 'pl', 'py', 'rb', 'jar',
}

CLAMAV_ENABLED = getattr(settings, 'UPLOAD_CLAMAV_ENABLED', False)
CLAMAV_HOST = getattr(settings, 'UPLOAD_CLAMAV_HOST', '127.0.0.1')
CLAMAV_PORT = getattr(settings, 'UPLOAD_CLAMAV_PORT', 3310)
CLAMAV_TIMEOUT = getattr(settings, 'UPLOAD_CLAMAV_TIMEOUT', 5)
CLAMAV_FAIL_CLOSED = getattr(settings, 'UPLOAD_CLAMAV_FAIL_CLOSED', False)

UPLOAD_ASYNC_PIPELINE_ENABLED = getattr(settings, 'UPLOAD_ASYNC_PIPELINE_ENABLED', False)
UPLOAD_STATUS_TTL = getattr(settings, 'UPLOAD_STATUS_TTL', 24 * 3600)

ERROR_RESPONSE_SCHEMA = {
    'type': 'object',
    'properties': {
        'error_code': {'type': 'string'},
        'error': {'type': 'string'},
        'message': {'type': 'string'},
    },
    'required': ['error_code', 'error', 'message'],
}

UploadImageRequestSerializer = inline_serializer(
    name='UploadImageRequest',
    fields={
        'file': serializers.FileField(),
    },
)

UploadFileRequestSerializer = inline_serializer(
    name='UploadFileRequest',
    fields={
        'file': serializers.FileField(),
    },
)


def _safe_extension(filename: str) -> str:
    if '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[-1].lower().strip()


def _peek_header(upload, size: int = 32) -> bytes:
    pos = upload.tell()
    header = upload.read(size)
    upload.seek(pos)
    return bytes(header)


def _looks_like_webp(header: bytes) -> bool:
    return len(header) >= 12 and header.startswith(b'RIFF') and header[8:12] == b'WEBP'


def _validate_image_magic(upload, ext: str) -> bool:
    header = _peek_header(upload, 32)
    if ext in {'jpg', 'jpeg'}:
        return header.startswith(b'\xff\xd8\xff')
    if ext == 'png':
        return header.startswith(b'\x89PNG\r\n\x1a\n')
    if ext == 'gif':
        return header.startswith(b'GIF87a') or header.startswith(b'GIF89a')
    if ext == 'webp':
        return _looks_like_webp(header)
    return False


def _contains_dangerous_magic(upload, ext: str) -> bool:
    header = _peek_header(upload, 32)
    return header.startswith(b'MZ') or header.startswith(b'\x7fELF') or header.startswith(b'#!')


def _save_upload(upload, folder: str) -> str:
    ext = _safe_extension(upload.name)
    today = datetime.now().strftime('%Y/%m')
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    relative_path = f"uploads/{folder}/{today}/{filename}"
    saved_path = default_storage.save(relative_path, upload)
    return f"{settings.MEDIA_URL}{saved_path}"


def _clamav_scan_fileobj(file_obj) -> tuple[bool, str]:
    file_obj.seek(0)
    with socket.create_connection((CLAMAV_HOST, CLAMAV_PORT), timeout=CLAMAV_TIMEOUT) as sock:
        sock.sendall(b'zINSTREAM\0')
        for chunk in file_obj.chunks():
            sock.sendall(struct.pack('!I', len(chunk)))
            sock.sendall(chunk)
        sock.sendall(struct.pack('!I', 0))
        resp = sock.recv(4096).decode('utf-8', errors='ignore').strip()
    file_obj.seek(0)

    if 'OK' in resp:
        return True, resp
    if 'FOUND' in resp:
        return False, resp
    raise RuntimeError(f'clamav unexpected response: {resp}')


def _scan_with_clamav(file_obj) -> tuple[bool, str]:
    if not CLAMAV_ENABLED:
        return True, 'clamav disabled'
    try:
        return _clamav_scan_fileobj(file_obj)
    except Exception as e:
        logger.exception('clamav scan failed')
        if CLAMAV_FAIL_CLOSED:
            return False, f'clamav error (fail-closed): {e}'
        return True, f'clamav error (fail-open): {e}'


def _set_upload_status(upload_id: str, payload: dict):
    cache.set(f'upload:status:{upload_id}', payload, UPLOAD_STATUS_TTL)


@extend_schema(
    operation_id='upload_status',
    summary='查询异步上传状态',
    tags=['upload'],
    responses={
        200: OpenApiResponse(description='上传状态', response={
            'type': 'object',
            'properties': {
                'status': {'type': 'string'},
                'upload_id': {'type': 'string'},
                'location': {'type': 'string'},
                'reason': {'type': 'string'},
            },
        }),
        404: OpenApiResponse(
            description='任务不存在',
            response=ERROR_RESPONSE_SCHEMA,
            examples=[OpenApiExample('Task not found', value=api_error_payload(ErrorCodes.UPLOAD_TASK_NOT_FOUND))],
        ),
    },
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def upload_status(request, upload_id: str):
    data = cache.get(f'upload:status:{upload_id}')
    if not data:
        return Response(api_error_payload(ErrorCodes.UPLOAD_TASK_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)
    return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    operation_id='upload_image',
    summary='上传图片（同步）',
    tags=['upload'],
    request={'multipart/form-data': UploadImageRequestSerializer},
    responses={
        200: OpenApiResponse(description='上传成功', response={
            'type': 'object',
            'properties': {'location': {'type': 'string'}},
            'required': ['location'],
        }),
        400: OpenApiResponse(
            description='上传参数错误',
            response=ERROR_RESPONSE_SCHEMA,
            examples=[
                OpenApiExample('No file', value=api_error_payload(ErrorCodes.UPLOAD_NO_FILE)),
                OpenApiExample('Image too large', value=api_error_payload(ErrorCodes.UPLOAD_IMAGE_TOO_LARGE)),
                OpenApiExample('Image type not allowed', value=api_error_payload(ErrorCodes.UPLOAD_IMAGE_TYPE_NOT_ALLOWED)),
                OpenApiExample('Image magic invalid', value=api_error_payload(ErrorCodes.UPLOAD_IMAGE_MAGIC_INVALID)),
                OpenApiExample('Scan rejected', value=api_error_payload(ErrorCodes.UPLOAD_SECURITY_SCAN_REJECTED)),
            ],
        ),
        500: OpenApiResponse(
            description='上传保存失败',
            response=ERROR_RESPONSE_SCHEMA,
            examples=[OpenApiExample('Upload save failed', value=api_error_payload(ErrorCodes.UPLOAD_SAVE_FAILED))],
        ),
    },
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UploadRateThrottle])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    upload = request.FILES.get('file')
    if not upload:
        return Response(api_error_payload(ErrorCodes.UPLOAD_NO_FILE), status=status.HTTP_400_BAD_REQUEST)

    if upload.size > 5 * 1024 * 1024:
        return Response(api_error_payload(ErrorCodes.UPLOAD_IMAGE_TOO_LARGE), status=status.HTTP_400_BAD_REQUEST)

    ext = _safe_extension(upload.name)
    if upload.content_type not in IMAGE_ALLOWED_MIME_TYPES or ext not in IMAGE_ALLOWED_EXTENSIONS:
        return Response(api_error_payload(ErrorCodes.UPLOAD_IMAGE_TYPE_NOT_ALLOWED), status=status.HTTP_400_BAD_REQUEST)

    if not _validate_image_magic(upload, ext):
        return Response(api_error_payload(ErrorCodes.UPLOAD_IMAGE_MAGIC_INVALID), status=status.HTTP_400_BAD_REQUEST)

    clean, detail = _scan_with_clamav(upload)
    if not clean:
        logger.warning('upload_image blocked by clamav: %s', detail)
        return Response(api_error_payload(ErrorCodes.UPLOAD_SECURITY_SCAN_REJECTED), status=status.HTTP_400_BAD_REQUEST)

    try:
        file_url = _save_upload(upload, 'images')
        return Response({'location': file_url}, status=status.HTTP_200_OK)
    except Exception:
        logger.exception('upload_image failed')
        return Response(api_error_payload(ErrorCodes.UPLOAD_SAVE_FAILED), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id='upload_file',
    summary='上传通用文件（同步/异步）',
    tags=['upload'],
    request={'multipart/form-data': UploadFileRequestSerializer},
    responses={
        200: OpenApiResponse(description='同步上传成功', response={
            'type': 'object',
            'properties': {
                'location': {'type': 'string'},
                'filename': {'type': 'string'},
                'size': {'type': 'integer'},
            },
        }),
        202: OpenApiResponse(description='异步处理已入队', response={
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'pending'},
                'upload_id': {'type': 'string'},
                'task_id': {'type': 'string'},
                'status_path': {'type': 'string'},
            },
        }),
        400: OpenApiResponse(
            description='上传参数错误或安全校验失败',
            response=ERROR_RESPONSE_SCHEMA,
            examples=[
                OpenApiExample('No file', value=api_error_payload(ErrorCodes.UPLOAD_NO_FILE)),
                OpenApiExample('File too large', value=api_error_payload(ErrorCodes.UPLOAD_FILE_TOO_LARGE)),
                OpenApiExample('File type denied', value=api_error_payload(ErrorCodes.UPLOAD_FILE_TYPE_DENIED)),
                OpenApiExample('File ext not allowed', value=api_error_payload(ErrorCodes.UPLOAD_FILE_EXT_NOT_ALLOWED)),
                OpenApiExample('Dangerous magic', value=api_error_payload(ErrorCodes.UPLOAD_FILE_MAGIC_DENIED)),
                OpenApiExample('Scan rejected', value=api_error_payload(ErrorCodes.UPLOAD_SECURITY_SCAN_REJECTED)),
            ],
        ),
        500: OpenApiResponse(
            description='上传保存失败',
            response=ERROR_RESPONSE_SCHEMA,
            examples=[OpenApiExample('Upload save failed', value=api_error_payload(ErrorCodes.UPLOAD_SAVE_FAILED))],
        ),
    },
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UploadRateThrottle])
@parser_classes([MultiPartParser, FormParser])
def upload_file(request):
    upload = request.FILES.get('file')
    if not upload:
        return Response(api_error_payload(ErrorCodes.UPLOAD_NO_FILE), status=status.HTTP_400_BAD_REQUEST)

    if upload.size > 10 * 1024 * 1024:
        return Response(api_error_payload(ErrorCodes.UPLOAD_FILE_TOO_LARGE), status=status.HTTP_400_BAD_REQUEST)

    ext = _safe_extension(upload.name)
    if ext in DANGEROUS_FILE_EXTENSIONS:
        return Response(api_error_payload(ErrorCodes.UPLOAD_FILE_TYPE_DENIED), status=status.HTTP_400_BAD_REQUEST)

    if ext not in FILE_ALLOWED_EXTENSIONS:
        return Response(api_error_payload(ErrorCodes.UPLOAD_FILE_EXT_NOT_ALLOWED), status=status.HTTP_400_BAD_REQUEST)

    if _contains_dangerous_magic(upload, ext):
        return Response(api_error_payload(ErrorCodes.UPLOAD_FILE_MAGIC_DENIED), status=status.HTTP_400_BAD_REQUEST)

    if UPLOAD_ASYNC_PIPELINE_ENABLED:
        from apps.core.upload_tasks import process_quarantined_upload

        upload_id = uuid.uuid4().hex
        today = datetime.now().strftime('%Y/%m')
        quarantine_name = f'{upload_id}.{ext}' if ext else upload_id
        quarantine_path = f'uploads/quarantine/{today}/{quarantine_name}'

        try:
            default_storage.save(quarantine_path, upload)
            task = process_quarantined_upload.delay(
                upload_id=upload_id,
                quarantine_path=quarantine_path,
                ext=ext,
                original_name=upload.name,
            )
            _set_upload_status(
                upload_id,
                {
                    'status': 'pending',
                    'upload_id': upload_id,
                    'task_id': task.id,
                    'filename': upload.name,
                },
            )
            return Response(
                {
                    'status': 'pending',
                    'upload_id': upload_id,
                    'task_id': task.id,
                    'status_path': f'/api/upload/status/{upload_id}/',
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception:
            logger.exception('upload_file async pipeline failed')
            return Response(api_error_payload(ErrorCodes.UPLOAD_SAVE_FAILED), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    clean, detail = _scan_with_clamav(upload)
    if not clean:
        logger.warning('upload_file blocked by clamav: %s', detail)
        return Response(api_error_payload(ErrorCodes.UPLOAD_SECURITY_SCAN_REJECTED), status=status.HTTP_400_BAD_REQUEST)

    try:
        file_url = _save_upload(upload, 'files')
        return Response(
            {
                'location': file_url,
                'filename': upload.name,
                'size': upload.size,
            },
            status=status.HTTP_200_OK,
        )
    except Exception:
        logger.exception('upload_file failed')
        return Response(api_error_payload(ErrorCodes.UPLOAD_SAVE_FAILED), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
