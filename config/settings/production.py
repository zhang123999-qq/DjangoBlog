"""Production settings for project."""

import logging

from .base import *

# =============================================================================
# 生产环境标识
# =============================================================================

ENVIRONMENT = 'production'
logger = logging.getLogger(__name__)

# =============================================================================
# 安全配置
# =============================================================================

DEBUG = False

# 从环境变量读取允许的主机
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])

# 安全中间件（确保 SecurityMiddleware 在最前面）
if 'django.middleware.security.SecurityMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(0, 'django.middleware.security.SecurityMiddleware')

# 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# =============================================================================
# 数据库配置 - MySQL（生产环境）
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME', default='djangoblog'),
        'USER': env('DB_USER', default='root'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            # MySQL 连接池参数
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30,
        },
        # 连接池配置
        'CONN_MAX_AGE': 600,  # 10 分钟连接池
        'CONN_HEALTH_CHECKS': True,  # 连接健康检查
        'ATOMIC_REQUESTS': True,  # 为每个请求自动包装事务
    }
}

# =============================================================================
# 缓存配置 - Redis（生产环境）
# =============================================================================

# 强制使用 Redis
USE_REDIS = True
REDIS_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 1000,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'djangoblog',
        'TIMEOUT': 300,  # 默认5分钟
    }
}

# 使用 Redis 存储会话
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 1天

# =============================================================================
# 邮件配置 - 生产环境使用 SMTP
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@example.com')

# =============================================================================
# 静态文件 - 生产环境使用 WhiteNoise
# =============================================================================

# 确保 whitenoise 在中间件中
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    # 找到 SecurityMiddleware 的位置，在其后插入
    try:
        security_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
        MIDDLEWARE.insert(security_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    except ValueError:
        MIDDLEWARE.insert(0, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1年缓存
WHITENOISE_COMPRESS = True

# =============================================================================
# 日志配置 - 生产环境
# =============================================================================

# 生产环境日志级别更高
LOGGING['root']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'ERROR'

# 添加错误邮件通知（可选）
ADMINS = [
    ('Admin', env('ADMIN_EMAIL', default='admin@example.com')),
]

# =============================================================================
# Celery 配置 - 异步任务（生产环境）
# =============================================================================

CELERY_BROKER_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30分钟超时

# =============================================================================
# 性能优化
# =============================================================================

# 数据库连接持久化
DATABASES['default']['CONN_MAX_AGE'] = 600

# =============================================================================
# 生产环境检查
# =============================================================================

# 确保关键配置已设置
if not SECRET_KEY or SECRET_KEY == 'your-secret-key-here':
    import warnings
    warnings.warn("警告: SECRET_KEY 未设置或使用了默认值，请在 .env 文件中设置安全的密钥！")

if DEBUG:
    import warnings
    warnings.warn("警告: 生产环境 DEBUG 设置为 True，建议设置为 False！")

logger.info("[SETTINGS] 使用生产环境配置 (MySQL + Redis)")
