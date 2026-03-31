"""
博客分类和标签 Admin
"""

from django.contrib import admin
from .admin_site import admin_site

from apps.blog.models import Category, Tag


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    """分类管理"""

    list_display = ["name", "slug", "created_at"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag, site=admin_site)
class TagAdmin(admin.ModelAdmin):
    """标签管理"""

    list_display = ["name", "slug", "created_at"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
