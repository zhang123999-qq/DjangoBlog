"""
自定义管理后台配置 - 统一使用自定义 admin_site
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db.models import Sum
from datetime import datetime, timedelta
import sys
import platform


# ========== 自定义 AdminSite ==========
class DjangoBlogAdminSite(admin.AdminSite):
    site_header = "DjangoBlog 管理后台"
    site_title = "DjangoBlog Admin"
    index_title = "仪表盘"

    def index(self, request, extra_context=None):
        """自定义首页，添加统计数据"""
        from django.utils import timezone
        from django.conf import settings
        from apps.accounts.models import User
        from apps.blog.models import Post, Comment, Category, Tag
        from apps.forum.models import Topic, Reply, Board
        from apps.tools.registry import tool_registry

        extra_context = extra_context or {}

        # 工具统计
        tools = tool_registry.get_all_tools()
        tool_count = len(tools)

        # 系统信息
        db_backend = settings.DATABASES["default"]["ENGINE"].split(".")[-1]
        db_engine_display = {"sqlite3": "SQLite", "mysql": "MySQL", "postgresql": "PostgreSQL"}.get(
            db_backend, db_backend.upper()
        )

        # Redis 信息
        redis_info = "未启用"
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, socket_connect_timeout=2)
            info = r.info()
            redis_info = f"Redis {info.get('redis_version', 'Unknown')}"
        except Exception:
            pass

        extra_context.update(
            {
                # 系统信息
                "django_version": __import__("django").VERSION,
                "django_version_str": ".".join(map(str, __import__("django").VERSION[:2])),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "python_version_full": platform.python_version(),
                "db_engine": db_engine_display,
                "redis_info": redis_info,
                "server_time": timezone.now(),
                "os_info": f"{platform.system()} {platform.release()}",
                # 业务统计
                "user_count": User.objects.count(),
                "post_count": Post.objects.filter(status="published").count(),
                "topic_count": Topic.objects.count(),
                "comment_count": Comment.objects.count() + Reply.objects.count(),
                "tool_count": tool_count,
                "category_count": Category.objects.count(),
                "tag_count": Tag.objects.count(),
                "board_count": Board.objects.count(),
                "tools_list": tools[:10],
            }
        )

        # 今日统计
        today = datetime.now().date()
        extra_context["today_users"] = User.objects.filter(date_joined__date=today).count()
        extra_context["today_posts"] = Post.objects.filter(created_at__date=today).count()
        extra_context["today_comments"] = Comment.objects.filter(created_at__date=today).count()

        # 待审核
        extra_context["pending_comments"] = Comment.objects.filter(review_status="pending").count()
        extra_context["pending_replies"] = Reply.objects.filter(review_status="pending").count()
        extra_context["pending_topics"] = Topic.objects.filter(review_status="pending").count()

        # 总浏览量
        total_views = Post.objects.aggregate(total=Sum("views_count"))["total"] or 0
        extra_context["total_views"] = total_views

        # 最近7天数据
        week_data = []
        for i in range(7):
            day = (datetime.now() - timedelta(days=6 - i)).date()
            day_posts = Post.objects.filter(created_at__date=day).count()
            day_comments = Comment.objects.filter(created_at__date=day).count()
            week_data.append({"date": day.strftime("%m-%d"), "posts": day_posts, "comments": day_comments})
        extra_context["week_data"] = week_data

        return super().index(request, extra_context)


# 创建全局 admin_site 实例
admin_site = DjangoBlogAdminSite(name="admin")


# ========== 用户管理 ==========
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


# ========== 博客管理 ==========
from apps.blog.models import Category, Tag, Post, Comment


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

    # 为 content 字段添加更多行
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # 设置 content 字段的 widget 属性
        if "content" in form.base_fields:
            form.base_fields["content"].widget.attrs.update(
                {
                    "rows": 20,
                    "style": "width: 100%; font-family: monospace;",
                    "data-editor": "tinymce",
                }
            )
        # 设置 summary 字段
        if "summary" in form.base_fields:
            form.base_fields["summary"].widget.attrs.update(
                {
                    "rows": 3,
                    "style": "width: 100%;",
                }
            )
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


@admin.register(Comment, site=admin_site)
class CommentAdmin(admin.ModelAdmin):
    """评论管理"""

    list_display = ["post", "user", "content_short", "review_status", "like_count", "created_at"]
    list_filter = ["review_status", "created_at"]
    search_fields = ["content", "user__username", "post__title"]
    actions = ["approve_comments", "reject_comments"]
    list_editable = ["review_status"]

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


# ========== 论坛管理 ==========
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
        from apps.forum.models import Reply

        return Reply.objects.filter(topic__board=obj).count()

    reply_count.short_description = "回复数"


@admin.register(Topic, site=admin_site)
class TopicAdmin(admin.ModelAdmin):
    """主题管理"""

    list_display = [
        "title",
        "board",
        "author",
        "views_count",
        "reply_count",
        "is_pinned",
        "is_locked",
        "review_status",
        "created_at",
    ]
    list_filter = ["board", "is_pinned", "is_locked", "review_status"]
    search_fields = ["title", "content", "author__username"]
    date_hierarchy = "created_at"
    actions = ["approve_topics", "reject_topics", "pin_topics", "lock_topics"]

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


# ========== 内容审核 ==========
from moderation.models import (
    SensitiveWord,
    ModerationLog,
    ModerationAdmin,
    ModerationReminder,
    UserReputation,
    ReputationLog,
)


@admin.register(SensitiveWord, site=admin_site)
class SensitiveWordAdmin(admin.ModelAdmin):
    """敏感词管理"""

    list_display = ["word", "category", "is_active", "created_at"]
    list_filter = ["is_active", "category"]
    search_fields = ["word"]
    list_editable = ["is_active", "category"]
    actions = ["activate_words", "deactivate_words"]

    def activate_words(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"成功启用 {count} 个敏感词")

    activate_words.short_description = "启用所选敏感词"

    def deactivate_words(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"成功禁用 {count} 个敏感词")

    deactivate_words.short_description = "禁用所选敏感词"


@admin.register(ModerationAdmin, site=admin_site)
class ModerationAdminAdmin(admin.ModelAdmin):
    """审核管理员分配管理"""

    list_display = ["target_type", "admin", "created_at"]
    list_filter = ["target_type", "admin"]


@admin.register(ModerationReminder, site=admin_site)
class ModerationReminderAdmin(admin.ModelAdmin):
    """审核提醒管理"""

    list_display = ["target_type", "target_id", "assigned_admin", "is_processed", "created_at"]
    list_filter = ["target_type", "assigned_admin", "is_processed"]
    search_fields = ["target_id"]
    readonly_fields = ["target_type", "target_id", "assigned_admin", "created_at"]
    actions = ["mark_as_processed"]

    def mark_as_processed(self, request, queryset):
        from django.utils import timezone

        count = queryset.filter(is_processed=False).update(is_processed=True, processed_at=timezone.now())
        self.message_user(request, f"已标记 {count} 条提醒为已处理")

    mark_as_processed.short_description = "标记为已处理"


@admin.register(ModerationLog, site=admin_site)
class ModerationLogAdmin(admin.ModelAdmin):
    """审核日志管理"""

    list_display = ["target_type", "target_id", "action", "operator", "created_at"]
    list_filter = ["target_type", "action", "operator"]
    search_fields = ["target_id", "note"]
    readonly_fields = ["target_type", "target_id", "action", "operator", "note", "created_at"]
    date_hierarchy = "created_at"


@admin.register(UserReputation, site=admin_site)
class UserReputationAdmin(admin.ModelAdmin):
    """用户信誉管理"""

    list_display = ["user", "score", "level_display", "total_posts", "approved_count", "rejected_count", "clean_days"]
    list_filter = ["score"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["add_bonus", "add_penalty", "reset_score"]

    def level_display(self, obj):
        return obj.get_level_display()

    level_display.short_description = "信誉等级"

    def add_bonus(self, request, queryset):
        for rep in queryset:
            rep.update_score(5, "管理员奖励")
        self.message_user(request, f"已为 {queryset.count()} 个用户奖励 5 分")

    add_bonus.short_description = "奖励 5 分"

    def add_penalty(self, request, queryset):
        for rep in queryset:
            rep.update_score(-5, "管理员惩罚")
        self.message_user(request, f"已对 {queryset.count()} 个用户扣 5 分")

    add_penalty.short_description = "惩罚 5 分"

    def reset_score(self, request, queryset):
        for rep in queryset:
            rep.update_score(50 - rep.score, "管理员重置")
        self.message_user(request, f"已重置 {queryset.count()} 个用户的信誉分")

    reset_score.short_description = "重置为 50 分"


@admin.register(ReputationLog, site=admin_site)
class ReputationLogAdmin(admin.ModelAdmin):
    """信誉日志管理"""

    list_display = ["user_reputation", "action", "old_score", "new_score", "delta", "reason", "created_at"]
    list_filter = ["action"]
    search_fields = ["user_reputation__user__username", "reason"]
    readonly_fields = ["user_reputation", "action", "old_score", "new_score", "delta", "reason", "created_at"]
    date_hierarchy = "created_at"


# ========== 网站配置 ==========
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


# ========== 工具配置 ==========
from apps.tools.models import ToolConfig


@admin.register(ToolConfig, site=admin_site)
class ToolConfigAdmin(admin.ModelAdmin):
    """工具配置管理"""

    list_display = ["name", "slug", "is_enabled", "sort_order"]
    list_filter = ["is_enabled"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


# ========== Django 内置模型 ==========
admin_site.register(Group)
admin_site.register(Site)
