"""
自定义 AdminSite 和首页仪表盘
"""

from django.contrib import admin
from datetime import datetime, timedelta
import sys
import platform


class DjangoBlogAdminSite(admin.AdminSite):
    """自定义后台，带统计仪表盘"""

    site_header = "DjangoBlog 管理后台"
    site_title = "DjangoBlog Admin"
    index_title = "仪表盘"

    def index(self, request, extra_context=None):
        """自定义首页，添加统计数据"""
        from django.utils import timezone
        from django.conf import settings
        from django.db.models import Sum
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

        extra_context.update({
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
        })

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
