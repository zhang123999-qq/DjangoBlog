"""
评论管理 Admin
"""

from django.contrib import admin
from .admin_site import admin_site

from apps.blog.models import Comment


@admin.register(Comment, site=admin_site)
class CommentAdmin(admin.ModelAdmin):
    """评论管理"""

    list_display = ["post", "user", "content_short", "review_status", "like_count", "created_at"]
    list_filter = ["review_status", "created_at"]
    search_fields = ["content", "user__username", "post__title"]
    actions = ["approve_comments", "reject_comments"]
    list_editable = ["review_status"]
    list_select_related = ["post", "user"]
    raw_id_fields = ["post", "user"]

    def content_short(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_short.short_description = "内容"

    def approve_comments(self, request, queryset):
        from moderation.services import approve_instance

        for comment in queryset:
            approve_instance(comment, request.user, note="")
        self.message_user(request, f"成功审核通过 {queryset.count()} 条评论")

    approve_comments.short_description = "审核通过所选评论"

    def reject_comments(self, request, queryset):
        from moderation.services import reject_instance

        for comment in queryset:
            reject_instance(comment, request.user, note="")
        self.message_user(request, f"成功拒绝 {queryset.count()} 条评论")

    reject_comments.short_description = "拒绝所选评论"
