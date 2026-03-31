"""
网站配置 Admin
"""

from django.contrib import admin
from .admin_site import admin_site

from apps.core.models import SiteConfig


@admin.register(SiteConfig, site=admin_site)
class SiteConfigAdmin(admin.ModelAdmin):
    """网站配置管理"""

    list_display = ["site_name", "is_installed", "allow_registration", "created_at"]
    fieldsets = (
        ("网站信息", {"fields": ("site_name", "site_title", "site_description", "logo")}),
        ("系统设置", {"fields": ("is_installed", "allow_registration")}),
    )

    def has_add_permission(self, request):
        # 只允许一条配置
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)
