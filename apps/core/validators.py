"""
文件上传验证器
提供统一的文件上传安全验证
"""

import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_file_extension(value, allowed_extensions=None):
    """
    验证文件扩展名

    Args:
        value: 上传的文件
        allowed_extensions: 允许的扩展名列表，如 ['.jpg', '.png', '.pdf']

    Raises:
        ValidationError: 如果文件扩展名不在允许列表中
    """
    if allowed_extensions is None:
        # 默认允许的图片扩展名
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"]

    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            _('不支持的文件扩展名 "%(ext)s"。允许的扩展名: %(allowed)s'),
            params={"ext": ext, "allowed": ", ".join(allowed_extensions)},
            code="invalid_extension",
        )


def validate_file_size(value, max_size_mb=10):
    """
    验证文件大小

    Args:
        value: 上传的文件
        max_size_mb: 最大文件大小（MB）

    Raises:
        ValidationError: 如果文件大小超过限制
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    if value.size > max_size_bytes:
        raise ValidationError(
            _("文件大小 %(size).1fMB 超过最大限制 %(max_size)dMB"),
            params={"size": value.size / (1024 * 1024), "max_size": max_size_mb},
            code="file_too_large",
        )


def validate_image_extension(value):
    """验证图片文件扩展名"""
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    validate_file_extension(value, allowed_extensions)


def validate_document_extension(value):
    """验证文档文件扩展名"""
    allowed_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"]
    validate_file_extension(value, allowed_extensions)


def validate_archive_extension(value):
    """验证压缩文件扩展名"""
    allowed_extensions = [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"]
    validate_file_extension(value, allowed_extensions)


def validate_any_file_extension(value):
    """验证任意文件扩展名（白名单模式）"""
    allowed_extensions = [
        # 图片
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".svg",
        # 文档
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        # 压缩文件
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        # 其他常见文件
        ".csv",
        ".json",
        ".xml",
        ".html",
        ".css",
        ".js",
    ]
    validate_file_extension(value, allowed_extensions)


# 组合验证器
def validate_image_upload(value):
    """验证图片上传（扩展名 + 大小）"""
    validate_image_extension(value)
    validate_file_size(value, max_size_mb=5)  # 图片最大5MB


def validate_document_upload(value):
    """验证文档上传（扩展名 + 大小）"""
    validate_document_extension(value)
    validate_file_size(value, max_size_mb=20)  # 文档最大20MB


def validate_any_upload(value):
    """验证任意文件上传（扩展名 + 大小）"""
    validate_any_file_extension(value)
    validate_file_size(value, max_size_mb=50)  # 任意文件最大50MB
