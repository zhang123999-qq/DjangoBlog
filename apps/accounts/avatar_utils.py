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
    # 头像目录
    avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
    
    # 支持的头像格式
    extensions = ['.png', '.jpg', '.jpeg', '.gif']
    
    # 获取所有头像文件
    avatars = []
    if os.path.exists(avatar_dir):
        for file in os.listdir(avatar_dir):
            file_path = os.path.join(avatar_dir, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    avatars.append(file)
    
    if not avatars:
        # 如果没有头像，返回None（使用默认头像）
        return None
    
    # 随机选择一个头像，返回相对路径
    selected = random.choice(avatars)
    return f'avatars/{selected}'


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
