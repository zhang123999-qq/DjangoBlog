"""Production settings for project."""

import logging
from typing import cast

from .base import *

# =============================================================================
# 生产环境标识
# =============================================================================

ENVIRONMENT = "production"
logger = logging.getLogger(__name__)

# =============================================================================
# 安全配置
# =============================================================================

DEBUG = False

# 从环境变量读取允许的主机
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])

# 安全中间件（确保 SecurityMiddleware 在最前面）
if "django.middleware.security.SecurityMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(0, "django.middleware.security.SecurityMiddleware")

# 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
# ⚠️ 安全配置与 HTTPS 状态联动：避免纯 HTTP 部署时登录和 CSRF 失效
# 当使用反向代理 HTTPS（USE_X_FORWARDED_PROTO=True）时启用安全 cookie
_use_https = env.bool("USE_X_FORWARDED_PROTO", default=False)

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
# ⚠️ 修复: 安全 cookie 必须与 HTTPS 状态联动
# 纯 HTTP 部署时如果强制 Secure=True，会导致 cookie 无法写入，登录和 CSRF 完全失效
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=_use_https)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=_use_https)
# HSTS 仅在 HTTPS 时启用
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0 if not _use_https else 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=_use_https)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=_use_https)
SECURE_REFERRER_POLICY = env("SECURE_REFERRER_POLICY", default="same-origin")

# 反向代理 HTTPS 头（Nginx/Ingress）
if _use_https:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =============================================================================
# 数据库配置（生产环境）
# =============================================================================

db_engine = env("DB_ENGINE", default="django.db.backends.mysql")
if "sqlite" in db_engine:
    DATABASES = {
        "default": {
            "ENGINE": "apps.core.db_backends.sqlite3",
            "NAME": BASE_DIR / env("DB_NAME", default="db.sqlite3"),
            "ATOMIC_REQUESTS": True,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME", default="djangoblog"),
            "USER": env("DB_USER", default="root"),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                # MySQL 连接池参数
                "connect_timeout": 10,
                "read_timeout": 30,
                "write_timeout": 30,
            },
            # 连接池配置
            "CONN_MAX_AGE": 600,  # 10 分钟连接池
            "CONN_HEALTH_CHECKS": True,  # 连接健康检查
            "ATOMIC_REQUESTS": True,  # 为每个请求自动包装事务
        }
    }

# =============================================================================
# 缓存配置 - Redis（生产环境）
# =============================================================================

# Redis 可选：默认开启，可通过 USE_REDIS=False 回退到本地缓存
USE_REDIS = env.bool("USE_REDIS", default=True)
REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/1")

if USE_REDIS:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_CLASS": "redis.connection.BlockingConnectionPool",
                "CONNECTION_POOL_CLASS_KWARGS": {
                    "max_connections": 50,
                    "timeout": 20,
                },
                "MAX_CONNECTIONS": 1000,
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
            },
            "KEY_PREFIX": "djangoblog",
            "TIMEOUT": 300,  # 默认5分钟
        }
    }

    # 使用 Redis 存储会话
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "djangoblog-production",
            "TIMEOUT": 300,
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.db"

SESSION_COOKIE_AGE = 86400  # 1天

# =============================================================================
# 邮件配置 - 生产环境使用 SMTP
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# =============================================================================
# 静态文件 - 生产环境使用 WhiteNoise
# =============================================================================

# 确保 whitenoise 在中间件中
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    # 找到 SecurityMiddleware 的位置，在其后插入
    try:
        security_index = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
        MIDDLEWARE.insert(security_index + 1, "whitenoise.middleware.WhiteNoiseMiddleware")
    except ValueError:
        MIDDLEWARE.insert(0, "whitenoise.middleware.WhiteNoiseMiddleware")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
WHITENOISE_MAX_AGE = 31536000  # 1年缓存
WHITENOISE_COMPRESS = True

# =============================================================================
# 日志配置 - 生产环境
# =============================================================================

# 生产环境日志级别更高
logging_config = cast(dict, LOGGING)
logging_config["root"]["level"] = "WARNING"
logging_config["loggers"]["django"]["level"] = "ERROR"

# 添加错误邮件通知（可选）
ADMINS = [
    ("Admin", env("ADMIN_EMAIL", default="admin@example.com")),
]

# =============================================================================
# Celery 配置 - 异步任务（生产环境）
# =============================================================================

CELERY_BROKER_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30分钟超时

# =============================================================================
# 性能优化
# =============================================================================

# 数据库连接持久化
db_config = cast(dict, DATABASES)
db_config["default"]["CONN_MAX_AGE"] = 600

# =============================================================================
# 监控配置 (Prometheus + Sentry)
# =============================================================================

# Prometheus 监控
PROMETHEUS_ENABLED = env.bool("PROMETHEUS_ENABLED", default=False)
if PROMETHEUS_ENABLED:
    INSTALLED_APPS += ["django_prometheus"]
    MIDDLEWARE = [
        "django_prometheus.middleware.PrometheusBeforeMiddleware",
        *MIDDLEWARE,
        "django_prometheus.middleware.PrometheusAfterMiddleware",
    ]

# Sentry 错误追踪
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% 请求追踪
        profiles_sample_rate=0.1,  # 10% 性能分析
        environment=ENVIRONMENT,
        send_default_pii=False,  # 不发送用户隐私信息
    )

# =============================================================================
# 生产环境检查
# =============================================================================

# 确保关键配置已设置
if not SECRET_KEY or SECRET_KEY == "your-secret-key-here":  # nosec B105 - 仅用于检测占位符
    import warnings

    warnings.warn("警告: SECRET_KEY 未设置或使用了默认值，请在 .env 文件中设置安全的密钥！")

if DEBUG:
    import warnings

    warnings.warn("警告: 生产环境 DEBUG 设置为 True，建议设置为 False！")

logger.info("[SETTINGS] 使用生产环境配置 (MySQL + Redis)")
