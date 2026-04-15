"""统一错误码与默认文案。"""

from typing import Dict, Optional


class ErrorCodes:
    # Upload
    UPLOAD_NO_FILE = "UPLOAD_NO_FILE"
    UPLOAD_IMAGE_TOO_LARGE = "UPLOAD_IMAGE_TOO_LARGE"
    UPLOAD_FILE_TOO_LARGE = "UPLOAD_FILE_TOO_LARGE"
    UPLOAD_IMAGE_TYPE_NOT_ALLOWED = "UPLOAD_IMAGE_TYPE_NOT_ALLOWED"
    UPLOAD_IMAGE_MAGIC_INVALID = "UPLOAD_IMAGE_MAGIC_INVALID"
    UPLOAD_FILE_TYPE_DENIED = "UPLOAD_FILE_TYPE_DENIED"
    UPLOAD_FILE_EXT_NOT_ALLOWED = "UPLOAD_FILE_EXT_NOT_ALLOWED"
    UPLOAD_FILE_MAGIC_DENIED = "UPLOAD_FILE_MAGIC_DENIED"
    UPLOAD_SECURITY_SCAN_REJECTED = "UPLOAD_SECURITY_SCAN_REJECTED"
    UPLOAD_TASK_NOT_FOUND = "UPLOAD_TASK_NOT_FOUND"
    UPLOAD_SAVE_FAILED = "UPLOAD_SAVE_FAILED"

    # Cache
    CACHE_MEMORY_INFO_FAILED = "CACHE_MEMORY_INFO_FAILED"
    CACHE_ANALYZE_FAILED = "CACHE_ANALYZE_FAILED"
    CACHE_CLEANUP_FAILED = "CACHE_CLEANUP_FAILED"

    # Moderation
    MODERATION_SERVICE_UNAVAILABLE = "MODERATION_SERVICE_UNAVAILABLE"
    MODERATION_INVALID_CONTENT_TYPE = "MODERATION_INVALID_CONTENT_TYPE"
    MODERATION_CONTENT_NOT_FOUND = "MODERATION_CONTENT_NOT_FOUND"
    MODERATION_APPROVE_FAILED = "MODERATION_APPROVE_FAILED"
    MODERATION_REJECT_FAILED = "MODERATION_REJECT_FAILED"
    MODERATION_PERMISSION_DENIED = "MODERATION_PERMISSION_DENIED"
    MODERATION_API_RATE_LIMITED = "MODERATION_API_RATE_LIMITED"
    MODERATION_API_CONCURRENCY_LIMITED = "MODERATION_API_CONCURRENCY_LIMITED"


DEFAULT_MESSAGES: Dict[str, str] = {
    ErrorCodes.UPLOAD_NO_FILE: "没有上传文件",
    ErrorCodes.UPLOAD_IMAGE_TOO_LARGE: "文件大小不能超过5MB",
    ErrorCodes.UPLOAD_FILE_TOO_LARGE: "文件大小不能超过10MB",
    ErrorCodes.UPLOAD_IMAGE_TYPE_NOT_ALLOWED: "不支持的图片类型",
    ErrorCodes.UPLOAD_IMAGE_MAGIC_INVALID: "图片文件头校验失败",
    ErrorCodes.UPLOAD_FILE_TYPE_DENIED: "不允许上传该类型文件",
    ErrorCodes.UPLOAD_FILE_EXT_NOT_ALLOWED: "文件类型不在允许列表",
    ErrorCodes.UPLOAD_FILE_MAGIC_DENIED: "检测到危险文件头，上传被拒绝",
    ErrorCodes.UPLOAD_SECURITY_SCAN_REJECTED: "文件安全扫描未通过",
    ErrorCodes.UPLOAD_TASK_NOT_FOUND: "上传任务不存在或已过期",
    ErrorCodes.UPLOAD_SAVE_FAILED: "上传失败，请稍后重试",
    ErrorCodes.CACHE_MEMORY_INFO_FAILED: "缓存内存信息获取失败",
    ErrorCodes.CACHE_ANALYZE_FAILED: "缓存键分析失败",
    ErrorCodes.CACHE_CLEANUP_FAILED: "缓存清理失败",
    ErrorCodes.MODERATION_SERVICE_UNAVAILABLE: "审核服务暂时不可用，请稍后重试",
    ErrorCodes.MODERATION_INVALID_CONTENT_TYPE: "不支持的审核内容类型",
    ErrorCodes.MODERATION_CONTENT_NOT_FOUND: "审核对象不存在",
    ErrorCodes.MODERATION_APPROVE_FAILED: "审核通过操作失败，请稍后重试",
    ErrorCodes.MODERATION_REJECT_FAILED: "审核拒绝操作失败，请稍后重试",
    ErrorCodes.MODERATION_PERMISSION_DENIED: "无审核权限",
    ErrorCodes.MODERATION_API_RATE_LIMITED: "审核请求过于频繁，请稍后再试",
    ErrorCodes.MODERATION_API_CONCURRENCY_LIMITED: "审核服务繁忙，请稍后再试",
}


def error_message(code: str, fallback: str = "请求失败") -> str:
    return DEFAULT_MESSAGES.get(code, fallback)


def api_error_payload(code: str, message: Optional[str] = None, **extra) -> Dict:
    msg = message or error_message(code)
    payload = {
        "error_code": code,
        "error": msg,
        "message": msg,
    }
    payload.update(extra)
    return payload
