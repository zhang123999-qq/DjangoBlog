from django.contrib import admin
from .models import ToolConfig


@admin.register(ToolConfig)
class ToolConfigAdmin(admin.ModelAdmin):
    """工具配置管理"""
    list_display = ('name', 'slug', 'is_enabled', 'sort_order')
    list_filter = ('is_enabled',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
