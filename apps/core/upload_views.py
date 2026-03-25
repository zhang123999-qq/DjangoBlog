"""编辑器/通用上传 API（安全加固版）"""

import logging
import os
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

DANGEROUS_FILE_EXTENSIONS = {
    'exe', 'dll', 'bat', 'cmd', 'ps1', 'sh', 'com', 'msi', 'scr',
    'php', 'phtml', 'jsp', 'asp', 'aspx', 'cgi', 'pl', 'py', 'rb', 'jar',
}


def _safe_extension(filename: str) -> str:
    if '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[-1].lower().strip()


def _save_upload(upload, folder: str) -> str:
    ext = _safe_extension(upload.name)
    today = datetime.now().strftime('%Y/%m')
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    relative_path = f"uploads/{folder}/{today}/{filename}"

    saved_path = default_storage.save(relative_path, upload)
    return f"{settings.MEDIA_URL}{saved_path}"


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
