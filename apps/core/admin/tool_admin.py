"""
工具配置 Admin
"""

from django.contrib import admin
from .admin_site import admin_site

from apps.tools.models import ToolConfig


@admin.register(ToolConfig, site=admin_site)
class ToolConfigAdmin(admin.ModelAdmin):
    """工具配置管理"""

    list_display = ["name", "slug", "is_enabled", "sort_order"]
    list_filter = ["is_enabled"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
