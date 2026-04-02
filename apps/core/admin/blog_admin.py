"""
博客文章管理 Admin
"""

from django.contrib import admin
from .admin_site import admin_site

from apps.blog.models import Post


@admin.register(Post, site=admin_site)
class PostAdmin(admin.ModelAdmin):
    """文章管理"""

    list_display = ["title", "author", "category", "status", "views_count", "allow_comments", "published_at"]
    list_filter = ["status", "category", "allow_comments", "published_at", "author"]
    search_fields = ["title", "content", "author__username"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["tags"]
    date_hierarchy = "published_at"
    actions = ["publish_posts", "unpublish_posts"]
    list_select_related = ["author", "category"]
    raw_id_fields = ["author"]

    # 为 content 字段添加更多行
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "content" in form.base_fields:
            form.base_fields["content"].widget.attrs.update({
                "rows": 20,
                "style": "width: 100%; font-family: monospace;",
                "data-editor": "tinymce",
            })
        if "summary" in form.base_fields:
            form.base_fields["summary"].widget.attrs.update({
                "rows": 3,
                "style": "width: 100%;",
            })
        return form

    # 添加 TinyMCE 编辑器媒体文件
    class Media:
        js = (
            "https://cdn.jsdelivr.net/npm/tinymce@7/tinymce.min.js",
            "js/admin-editor.js",
        )
        css = {
            "all": ("css/admin-editor.css",),
        }

    fieldsets = (
        ("文章内容", {"fields": ("title", "slug", "summary", "content", "author")}),
        ("分类标签", {"fields": ("category", "tags")}),
        ("发布设置", {"fields": ("status", "allow_comments", "published_at")}),
    )

    def publish_posts(self, request, queryset):
        count = queryset.update(status="published")
        self.message_user(request, f"成功发布 {count} 篇文章")

    publish_posts.short_description = "发布所选文章"

    def unpublish_posts(self, request, queryset):
        count = queryset.update(status="draft")
        self.message_user(request, f"成功取消发布 {count} 篇文章")

    unpublish_posts.short_description = "取消发布所选文章"
