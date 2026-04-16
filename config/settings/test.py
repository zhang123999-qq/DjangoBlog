"""Test settings for pytest smoke/CI.

目标：完全隔离外部依赖（MySQL/Redis），确保 CI 与本地测试稳定。
"""

import os

from .base import BASE_DIR
from .development import *  # noqa: F401,F403,E402

# 测试环境标识
ENVIRONMENT = "test"
TESTING = True  # 用于跳过验证码等验证
# 根据环境变量设置 DEBUG，默认为 True
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

# 根据环境变量选择数据库引擎
db_engine = os.environ.get("DB_ENGINE", "sqlite").lower()

if db_engine == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "djangoblog_test"),
            "USER": os.environ.get("DB_USER", "testuser"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "testpass"),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",
        }
    }

# 根据环境变量选择缓存后端
use_redis = os.environ.get("USE_REDIS", "").lower() == "true"

if use_redis:
    redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1")
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": redis_url,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_CLASS": "redis.connection.BlockingConnectionPool",
                "CONNECTION_POOL_CLASS_KWARGS": {
                    "max_connections": 20,
                    "timeout": 10,
                },
            }
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
else:
    # 强制使用本地内存缓存，避免 Redis 依赖
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "djangoblog-test-cache",
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.db"

# 减少测试成本
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# 加速测试中的静态文件处理
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# 防止测试中被 HTTPS 强制重定向影响断言
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
