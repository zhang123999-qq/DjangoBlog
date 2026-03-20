"""
DjangoBlog 设置模块

环境配置：
- development.py - 开发环境 (SQLite)
- production.py  - 生产环境 (MySQL + Redis)

使用方式：
1. 开发环境：
   export DJANGO_SETTINGS_MODULE=config.settings.development
   python manage.py runserver

2. 生产环境：
   export DJANGO_SETTINGS_MODULE=config.settings.production
   python manage.py runserver

3. 使用默认（自动根据 DEBUG 判断）：
   python manage.py runserver
"""

import os

# 根据环境变量或默认选择配置
def get_settings_module():
    """获取设置模块"""
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE')
    
    if settings_module:
        return settings_module
    
    # 根据 DEBUG 环境变量自动选择
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    if debug:
        return 'config.settings.development'
    else:
        return 'config.settings.production'

# 设置默认配置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_module())
