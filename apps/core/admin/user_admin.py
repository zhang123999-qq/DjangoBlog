"""
用户管理 Admin
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .admin_site import admin_site

from apps.accounts.models import User, Profile


class ProfileInline(admin.StackedInline):
    """在 User 管理页面中内联显示 Profile"""

    model = Profile
    can_delete = False
    verbose_name_plural = "个人资料"
    extra = 0


@admin.register(User, site=admin_site)
class CustomUserAdmin(UserAdmin):
    """自定义 User 管理"""

    inlines = [ProfileInline]
    list_display = ["username", "email", "nickname", "is_staff", "is_active", "date_joined"]
    list_filter = ["is_staff", "is_active", "date_joined"]
    search_fields = ["username", "email", "nickname"]
    ordering = ["-date_joined"]
    actions = ["activate_users", "deactivate_users"]

    fieldsets = (
        ("基本信息", {"fields": ("username", "email", "nickname", "password")}),
        (
            "权限设置",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
                "classes": ("collapse",),
            },
        ),
        ("重要日期", {"fields": ("last_login", "date_joined"), "classes": ("collapse",)}),
    )

    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"成功激活 {count} 个用户")

    activate_users.short_description = "激活所选用户"

    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"成功禁用 {count} 个用户")

    deactivate_users.short_description = "禁用所选用户"


@admin.register(Profile, site=admin_site)
class ProfileAdmin(admin.ModelAdmin):
    """个人资料管理"""

    list_display = ["user", "bio", "website", "created_at"]
    search_fields = ["user__username", "user__email"]
    list_filter = ["created_at"]
    list_select_related = ["user"]
    raw_id_fields = ["user"]
