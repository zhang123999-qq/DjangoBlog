from django.contrib import admin
from .models import Board, Topic, Reply
from moderation.services import approve_instance, reject_instance


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """版块管理"""
    list_display = ('name', 'topic_count', 'reply_count', 'last_post_at', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    """主题管理"""
    list_display = ('title', 'board', 'author', 'views_count', 'reply_count', 'is_pinned', 'is_locked', 'review_status', 'reviewed_by', 'reviewed_at', 'last_reply_at', 'created_at')
    list_filter = ('board', 'author', 'is_pinned', 'is_locked', 'review_status', 'reviewed_by')
    search_fields = ('title', 'content', 'reviewed_by__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('reviewed_by', 'reviewed_at', 'created_at', 'updated_at')
    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        """批量通过主题"""
        for topic in queryset:
            approve_instance(topic, request.user, note="")

    def reject_selected(self, request, queryset):
        """批量拒绝主题"""
        for topic in queryset:
            reject_instance(topic, request.user, note="")

    approve_selected.short_description = '通过选中的主题'
    reject_selected.short_description = '拒绝选中的主题'


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    """回复管理"""
    list_display = ('topic', 'author', 'like_count', 'is_deleted', 'review_status', 'reviewed_by', 'reviewed_at', 'created_at')
    list_filter = ('topic', 'author', 'is_deleted', 'review_status', 'reviewed_by')
    search_fields = ('content', 'reviewed_by__username')
    readonly_fields = ('reviewed_by', 'reviewed_at', 'created_at', 'updated_at')
    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        """批量通过回复"""
        for reply in queryset:
            approve_instance(reply, request.user, note="")

    def reject_selected(self, request, queryset):
        """批量拒绝回复"""
        for reply in queryset:
            reject_instance(reply, request.user, note="")

    approve_selected.short_description = '通过选中的回复'
    reject_selected.short_description = '拒绝选中的回复'
