"""
审核系统 Admin
"""

from django.contrib import admin
from .admin_site import admin_site

from moderation.models import (
    SensitiveWord,
    ModerationLog,
    ModerationAdmin,
    ModerationReminder,
    UserReputation,
    ReputationLog,
)


@admin.register(SensitiveWord, site=admin_site)
class SensitiveWordAdmin(admin.ModelAdmin):
    """敏感词管理"""

    list_display = ["word", "category", "is_active", "created_at"]
    list_filter = ["is_active", "category"]
    search_fields = ["word"]
    list_editable = ["is_active", "category"]
    actions = ["activate_words", "deactivate_words"]

    def activate_words(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"成功启用 {count} 个敏感词")

    activate_words.short_description = "启用所选敏感词"

    def deactivate_words(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"成功禁用 {count} 个敏感词")

    deactivate_words.short_description = "禁用所选敏感词"


@admin.register(ModerationAdmin, site=admin_site)
class ModerationAdminAdmin(admin.ModelAdmin):
    """审核管理员分配管理"""

    list_display = ["target_type", "admin", "created_at"]
    list_filter = ["target_type", "admin"]
    list_select_related = ["admin"]


@admin.register(ModerationReminder, site=admin_site)
class ModerationReminderAdmin(admin.ModelAdmin):
    """审核提醒管理"""

    list_display = ["target_type", "target_id", "assigned_admin", "is_processed", "created_at"]
    list_filter = ["target_type", "assigned_admin", "is_processed"]
    search_fields = ["target_id"]
    readonly_fields = ["target_type", "target_id", "assigned_admin", "created_at"]
    list_select_related = ["assigned_admin"]
    actions = ["mark_as_processed"]

    def mark_as_processed(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(is_processed=False).update(is_processed=True, processed_at=timezone.now())
        self.message_user(request, f"已标记 {count} 条提醒为已处理")

    mark_as_processed.short_description = "标记为已处理"


@admin.register(ModerationLog, site=admin_site)
class ModerationLogAdmin(admin.ModelAdmin):
    """审核日志管理"""

    list_display = ["target_type", "target_id", "action", "operator", "created_at"]
    list_filter = ["target_type", "action", "operator"]
    search_fields = ["target_id", "note"]
    readonly_fields = ["target_type", "target_id", "action", "operator", "note", "created_at"]
    list_select_related = ["operator"]
    date_hierarchy = "created_at"


@admin.register(UserReputation, site=admin_site)
class UserReputationAdmin(admin.ModelAdmin):
    """用户信誉管理"""

    list_display = ["user", "score", "level_display", "total_posts", "approved_count", "rejected_count", "clean_days"]
    list_filter = ["score"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["add_bonus", "add_penalty", "reset_score"]
    list_select_related = ["user"]
    raw_id_fields = ["user"]

    def level_display(self, obj):
        return obj.get_level_display()

    level_display.short_description = "信誉等级"

    def add_bonus(self, request, queryset):
        for rep in queryset:
            rep.update_score(5, "管理员奖励")
        self.message_user(request, f"已为 {queryset.count()} 个用户奖励 5 分")

    add_bonus.short_description = "奖励 5 分"

    def add_penalty(self, request, queryset):
        for rep in queryset:
            rep.update_score(-5, "管理员惩罚")
        self.message_user(request, f"已对 {queryset.count()} 个用户扣 5 分")

    add_penalty.short_description = "惩罚 5 分"

    def reset_score(self, request, queryset):
        for rep in queryset:
            rep.update_score(50 - rep.score, "管理员重置")
        self.message_user(request, f"已重置 {queryset.count()} 个用户的信誉分")

    reset_score.short_description = "重置为 50 分"


@admin.register(ReputationLog, site=admin_site)
class ReputationLogAdmin(admin.ModelAdmin):
    """信誉日志管理"""

    list_display = ["user_reputation", "action", "old_score", "new_score", "delta", "reason", "created_at"]
    list_filter = ["action"]
    search_fields = ["user_reputation__user__username", "reason"]
    readonly_fields = ["user_reputation", "action", "old_score", "new_score", "delta", "reason", "created_at"]
    list_select_related = ["user_reputation"]
    date_hierarchy = "created_at"
