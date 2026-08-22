"""
项目统一常量定义

集中管理所有硬编码常量，避免分散在各处导致维护困难。
"""

from typing import Final

# ============================================================
# 缓存 TTL 常量 (秒)
# ============================================================
CACHE_TTL_SHORT: Final[int] = 300          # 5 分钟
CACHE_TTL_MEDIUM: Final[int] = 900         # 15 分钟
CACHE_TTL_LONG: Final[int] = 3600          # 1 小时
CACHE_TTL_DAY: Final[int] = 86400          # 1 天
CACHE_TTL_WEEK: Final[int] = 604800        # 1 周

# ============================================================
# 分页常量
# ============================================================
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100
API_DEFAULT_PAGE_SIZE: Final[int] = 20
API_MAX_PAGE_SIZE: Final[int] = 50

# ============================================================
# 速率限制常量
# ============================================================
RATE_LIMIT_ANONYMOUS: Final[str] = "100/hour"
RATE_LIMIT_AUTHENTICATED: Final[str] = "1000/hour"
RATE_LIMIT_LOGIN: Final[str] = "5/minute"
RATE_LIMIT_REGISTER: Final[str] = "3/minute"
RATE_LIMIT_COMMENT: Final[str] = "30/minute"
RATE_LIMIT_TOPIC: Final[str] = "10/minute"
RATE_LIMIT_REPLY: Final[str] = "30/minute"
RATE_LIMIT_TOOL_USE: Final[str] = "60/minute"
RATE_LIMIT_API_ANON: Final[str] = "100/hour"
RATE_LIMIT_API_AUTH: Final[str] = "1000/hour"

# ============================================================
# 文件上传常量
# ============================================================
MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE: Final[int] = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS: Final[set] = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
ALLOWED_DOCUMENT_EXTENSIONS: Final[set] = {".pdf", ".doc", ".docx", ".txt", ".md"}
ALLOWED_ARCHIVE_EXTENSIONS: Final[set] = {".zip", ".tar", ".gz", ".rar", ".7z"}

# 允许上传的文件扩展名（不带点，用于扩展名检查）
FILE_ALLOWED_EXTENSIONS: Final[set] = {
    "pdf", "doc", "docx", "txt", "md",
    "zip", "tar", "gz", "rar", "7z",
    "jpg", "jpeg", "png", "gif", "webp", "bmp",
}

# MIME 白名单
ALLOWED_IMAGE_MIMES: Final[set] = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"
}
ALLOWED_DOCUMENT_MIMES: Final[set] = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
}
ALLOWED_ARCHIVE_MIMES: Final[set] = {
    "application/zip",
    "application/x-tar",
    "application/gzip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
}

FILE_MIME_WHITELIST: Final[set] = (
    ALLOWED_IMAGE_MIMES | ALLOWED_DOCUMENT_MIMES | ALLOWED_ARCHIVE_MIMES
)

# 危险文件扩展名（严禁上传）
DANGEROUS_FILE_EXTENSIONS: Final[set] = {
    "exe", "dll", "bat", "cmd", "ps1", "sh", "com", "msi", "scr",
    "php", "phtml", "jsp", "asp", "aspx", "cgi", "pl", "py", "rb",
    "jar", "war", "ear", "class", "so", "dylib",
    "html", "htm", "shtml", "htaccess", "htpasswd",
}

# ============================================================
# 审核系统常量
# ============================================================
MODERATION_STATUS_CHOICES: Final[tuple] = (
    ("pending", "待审核"),
    ("approved", "已通过"),
    ("rejected", "已拒绝"),
)

REVIEW_ACTION_CHOICES: Final[tuple] = (
    ("approved", "通过"),
    ("rejected", "拒绝"),
    ("reminded", "提醒"),
)

# 信誉分数阈值
REPUTATION_TRUSTED_THRESHOLD: Final[int] = 80
REPUTATION_NORMAL_THRESHOLD: Final[int] = 30
REPUTATION_LOW_THRESHOLD: Final[int] = 0

REPUTATION_INITIAL_SCORE: Final[int] = 50
REPUTATION_MAX_SCORE: Final[int] = 100
REPUTATION_MIN_SCORE: Final[int] = 0

# 信誉分增减
REPUTATION_APPROVE_BONUS: Final[int] = 1
REPUTATION_REJECT_PENALTY: Final[int] = 5
REPUTATION_REPORT_PENALTY: Final[int] = 10
REPUTATION_WEEKLY_BONUS: Final[int] = 5
REPUTATION_DAILY_DECAY: Final[int] = 0  # 暂不启用每日衰减

# 连续无违规奖励
REPUTATION_CLEAN_DAYS_BONUS_INTERVAL: Final[int] = 7  # 每 7 天

# ============================================================
# 百度 AI 审核常量
# ============================================================
BAIDU_AI_TIMEOUT: Final[int] = 10  # 秒
BAIDU_AI_MAX_RETRIES: Final[int] = 3
BAIDU_AI_RETRY_DELAY: Final[float] = 1.0  # 秒

# ============================================================
# 敏感词检测常量
# ============================================================
SENSITIVE_WORD_CACHE_PREFIX: Final[str] = "sensitive_words"
SENSITIVE_WORD_VERSION_KEY: Final[str] = "sensitive_words_version"
SENSITIVE_WORD_MAX_LENGTH: Final[int] = 50

# ============================================================
# 浏览量统计常量
# ============================================================
VIEWS_SYNC_BATCH_SIZE: Final[int] = 100
VIEWS_SYNC_INTERVAL: Final[int] = 300  # 5 分钟
VIEWS_FLUSH_INTERVAL: Final[int] = 10  # 秒
VIEWS_BUFFER_MAX_PER_TYPE: Final[int] = 10000
VIEWS_BUFFER_CLEANUP_INTERVAL: Final[int] = 60  # 秒
VIEWS_ANTI_SPAM_TTL: Final[int] = 3600  # 1 小时防刷

# ============================================================
# 热门内容常量
# ============================================================
HOT_POSTS_WEEK_LIMIT: Final[int] = 10
HOT_POSTS_MONTH_LIMIT: Final[int] = 20
HOT_POSTS_WEEK_DAYS: Final[int] = 7
HOT_POSTS_MONTH_DAYS: Final[int] = 30

# ============================================================
# 评论/回复常量
# ============================================================
COMMENT_MAX_LENGTH: Final[int] = 5000
REPLY_MAX_LENGTH: Final[int] = 5000
TOPIC_MAX_LENGTH: Final[int] = 20000
POST_MAX_LENGTH: Final[int] = 100000

# ============================================================
# WebSocket 通知常量
# ============================================================
NOTIFICATION_TYPES: Final[tuple] = (
    ("comment", "评论"),
    ("reply", "回复"),
    ("like", "点赞"),
    ("mention", "提及"),
    ("system", "系统"),
    ("moderation", "审核"),
)

WEBSOCKET_HEARTBEAT_INTERVAL: Final[int] = 30  # 秒

# ============================================================
# Celery 任务常量
# ============================================================
TASK_DEFAULT_TIMEOUT: Final[int] = 300  # 5 分钟
TASK_LOCK_TIMEOUT: Final[int] = 300     # 5 分钟
TASK_MAX_RETRIES: Final[int] = 3
TASK_DEFAULT_RETRY_DELAY: Final[int] = 60  # 秒

# 定时任务锁名
TASK_LOCK_PREFIX: Final[str] = "task_lock:"

# ============================================================
# 搜索常量
# ============================================================
SEARCH_DEFAULT_LIMIT: Final[int] = 20
SEARCH_MAX_LIMIT: Final[int] = 100
SEARCH_HIGHLIGHT_TAG: Final[str] = "<mark>"
SEARCH_HIGHLIGHT_END_TAG: Final[str] = "</mark>"

# ============================================================
# 工具系统常量
# ============================================================
TOOL_RESULT_TTL: Final[int] = 3600  # 1 小时
TOOL_MAX_INPUT_SIZE: Final[int] = 1024 * 1024  # 1MB

# ============================================================
# 用户/认证常量
# ============================================================
USERNAME_MIN_LENGTH: Final[int] = 3
USERNAME_MAX_LENGTH: Final[int] = 30
PASSWORD_MIN_LENGTH: Final[int] = 8
EMAIL_MAX_LENGTH: Final[int] = 254

# 验证码
CAPTCHA_CODE_LENGTH: Final[int] = 6
CAPTCHA_EXPIRE_SECONDS: Final[int] = 300
CAPTCHA_MAX_ATTEMPTS: Final[int] = 3
CAPTCHA_LOCKOUT_SECONDS: Final[int] = 300

# ============================================================
# API 响应常量
# ============================================================
API_SUCCESS_CODE: Final[int] = 200
API_CREATED_CODE: Final[int] = 201
API_BAD_REQUEST_CODE: Final[int] = 400
API_UNAUTHORIZED_CODE: Final[int] = 401
API_FORBIDDEN_CODE: Final[int] = 403
API_NOT_FOUND_CODE: Final[int] = 404
API_SERVER_ERROR_CODE: Final[int] = 500

# ============================================================
# 健康检查常量
# ============================================================
HEALTH_CHECK_DISK_WARNING_THRESHOLD: Final[float] = 85.0  # %
HEALTH_CHECK_DISK_CRITICAL_THRESHOLD: Final[float] = 95.0  # %
HEALTH_CHECK_MEMORY_WARNING_THRESHOLD: Final[float] = 85.0  # %
HEALTH_CHECK_MEMORY_CRITICAL_THRESHOLD: Final[float] = 95.0  # %

# ============================================================
# 版本/环境常量
# ============================================================
DEFAULT_ENVIRONMENT: Final[str] = "development"
SUPPORTED_ENVIRONMENTS: Final[tuple] = ("development", "staging", "production", "test")

# ============================================================
# 安全头常量
# ============================================================
CSP_NONCE_LENGTH: Final[int] = 32
SECURE_HSTS_SECONDS: Final[int] = 31536000  # 1 年
SECURE_HSTS_INCLUDE_SUBDOMAINS: Final[bool] = True
SECURE_HSTS_PRELOAD: Final[bool] = True