"""编辑器/通用上传 API（安全加固版 v4：可选异步隔离扫描）"""

import logging
import socket
import struct
import uuid
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from rest_framework import permissions, status
from rest_framework.decorators import api_view, parser_classes, permission_classes, throttle_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

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

# 文件上传：保守白名单（可按业务扩展）
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

# ClamAV（可选）
CLAMAV_ENABLED = getattr(settings, 'UPLOAD_CLAMAV_ENABLED', False)
CLAMAV_HOST = getattr(settings, 'UPLOAD_CLAMAV_HOST', '127.0.0.1')
CLAMAV_PORT = getattr(settings, 'UPLOAD_CLAMAV_PORT', 3310)
CLAMAV_TIMEOUT = getattr(settings, 'UPLOAD_CLAMAV_TIMEOUT', 5)
CLAMAV_FAIL_CLOSED = getattr(settings, 'UPLOAD_CLAMAV_FAIL_CLOSED', False)

# 异步隔离扫描（仅对通用文件上传生效）
UPLOAD_ASYNC_PIPELINE_ENABLED = getattr(settings, 'UPLOAD_ASYNC_PIPELINE_ENABLED', False)
UPLOAD_STATUS_TTL = getattr(settings, 'UPLOAD_STATUS_TTL', 24 * 3600)


def _safe_extension(filename: str) -> str:
    if '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[-1].lower().strip()


def _peek_header(upload, size: int = 32) -> bytes:
    pos = upload.tell()
    header = upload.read(size)
    upload.seek(pos)
    return header


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
    """检测危险文件头。"""
    header = _peek_header(upload, 32)
    if header.startswith(b'MZ') or header.startswith(b'\x7fELF') or header.startswith(b'#!'):
        return True
    return False


def _save_upload(upload, folder: str) -> str:
    ext = _safe_extension(upload.name)
    today = datetime.now().strftime('%Y/%m')
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    relative_path = f"uploads/{folder}/{today}/{filename}"

    saved_path = default_storage.save(relative_path, upload)
    return f"{settings.MEDIA_URL}{saved_path}"


def _clamav_scan_fileobj(file_obj) -> tuple[bool, str]:
    """使用 clamd INSTREAM 协议扫描文件对象。"""
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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def upload_status(request, upload_id: str):
    """查询异步上传处理状态。"""
    data = cache.get(f'upload:status:{upload_id}')
    if not data:
        return Response({'error': '上传任务不存在或已过期'}, status=status.HTTP_404_NOT_FOUND)
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UploadRateThrottle])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    """TinyMCE 图片上传接口（仅登录用户，同步返回 location）。"""
    upload = request.FILES.get('file')
    if not upload:
        return Response({'error': '没有上传文件'}, status=status.HTTP_400_BAD_REQUEST)

    if upload.size > 5 * 1024 * 1024:
        return Response({'error': '文件大小不能超过5MB'}, status=status.HTTP_400_BAD_REQUEST)

    ext = _safe_extension(upload.name)
    if upload.content_type not in IMAGE_ALLOWED_MIME_TYPES or ext not in IMAGE_ALLOWED_EXTENSIONS:
        return Response({'error': '不支持的图片类型'}, status=status.HTTP_400_BAD_REQUEST)

    if not _validate_image_magic(upload, ext):
        return Response({'error': '图片文件头校验失败'}, status=status.HTTP_400_BAD_REQUEST)

    clean, detail = _scan_with_clamav(upload)
    if not clean:
        logger.warning('upload_image blocked by clamav: %s', detail)
        return Response({'error': '文件安全扫描未通过'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        file_url = _save_upload(upload, 'images')
        return Response({'location': file_url}, status=status.HTTP_200_OK)
    except Exception:
        logger.exception('upload_image failed')
        return Response({'error': '上传失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UploadRateThrottle])
@parser_classes([MultiPartParser, FormParser])
def upload_file(request):
    """通用文件上传接口（仅登录用户）。"""
    upload = request.FILES.get('file')
    if not upload:
        return Response({'error': '没有上传文件'}, status=status.HTTP_400_BAD_REQUEST)

    if upload.size > 10 * 1024 * 1024:
        return Response({'error': '文件大小不能超过10MB'}, status=status.HTTP_400_BAD_REQUEST)

    ext = _safe_extension(upload.name)

    if ext in DANGEROUS_FILE_EXTENSIONS:
        return Response({'error': '不允许上传该类型文件'}, status=status.HTTP_400_BAD_REQUEST)

    if ext not in FILE_ALLOWED_EXTENSIONS:
        return Response({'error': '文件类型不在允许列表'}, status=status.HTTP_400_BAD_REQUEST)

    if _contains_dangerous_magic(upload, ext):
        return Response({'error': '检测到危险文件头，上传被拒绝'}, status=status.HTTP_400_BAD_REQUEST)

    # v4：可选异步隔离扫描管线
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
                    'status_path': f"/api/upload/status/{upload_id}/",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception:
            logger.exception('upload_file async pipeline failed')
            return Response({'error': '上传失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 同步流程
    clean, detail = _scan_with_clamav(upload)
    if not clean:
        logger.warning('upload_file blocked by clamav: %s', detail)
        return Response({'error': '文件安全扫描未通过'}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response({'error': '上传失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
