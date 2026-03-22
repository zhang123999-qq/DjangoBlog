"""Base settings for project."""

import os
import socket
from pathlib import Path
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
    default_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
    
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
    ENABLE_INSTALLER=(bool, True),
)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

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
    'apps.install',
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
    'apps.core.security_middleware.SecurityMiddleware',
    'apps.install.middleware.InstallMiddleware',
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
        'ENGINE': 'django.db.backends.sqlite3',
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
AXES_IP_WHITELIST = []
AXES_IP_BLACKLIST = []

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
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
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
CACHES = {}

# Email settings
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Installer settings
ENABLE_INSTALLER = env('ENABLE_INSTALLER')

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
import sys
if sys.platform == 'win32':
    os.environ['NO_COLOR'] = '1'

# REST Framework 配置
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
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
