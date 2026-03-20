#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def get_settings_module():
    """根据环境自动选择配置模块"""
    # 如果已设置，使用环境变量
    if os.environ.get('DJANGO_SETTINGS_MODULE'):
        return os.environ['DJANGO_SETTINGS_MODULE']
    
    # 根据 DEBUG 自动选择
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    if debug:
        return 'config.settings.development'
    else:
        return 'config.settings.production'

def main():
    """Run administrative tasks."""
    settings_module = get_settings_module()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    
    # 打印当前使用的配置
    if len(sys.argv) > 1 and sys.argv[1] in ['runserver', 'shell', 'dbshell']:
        print(f"[INFO] 使用配置: {settings_module}")
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
