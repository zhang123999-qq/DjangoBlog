"""Base settings for project."""

import os
import socket
import sys
from pathlib import Path
from typing import Any

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def get_local_ip():
    """获取本机局域网 IP 地址"""
    try:
        # 创建一个 UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到一个公共 DNS（不需要真正连接）
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return None


def get_allowed_hosts():
    """获取 ALLOWED_HOSTS 列表，自动包含本机 IP"""
    default_hosts = ['localhost', '127.0.0.1']

    # 尝试从环境变量读取
    env_hosts = os.environ.get('ALLOWED_HOSTS', '')
    if env_hosts:
        hosts = [h.strip() for h in env_hosts.split(',') if h.strip()]
    else:
        hosts = default_hosts.copy()

    # 添加本机局域网 IP
    local_ip = get_local_ip()
    if local_ip and local_ip not in hosts:
        hosts.append(local_ip)

    # 开发模式添加通配符（仅在 DEBUG=True 时）
    if os.environ.get('DEBUG', 'False').lower() == 'true':
        if '*' not in hosts:
            hosts.append('*')

    return hosts


# Initialize environ with defaults
env = environ.Env(
    DEBUG=(bool, False),
)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# ALLOWED_HOSTS - 自动支持局域网访问
ALLOWED_HOSTS = get_allowed_hosts()

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',

    # Third-party apps
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'compressor',
    'axes',

    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.blog',
    'apps.forum',
    'apps.tools',
    'apps.api',
    'moderation',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 安全头中间件（新增）
    'apps.core.security_headers.CSPMiddleware',
    'apps.core.security_headers.SecurityHeadersMiddleware',
    'apps.core.security_middleware.SecurityMonitorMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Sites 框架配置
SITE_ID = 1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - 默认使用 SQLite，可在环境配置中覆盖
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'apps.core.db_backends.sqlite3',  # 自定义后端，禁用外键约束
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUESTS': True,  # 为每个请求自动包装事务
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# AXES 防暴力破解配置
AXES_ENABLED = True
AXES_LOCK_OUT_AT_FAILURE = True
AXES_FAILURE_THRESHOLD = 5
AXES_LOCK_OUT_DURATION = 300
AXES_COOL_DOWN_TIME = 300
AXES_RESET_ON_SUCCESS = True
# AXES_USE_USER_AGENT 已弃用，使用 AXES_LOCKOUT_PARAMETERS 替代
AXES_LOCKOUT_PARAMETERS = [["ip_address"]]  # 仅按 IP 地址锁定
AXES_IP_WHITELIST: list[str] = []
AXES_IP_BLACKLIST: list[str] = []

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# 静态文件压缩
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

COMPRESS_ENABLED = not DEBUG

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # 必须放在第一位，支持 get_user
    'axes.backends.AxesStandaloneBackend',  # Axes 监控 backend
]

# Login settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Site settings
SITE_NAME = env('SITE_NAME', default='Django Blog')
SITE_TITLE = env('SITE_TITLE', default='Django Blog')

# 百度内容审核 API 配置
BAIDU_APP_ID = env('BAIDU_APP_ID', default='')
BAIDU_API_KEY = env('BAIDU_API_KEY', default='')
BAIDU_SECRET_KEY = env('BAIDU_SECRET_KEY', default='')
BAIDU_MODERATION_ENABLED = bool(BAIDU_APP_ID and BAIDU_API_KEY and BAIDU_SECRET_KEY)

# Caches - 将在环境配置中定义
CACHES: dict[str, Any] = {}

# Email settings
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# 创建日志目录
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Disable colorama on Windows to avoid OSError
if sys.platform == 'win32':
    os.environ['NO_COLOR'] = '1'

# REST Framework 配置
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('API_ANON_RATE', default='100/hour'),
        'user': env('API_USER_RATE', default='1000/hour'),
        'upload': env('API_UPLOAD_RATE', default='30/hour'),
        'api_read': env('API_READ_RATE', default='1200/hour'),
    },
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': env.int('API_PAGE_SIZE', default=20),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS 配置
INSTALLED_APPS += [
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
] + MIDDLEWARE

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True

# CSRF 配置
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# API 文档配置
SPECTACULAR_SETTINGS = {
    'TITLE': 'DjangoBlog API',
    'DESCRIPTION': '博客论坛系统 REST API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# 上传安全扫描（ClamAV，可选）
UPLOAD_CLAMAV_ENABLED = env.bool('UPLOAD_CLAMAV_ENABLED', default=False)
UPLOAD_CLAMAV_HOST = env('UPLOAD_CLAMAV_HOST', default='127.0.0.1')
UPLOAD_CLAMAV_PORT = env.int('UPLOAD_CLAMAV_PORT', default=3310)
UPLOAD_CLAMAV_TIMEOUT = env.int('UPLOAD_CLAMAV_TIMEOUT', default=5)
UPLOAD_CLAMAV_FAIL_CLOSED = env.bool('UPLOAD_CLAMAV_FAIL_CLOSED', default=False)

# 上传异步隔离扫描（v4）
UPLOAD_ASYNC_PIPELINE_ENABLED = env.bool('UPLOAD_ASYNC_PIPELINE_ENABLED', default=False)
UPLOAD_STATUS_TTL = env.int('UPLOAD_STATUS_TTL', default=86400)

# =============================================================================
# Celery 配置
# =============================================================================

# Celery Broker (Redis)
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# Celery 配置
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# 任务结果过期时间（秒）
CELERY_RESULT_EXPIRES = 3600

# 任务重试配置
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5分钟软超时
CELERY_TASK_TIME_LIMIT = 600  # 10分钟硬超时

# Beat 定时任务
CELERY_BEAT_SCHEDULE = {
    # ============================================================
    # 浏览量 Redis 同步（新增）
    # ============================================================
    # 每 5 分钟同步浏览量到数据库
    'sync-views-to-db': {
        'task': 'apps.blog.tasks.sync_views_to_db',
        'schedule': 300.0,  # 5 分钟
        'options': {'queue': 'low_priority'},
    },
    # 每小时更新热门文章
    'update-hot-posts': {
        'task': 'apps.blog.tasks.update_hot_posts',
        'schedule': 3600.0,  # 1 小时
        'options': {'queue': 'low_priority'},
    },
    # ============================================================
    # 审核系统任务
    # ============================================================
    # 每 6 小时检查待审核内容
    'check-pending-moderation': {
        'task': 'moderation.tasks.check_pending_moderation',
        'schedule': 21600.0,  # 6 小时 = 6 * 60 * 60 = 21600 秒
    },
    # 每天凌晨 2 点自动通过旧待审核内容
    'auto-approve-old-pending': {
        'task': 'moderation.tasks.auto_approve_old_pending',
        'schedule': 86400.0,  # 1 天 = 24 * 60 * 60 = 86400 秒
        'options': {'queue': 'low_priority'},
    },
    # 每天凌晨 3 点更新用户信誉连续无违规天数
    'update-reputation-clean-days': {
        'task': 'moderation.tasks.update_reputation_clean_days',
        'schedule': 86400.0,
        'options': {'queue': 'low_priority'},
    },
    # ============================================================
    # 性能维护任务
    # ============================================================
    # 每小时清理过期 Session
    'cleanup-expired-sessions': {
        'task': 'apps.core.maintenance_tasks.cleanup_expired_sessions',
        'schedule': 3600.0,  # 1 小时
        'options': {'queue': 'low_priority'},
    },
    # 每 6 小时缓存预热
    'warmup-cache': {
        'task': 'apps.core.maintenance_tasks.warmup_cache',
        'schedule': 21600.0,  # 6 小时
        'options': {'queue': 'low_priority'},
    },
    # 每天 1 点清理旧审核日志
    'cleanup-moderation-logs': {
        'task': 'apps.core.maintenance_tasks.cleanup_old_moderation_logs',
        'schedule': 86400.0,
        'options': {'queue': 'low_priority'},
    },
    # 每天凌晨 0 点生成统计数据
    'generate-statistics': {
        'task': 'apps.core.maintenance_tasks.generate_statistics',
        'schedule': 86400.0,
        'options': {'queue': 'low_priority'},
    },
    # 每周日凌晨 4 点优化数据库
    'optimize-database': {
        'task': 'apps.core.maintenance_tasks.optimize_database',
        'schedule': 604800.0,  # 1 周
        'options': {'queue': 'low_priority'},
    },
    # 每 5 分钟检查 Redis 健康
    'check-redis-health': {
        'task': 'apps.core.maintenance_tasks.check_redis_health',
        'schedule': 300.0,  # 5 分钟
        'options': {'queue': 'low_priority'},
    },
}

# =============================================================================
# 审核系统配置
# =============================================================================

# 审核模式
MODERATION_MODE = env('MODERATION_MODE', default='hybrid')  # auto/manual/hybrid

# AI 审核权重（0-1，越高越严格）
MODERATION_AI_THRESHOLD = env.float('MODERATION_AI_THRESHOLD', default=0.8)

# Moderation API 保护阈值（Phase 14）
MODERATION_API_RATE_LIMIT_PER_MIN = env.int('MODERATION_API_RATE_LIMIT_PER_MIN', default=120)
MODERATION_API_MAX_CONCURRENCY = env.int('MODERATION_API_MAX_CONCURRENCY', default=20)

# Moderation UI 告警阈值（Phase 19）
MODERATION_UI_ALERT_RATE_LIMITED = env.int('MODERATION_UI_ALERT_RATE_LIMITED', default=5)
MODERATION_UI_ALERT_CONCURRENCY_LIMITED = env.int('MODERATION_UI_ALERT_CONCURRENCY_LIMITED', default=3)
MODERATION_UI_ALERT_FAIL_RATE = env.float('MODERATION_UI_ALERT_FAIL_RATE', default=0.2)

# 用户信誉配置
REPUTATION_MIN_SCORE = 0
REPUTATION_MAX_SCORE = 100
REPUTATION_INITIAL_SCORE = 50
REPUTATION_TRUSTED_THRESHOLD = 80  # 高信誉阈值
REPUTATION_LOW_THRESHOLD = 30  # 低信誉阈值

# 信誉分变化规则
REPUTATION_APPROVE_BONUS = 1  # 内容通过 +1
REPUTATION_REJECT_PENALTY = 5  # 内容拒绝 -5
REPUTATION_REPORT_PENALTY = 10  # 被举报 -10
REPUTATION_WEEKLY_BONUS = 5  # 连续一周无违规 +5

# =============================================================================
# 安全配置（CSP、HSTS 等）
# =============================================================================

# Content Security Policy (CSP) 配置
# 注意：django-csp 需要安装：uv pip install django-csp
# 如果未安装，以下配置不会生效

# 使用自定义 CSP 中间件（轻量级实现）
CSP_ENABLED = env.bool('CSP_ENABLED', default=not DEBUG)

if CSP_ENABLED:
    # CSP 指令配置
    CSP_DEFAULT_SRC = env.list('CSP_DEFAULT_SRC', default=["'self'"])
    CSP_SCRIPT_SRC = env.list('CSP_SCRIPT_SRC', default=[
        "'self'",
        "'unsafe-inline'",  # 内联脚本（Bootstrap 需要）
        "'unsafe-eval'",    # eval（部分库需要）
        "cdn.jsdelivr.net",
        "code.jquery.com",
    ])
    CSP_STYLE_SRC = env.list('CSP_STYLE_SRC', default=[
        "'self'",
        "'unsafe-inline'",  # 内联样式（Bootstrap 需要）
        "cdn.jsdelivr.net",
        "fonts.googleapis.com",
    ])
    CSP_IMG_SRC = env.list('CSP_IMG_SRC', default=[
        "'self'",
        "data:",            # Base64 图片
        "blob:",            # Blob 图片
        "cdn.jsdelivr.net",
    ])
    CSP_FONT_SRC = env.list('CSP_FONT_SRC', default=[
        "'self'",
        "cdn.jsdelivr.net",
        "fonts.gstatic.com",
    ])
    CSP_CONNECT_SRC = env.list('CSP_CONNECT_SRC', default=[
        "'self'",
    ])
    CSP_FRAME_ANCESTORS = env.list('CSP_FRAME_ANCESTORS', default=["'self'"])
    CSP_BASE_URI = env.list('CSP_BASE_URI', default=["'self'"])
    CSP_FORM_ACTION = env.list('CSP_FORM_ACTION', default=["'self'"])
else:
    # 开发模式下宽松配置
    CSP_DEFAULT_SRC = ["*"]
    CSP_SCRIPT_SRC = ["*"]
    CSP_STYLE_SRC = ["*"]
    CSP_IMG_SRC = ["*"]
    CSP_FONT_SRC = ["*"]
    CSP_CONNECT_SRC = ["*"]

# HSTS 配置（生产环境强制 HTTPS）
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0 if DEBUG else 31536000)  # 1 年
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# 其他安全头
SECURE_CONTENT_TYPE_NOSNIFF = True  # 防止 MIME 类型嗅探
SECURE_BROWSER_XSS_FILTER = True    # XSS 过滤（已弃用但仍有效）
X_FRAME_OPTIONS = 'DENY'            # 禁止 iframe 嵌入

# Session 安全
SESSION_COOKIE_SECURE = not DEBUG   # 仅 HTTPS（生产环境）
SESSION_COOKIE_HTTPONLY = True      # 禁止 JS 访问
SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF 防护

# CSRF 安全
CSRF_COOKIE_SECURE = not DEBUG      # 仅 HTTPS（生产环境）
CSRF_COOKIE_HTTPONLY = True         # 禁止 JS 访问
CSRF_COOKIE_SAMESITE = 'Lax'

# 允许的嵌入域名（iframe）
X_FRAME_OPTIONS_ALLOW_FROM = env.list('X_FRAME_OPTIONS_ALLOW_FROM', default=[])

# =============================================================================
# 性能优化配置
# =============================================================================

# 数据库连接池（MySQL/PostgreSQL）
if 'mysql' in env('DB_ENGINE', default='sqlite'):
    DATABASES['default']['CONN_MAX_AGE'] = env.int('DB_CONN_MAX_AGE', default=600)
    DATABASES['default']['OPTIONS'] = {
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'charset': 'utf8mb4',
    }

# 查询优化：预加载相关对象
PREFETCH_RELATED_MAX_DEPTH = env.int('PREFETCH_RELATED_MAX_DEPTH', default=3)

# =============================================================================
# Sentry APM 监控配置
# =============================================================================

# Sentry DSN（从环境变量读取）
SENTRY_DSN = env('SENTRY_DSN', default='')

if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        import logging

        _logger = logging.getLogger(__name__)

        # 环境标识
        environment = 'production' if not DEBUG else 'development'

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=environment,
            release=f'djangoblog@{env("APP_VERSION", default="2.3.2")}',

            # 集成
            integrations=[
                DjangoIntegration(
                    transaction_style='url',  # 使用 URL 作为事务名
                    middleware_spans=True,    # 记录中间件
                    signals_spans=True,       # 记录信号
                    cache_spans=True,         # 记录缓存
                ),
                CeleryIntegration(
                    monitor_beat_tasks=True,  # 监控 Beat 任务
                ),
                RedisIntegration(),
            ],

            # 性能监控采样率
            traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1),
            profiles_sample_rate=env.float('SENTRY_PROFILES_SAMPLE_RATE', default=0.1),

            # 忽略特定异常
            ignore_errors=[
                'django.http.Http404',
                'django.core.exceptions.PermissionDenied',
            ],

            # 发送用户信息
            send_default_pii=False,  # 不发送个人敏感信息

            # 附加请求体
            request_bodies='small',  # 只发送小型请求体
        )

        _logger.info(f'Sentry 初始化成功 (环境: {environment})')

    except ImportError:
        pass  # sentry-sdk 未安装
    except Exception:
        pass  # Sentry 初始化失败
