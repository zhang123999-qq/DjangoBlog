"""
通知模型

存储用户通知记录
"""

from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    通知模型

    存储用户收到的通知
    """

    TYPE_CHOICES = [
        ("comment", "评论"),
        ("reply", "回复"),
        ("like", "点赞"),
        ("system", "系统通知"),
        ("moderation", "审核通知"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", verbose_name="接收用户"
    )
    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="system", verbose_name="通知类型")
    link = models.URLField(blank=True, verbose_name="跳转链接")
    is_read = models.BooleanField(default=False, verbose_name="是否已读")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="阅读时间")
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="额外数据")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = "通知"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        """标记为已读"""
        if not self.is_read:
            from django.utils import timezone

            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    @classmethod
    def get_unread_count(cls, user) -> int:
        """获取用户未读通知数量"""
        return cls.objects.filter(user=user, is_read=False).count()

    @classmethod
    def get_recent(cls, user, limit: int = 10):
        """获取用户最近的通知"""
        return cls.objects.filter(user=user).order_by("-created_at")[:limit]
