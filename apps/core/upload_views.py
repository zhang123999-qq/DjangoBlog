"""编辑器/通用上传 API（安全加固版 v2：MIME + 魔数双检）"""

import logging
import socket
import struct
import uuid
from datetime import datetime

from django.conf import settings
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

# 常见可执行/脚本文件头（魔数）
DANGEROUS_MAGIC_HEADERS = [
    b'MZ',                 # Windows PE/EXE/DLL
    b'#!',                 # shebang script
    b'\x7fELF',            # Linux ELF
    b'PK\x03\x04',        # zip (不一定危险，后续按扩展放行)
]

# 图片魔数
IMAGE_MAGIC = {
    'jpg': [b'\xff\xd8\xff'],
    'jpeg': [b'\xff\xd8\xff'],
    'png': [b'\x89PNG\r\n\x1a\n'],
    'gif': [b'GIF87a', b'GIF89a'],
    'webp': [b'RIFF'],  # 需额外检查 WEBP 标识
}


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
    patterns = IMAGE_MAGIC.get(ext, [])
    if not patterns:
        return False

    if ext == 'webp':
        return _looks_like_webp(header)

    return any(header.startswith(p) for p in patterns)


def _contains_dangerous_magic(upload, ext: str) -> bool:
    """
    检测危险文件头。
    注意：ZIP 在业务白名单中允许（docx/xlsx/pptx/zip 等），因此仅对“可执行特征”严格拦截。
    """
    header = _peek_header(upload, 32)

    # 强拦截：MZ / ELF / shebang
    if header.startswith(b'MZ') or header.startswith(b'\x7fELF') or header.startswith(b'#!'):
        return True

    # PK\x03\x04 是 zip 容器，不直接判危险
    return False


def _save_upload(upload, folder: str) -> str:
    ext = _safe_extension(upload.name)
    today = datetime.now().strftime('%Y/%m')
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    relative_path = f"uploads/{folder}/{today}/{filename}"

    saved_path = default_storage.save(relative_path, upload)
    return f"{settings.MEDIA_URL}{saved_path}"


def _clamav_scan_stream(upload) -> tuple[bool, str]:
    """
    使用 clamd INSTREAM 协议扫描上传文件（不落盘）。
    返回: (is_clean, message)
    """
    # 兼容不同文件对象
    upload.seek(0)

    with socket.create_connection((CLAMAV_HOST, CLAMAV_PORT), timeout=CLAMAV_TIMEOUT) as sock:
        # zINSTREAM\0（新版 clamd 推荐）
        sock.sendall(b'zINSTREAM\0')

        for chunk in upload.chunks():
            sock.sendall(struct.pack('!I', len(chunk)))
            sock.sendall(chunk)

        # 发送结束块
        sock.sendall(struct.pack('!I', 0))

        resp = sock.recv(4096).decode('utf-8', errors='ignore').strip()

    upload.seek(0)

    if 'OK' in resp:
        return True, resp
    if 'FOUND' in resp:
        return False, resp

    # 未知响应按异常处理
    raise RuntimeError(f'clamav unexpected response: {resp}')


def _scan_with_clamav(upload) -> tuple[bool, str]:
    """
    ClamAV 扫描门面：支持 fail-open / fail-closed。
    """
    if not CLAMAV_ENABLED:
        return True, 'clamav disabled'

    try:
        return _clamav_scan_stream(upload)
    except Exception as e:
        logger.exception('clamav scan failed')
        if CLAMAV_FAIL_CLOSED:
            return False, f'clamav error (fail-closed): {e}'
        return True, f'clamav error (fail-open): {e}'


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UploadRateThrottle])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    """TinyMCE 图片上传接口（仅登录用户）"""
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
    """通用文件上传接口（仅登录用户）"""
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
