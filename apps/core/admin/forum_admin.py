"""
论坛管理 Admin
"""

from django.contrib import admin
from .admin_site import admin_site

from apps.forum.models import Board, Topic, Reply


@admin.register(Board, site=admin_site)
class BoardAdmin(admin.ModelAdmin):
    """版块管理"""

    list_display = ["name", "slug", "topic_count", "reply_count", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}

    def topic_count(self, obj):
        return obj.topics.count()

    topic_count.short_description = "主题数"

    def reply_count(self, obj):
        return Reply.objects.filter(topic__board=obj).count()

    reply_count.short_description = "回复数"


@admin.register(Topic, site=admin_site)
class TopicAdmin(admin.ModelAdmin):
    """主题管理"""

    list_display = [
        "title", "board", "author", "views_count", "reply_count",
        "is_pinned", "is_locked", "review_status", "created_at",
    ]
    list_filter = ["board", "is_pinned", "is_locked", "review_status"]
    search_fields = ["title", "content", "author__username"]
    date_hierarchy = "created_at"
    actions = ["approve_topics", "reject_topics", "pin_topics", "lock_topics"]
    list_select_related = ["board", "author"]
    raw_id_fields = ["author"]

    def approve_topics(self, request, queryset):
        from moderation.services import approve_instance
        for topic in queryset:
            approve_instance(topic, request.user, note="")
        self.message_user(request, f"成功审核通过 {queryset.count()} 个主题")

    approve_topics.short_description = "审核通过所选主题"

    def reject_topics(self, request, queryset):
        from moderation.services import reject_instance
        for topic in queryset:
            reject_instance(topic, request.user, note="")
        self.message_user(request, f"成功拒绝 {queryset.count()} 个主题")

    reject_topics.short_description = "拒绝所选主题"

    def pin_topics(self, request, queryset):
        count = queryset.update(is_pinned=True)
        self.message_user(request, f"成功置顶 {count} 个主题")

    pin_topics.short_description = "置顶所选主题"

    def lock_topics(self, request, queryset):
        count = queryset.update(is_locked=True)
        self.message_user(request, f"成功锁定 {count} 个主题")

    lock_topics.short_description = "锁定所选主题"


@admin.register(Reply, site=admin_site)
class ReplyAdmin(admin.ModelAdmin):
    """回复管理"""

    list_display = ["topic", "author", "content_short", "review_status", "like_count", "created_at"]
    list_filter = ["review_status", "created_at"]
    search_fields = ["content", "author__username", "topic__title"]
    actions = ["approve_replies", "reject_replies"]
    list_select_related = ["topic", "author"]
    raw_id_fields = ["topic", "author"]

    def content_short(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_short.short_description = "内容"

    def approve_replies(self, request, queryset):
        from moderation.services import approve_instance
        for reply in queryset:
            approve_instance(reply, request.user, note="")
        self.message_user(request, f"成功审核通过 {queryset.count()} 条回复")

    approve_replies.short_description = "审核通过所选回复"

    def reject_replies(self, request, queryset):
        from moderation.services import reject_instance
        for reply in queryset:
            reject_instance(reply, request.user, note="")
        self.message_user(request, f"成功拒绝 {queryset.count()} 条回复")

    reject_replies.short_description = "拒绝所选回复"
