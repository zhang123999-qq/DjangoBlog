"""Development settings for project."""

import os
from .base import *

# =============================================================================
# 开发环境标识
# =============================================================================

ENVIRONMENT = 'development'

# =============================================================================
# 调试配置
# =============================================================================

DEBUG = True

# 开发环境允许所有主机
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# =============================================================================
# 数据库配置
# =============================================================================

# 读取环境变量
db_engine = os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3')
db_name = os.environ.get('DB_NAME', 'db.sqlite3')

if 'mysql' in db_engine:
    # MySQL 配置
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'djangoblog'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
    print(f"[SETTINGS] 使用开发环境配置 (MySQL: {db_name})")
else:
    # SQLite 配置
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / db_name,
        }
    }
    print(f"[SETTINGS] 使用开发环境配置 (SQLite)")

# =============================================================================
# 缓存配置
# =============================================================================

use_redis = os.environ.get('USE_REDIS', '').lower() == 'true'
redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')

if use_redis:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': redis_url,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# =============================================================================
# 邮件配置 - 开发环境打印到控制台
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =============================================================================
# 静态文件 - 开发环境使用 Django 默认
# =============================================================================

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# =============================================================================
# 日志配置 - 开发环境更详细
# =============================================================================

LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['root']['level'] = 'DEBUG'

# 创建必要的目录
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'tmp' / 'session', exist_ok=True)

# =============================================================================
# 开发环境特定设置
# =============================================================================

# 禁用安装向导（开发环境不需要）
ENABLE_INSTALLER = False

# 禁用 axes（开发环境方便测试）
AXES_ENABLED = False
