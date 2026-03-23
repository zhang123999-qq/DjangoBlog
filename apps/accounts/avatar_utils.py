"""
随机头像工具
"""
import os
import random
from django.conf import settings


def get_random_avatar():
    """
    随机获取一个默认头像路径
    
    Returns:
        str: 头像相对路径（用于ImageField）
    """
    # 头像目录 - 从 static/img/avatars 获取
    avatar_dir = os.path.join(settings.BASE_DIR, 'static', 'img', 'avatars')
    
    # 支持的头像格式
    extensions = ['.png', '.jpg', '.jpeg', '.gif']
    
    # 获取所有头像文件
    avatars = []
    if os.path.exists(avatar_dir):
        for file in os.listdir(avatar_dir):
            file_path = os.path.join(avatar_dir, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions and not file.startswith('README'):
                    avatars.append(file)
    
    if not avatars:
        # 如果没有头像，返回默认头像
        return 'avatars/default-avatar.png'
    
    # 随机选择一个头像
    selected = random.choice(avatars)
    
    # 复制到 media/avatars 目录
    import shutil
    media_avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
    os.makedirs(media_avatar_dir, exist_ok=True)
    
    src_path = os.path.join(avatar_dir, selected)
    # 生成唯一文件名
    import uuid
    ext = os.path.splitext(selected)[1]
    unique_name = f'{uuid.uuid4().hex[:8]}{ext}'
    dst_path = os.path.join(media_avatar_dir, unique_name)
    
    shutil.copy2(src_path, dst_path)
    
    return f'avatars/{unique_name}'


def get_avatar_list():
    """
    获取所有可用头像列表
    
    Returns:
        list: 头像文件名列表
    """
    avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
    extensions = ['.png', '.jpg', '.jpeg', '.gif']
    
    avatars = []
    if os.path.exists(avatar_dir):
        for file in os.listdir(avatar_dir):
            file_path = os.path.join(avatar_dir, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    avatars.append(file)
    
    return sorted(avatars)


def get_avatar_count():
    """
    获取可用头像数量
    
    Returns:
        int: 头像数量
    """
    return len(get_avatar_list())
