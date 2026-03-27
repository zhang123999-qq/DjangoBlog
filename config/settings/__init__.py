"""
DjangoBlog 设置模块

环境配置：
- development.py - 开发环境 (SQLite / MySQL)
- production.py  - 生产环境 (MySQL + 可选 Redis)

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


def setup_pymysql() -> None:
    """配置 PyMySQL 作为 MySQL 驱动（替代 mysqlclient）。"""
    try:
        import pymysql

        pymysql.install_as_MySQLdb()
        # 兼容 Django 版本检查
        pymysql.version_info = (2, 2, 0, 'final', 0)
    except ImportError:
        # 开发环境用 SQLite 时允许未安装 PyMySQL
        pass


def get_settings_module() -> str:
    """获取设置模块。"""
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE')

    if settings_module:
        return settings_module

    # 根据 DEBUG 环境变量自动选择
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    if debug:
        return 'config.settings.development'
    return 'config.settings.production'


# 在 settings 包被导入时即完成 MySQL 驱动兼容注入
setup_pymysql()

# 设置默认配置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_module())
