from django.contrib import admin
from .models import SensitiveWord, ModerationLog, ModerationAdmin, ModerationReminder


@admin.register(SensitiveWord)
class SensitiveWordAdmin(admin.ModelAdmin):
    """敏感词管理"""
    list_display = ('word', 'created_at')
    search_fields = ('word',)
    ordering = ('word',)


@admin.register(ModerationAdmin)
class ModerationAdminAdmin(admin.ModelAdmin):
    """审核管理员分配管理"""
    list_display = ('target_type', 'admin', 'created_at')
    list_filter = ('target_type', 'admin')
    ordering = ('target_type',)


@admin.register(ModerationReminder)
class ModerationReminderAdmin(admin.ModelAdmin):
    """审核提醒管理"""
    list_display = ('target_type', 'target_id', 'assigned_admin', 'is_processed', 'created_at')
    list_filter = ('target_type', 'assigned_admin', 'is_processed')
    search_fields = ('target_id',)
    ordering = ('-created_at',)
    readonly_fields = ('target_type', 'target_id', 'assigned_admin', 'created_at')


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    """审核日志管理"""
    list_display = ('target_type', 'target_id', 'action', 'operator', 'created_at')
    list_filter = ('target_type', 'action', 'operator')
    search_fields = ('target_id', 'note')
    ordering = ('-created_at',)
    readonly_fields = ('target_type', 'target_id', 'action', 'operator', 'note', 'created_at')
    date_hierarchy = 'created_at'
