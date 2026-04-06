"""Test settings for pytest smoke/CI.

目标：完全隔离外部依赖（MySQL/Redis），确保 CI 与本地测试稳定。
"""

from .base import BASE_DIR
from .development import *  # noqa

# 测试环境标识
ENVIRONMENT = 'test'
TESTING = True  # 用于跳过验证码等验证
DEBUG = True  # 测试环境保持 DEBUG=True，避免安全警告，同时让 API 文档端点可用

# 强制使用 SQLite，避免继承宿主机 DB_ENGINE=MySQL 等环境变量
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# 强制使用本地内存缓存，避免 Redis 依赖
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'djangoblog-test-cache',
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# 减少测试成本
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# 加速测试中的静态文件处理
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# 防止测试中被 HTTPS 强制重定向影响断言
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
