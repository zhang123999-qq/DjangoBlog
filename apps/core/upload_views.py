"""
编辑器图片上传API
"""
import os
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.files.storage import default_storage


@csrf_exempt
@require_POST
def upload_image(request):
    """
    TinyMCE 图片上传接口
    返回格式: { "location": "图片URL" }
    """
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': '没有上传文件'}, status=400)
        
        upload = request.FILES['file']
        
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
        if upload.content_type not in allowed_types:
            return JsonResponse({'error': '不支持的文件类型'}, status=400)
        
        # 验证文件大小 (最大5MB)
        if upload.size > 5 * 1024 * 1024:
            return JsonResponse({'error': '文件大小不能超过5MB'}, status=400)
        
        # 生成文件名
        ext = upload.name.split('.')[-1].lower()
        today = datetime.now().strftime('%Y/%m')
        filename = f'{uuid.uuid4().hex}.{ext}'
        
        # 保存路径
        relative_path = f'uploads/images/{today}/{filename}'
        
        # 确保目录存在
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 保存文件
        with open(full_path, 'wb+') as destination:
            for chunk in upload.chunks():
                destination.write(chunk)
        
        # 返回URL
        file_url = f'{settings.MEDIA_URL}{relative_path}'
        
        return JsonResponse({'location': file_url})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def upload_file(request):
    """
    通用文件上传接口
    """
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': '没有上传文件'}, status=400)
        
        upload = request.FILES['file']
        
        # 验证文件大小 (最大10MB)
        if upload.size > 10 * 1024 * 1024:
            return JsonResponse({'error': '文件大小不能超过10MB'}, status=400)
        
        # 生成文件名
        ext = upload.name.split('.')[-1].lower() if '.' in upload.name else ''
        today = datetime.now().strftime('%Y/%m')
        filename = f'{uuid.uuid4().hex}.{ext}' if ext else uuid.uuid4().hex
        
        # 保存路径
        relative_path = f'uploads/files/{today}/{filename}'
        
        # 确保目录存在
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 保存文件
        with open(full_path, 'wb+') as destination:
            for chunk in upload.chunks():
                destination.write(chunk)
        
        # 返回URL
        file_url = f'{settings.MEDIA_URL}{relative_path}'
        
        return JsonResponse({
            'location': file_url,
            'filename': upload.name,
            'size': upload.size
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
