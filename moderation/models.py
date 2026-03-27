from django.db import models
from django.conf import settings


class SensitiveWord(models.Model):
    """敏感词模型"""
    word = models.CharField(max_length=100, unique=True, verbose_name='敏感词')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    category = models.CharField(max_length=50, blank=True, verbose_name='分类')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '敏感词'
        verbose_name_plural = '敏感词'
        ordering = ['word']

    def __str__(self):
        return self.word

    def save(self, *args, **kwargs):
        from .utils import clear_sensitive_words_cache
        super().save(*args, **kwargs)
        # 清除缓存
        clear_sensitive_words_cache()


class ModerationAdmin(models.Model):
    """审核管理员分配模型"""
    TARGET_TYPE_CHOICES = (
        ('comment', '评论'),
        ('topic', '主题'),
        ('reply', '回复'),
    )

    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES, unique=True, verbose_name='内容类型')
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderation_roles', verbose_name='审核管理员')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '审核管理员分配'
        verbose_name_plural = '审核管理员分配'
        ordering = ['target_type']

    def __str__(self):
        return f'{self.get_target_type_display()} 审核管理员: {self.admin.username if self.admin else "未设置"}'


class ModerationReminder(models.Model):
    """审核提醒模型"""
    TARGET_TYPE_CHOICES = (
        ('comment', '评论'),
        ('topic', '主题'),
        ('reply', '回复'),
    )

    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES, verbose_name='内容类型')
    target_id = models.PositiveIntegerField(verbose_name='内容ID')
    assigned_admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='moderation_reminders', verbose_name='指派管理员')
    is_processed = models.BooleanField(default=False, verbose_name='是否已处理')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')

    class Meta:
        verbose_name = '审核提醒'
        verbose_name_plural = '审核提醒'
        ordering = ['-created_at']
        unique_together = ['target_type', 'target_id']  # 确保每个内容只生成一条提醒

    def __str__(self):
        return f'{self.get_target_type_display()} {self.target_id} 提醒给 {self.assigned_admin.username if self.assigned_admin else "超级管理员"}'


class ModerationLog(models.Model):
    """审核日志模型"""
    TARGET_TYPE_CHOICES = (
        ('comment', '评论'),
        ('topic', '主题'),
        ('reply', '回复'),
    )

    ACTION_CHOICES = (
        ('approved', '通过'),
        ('rejected', '拒绝'),
        ('reminded', '提醒'),
    )

    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.PositiveIntegerField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='moderation_logs')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '审核日志'
        verbose_name_plural = '审核日志'
        ordering = ['-created_at']

    def __str__(self):
        operator_name = self.operator.username if self.operator else '系统'
        return f'{self.get_target_type_display()} {self.target_id} - {self.get_action_display()} by {operator_name}'


# 导入信誉模型
from .reputation import UserReputation, ReputationLog

__all__ = [
    'SensitiveWord',
    'ModerationAdmin',
    'ModerationReminder',
    'ModerationLog',
    'UserReputation',
    'ReputationLog',
]
