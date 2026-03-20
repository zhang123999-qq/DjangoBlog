from django.contrib import admin
from .models import Category, Tag, Post, Comment
from moderation.services import approve_instance, reject_instance


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """分类管理"""
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """标签管理"""
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """文章管理"""
    list_display = ('title', 'author', 'category', 'status', 'allow_comments', 'views_count', 'published_at', 'created_at')
    list_filter = ('status', 'category', 'tags', 'author')
    search_fields = ('title', 'content', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    ordering = ('-published_at', '-created_at')
    filter_horizontal = ('tags',)
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'slug', 'summary', 'content')
        }),
        ('分类与标签', {
            'fields': ('category', 'tags')
        }),
        ('状态与作者', {
            'fields': ('status', 'author', 'published_at')
        }),
        ('评论设置', {
            'fields': ('allow_comments',)
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """评论管理"""
    list_display = ('post', 'user', 'name', 'is_approved', 'review_status', 'reviewed_by', 'reviewed_at', 'created_at')
    list_filter = ('is_approved', 'review_status', 'post', 'user', 'reviewed_by')
    search_fields = ('content', 'name', 'email', 'user__username', 'reviewed_by__username')
    readonly_fields = ('reviewed_by', 'reviewed_at', 'created_at', 'updated_at', 'ip_address', 'user_agent')
    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        """批量通过评论"""
        for comment in queryset:
            approve_instance(comment, request.user, note="")

    def reject_selected(self, request, queryset):
        """批量拒绝评论"""
        for comment in queryset:
            reject_instance(comment, request.user, note="")

    approve_selected.short_description = '通过选中的评论'
    reject_selected.short_description = '拒绝选中的评论'
