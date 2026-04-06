"""
通知管理后台
"""

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """通知管理"""

    list_display = ['id', 'user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['created_at', 'read_at']
    raw_id_fields = ['user']

    date_hierarchy = 'created_at'
    ordering = ['-created_at']
