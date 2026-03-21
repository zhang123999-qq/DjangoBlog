from django.contrib import admin
from .models import SensitiveWord, ModerationLog, ModerationAdmin, ModerationReminder, UserReputation, ReputationLog


@admin.register(SensitiveWord)
class SensitiveWordAdmin(admin.ModelAdmin):
    """敏感词管理"""
    list_display = ('word', 'category', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('word',)
    ordering = ('word',)
    list_editable = ('is_active', 'category')


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
    actions = ['mark_as_processed']
    
    def mark_as_processed(self, request, queryset):
        """标记为已处理"""
        from django.utils import timezone
        count = queryset.filter(is_processed=False).update(is_processed=True, processed_at=timezone.now())
        self.message_user(request, f'已标记 {count} 条提醒为已处理')
    mark_as_processed.short_description = '标记为已处理'


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    """审核日志管理"""
    list_display = ('target_type', 'target_id', 'action', 'operator', 'created_at')
    list_filter = ('target_type', 'action', 'operator')
    search_fields = ('target_id', 'note')
    ordering = ('-created_at',)
    readonly_fields = ('target_type', 'target_id', 'action', 'operator', 'note', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(UserReputation)
class UserReputationAdmin(admin.ModelAdmin):
    """用户信誉管理"""
    list_display = ('user', 'score', 'level_display', 'total_posts', 'approved_count', 'rejected_count', 'clean_days')
    list_filter = ('score',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-score',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('用户信息', {
            'fields': ('user', 'score')
        }),
        ('统计数据', {
            'fields': ('total_posts', 'approved_count', 'rejected_count', 'report_count', 'clean_days', 'last_clean_check')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['add_bonus', 'add_penalty', 'reset_score']
    
    def level_display(self, obj):
        return obj.get_level_display()
    level_display.short_description = '信誉等级'
    
    def add_bonus(self, request, queryset):
        """奖励 5 分"""
        for rep in queryset:
            rep.update_score(5, '管理员奖励')
        self.message_user(request, f'已为 {queryset.count()} 个用户奖励 5 分')
    add_bonus.short_description = '奖励 5 分'
    
    def add_penalty(self, request, queryset):
        """惩罚 5 分"""
        for rep in queryset:
            rep.update_score(-5, '管理员惩罚')
        self.message_user(request, f'已对 {queryset.count()} 个用户扣除 5 分')
    add_penalty.short_description = '惩罚 5 分'
    
    def reset_score(self, request, queryset):
        """重置为 50 分"""
        for rep in queryset:
            rep.update_score(50 - rep.score, '管理员重置')
        self.message_user(request, f'已重置 {queryset.count()} 个用户的信誉分')
    reset_score.short_description = '重置为 50 分'


@admin.register(ReputationLog)
class ReputationLogAdmin(admin.ModelAdmin):
    """信誉日志管理"""
    list_display = ('user_reputation', 'action', 'old_score', 'new_score', 'delta', 'reason', 'created_at')
    list_filter = ('action',)
    search_fields = ('user_reputation__user__username', 'reason')
    ordering = ('-created_at',)
    readonly_fields = ('user_reputation', 'action', 'old_score', 'new_score', 'delta', 'reason', 'created_at')
    date_hierarchy = 'created_at'
