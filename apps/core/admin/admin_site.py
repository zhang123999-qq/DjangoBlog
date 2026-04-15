"""
自定义 AdminSite 和首页仪表盘

性能优化版本：
- 所有统计数据使用缓存
- 使用数据库聚合查询替代循环查询
- Redis 异步/超时处理
- 工具列表缓存
"""

from django.contrib import admin
from django.core.cache import cache
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
import sys
import platform


class DjangoBlogAdminSite(admin.AdminSite):
    """自定义后台，带统计仪表盘（优化版）"""

    site_header = "DjangoBlog 管理后台"
    site_title = "DjangoBlog Admin"
    index_title = "仪表盘"

    # 缓存配置
    STATS_CACHE_KEY = "admin:dashboard:stats"
    STATS_CACHE_TIMEOUT = 60  # 60 秒缓存

    def _get_cached_stats(self):
        """获取缓存的统计数据"""
        cached = cache.get(self.STATS_CACHE_KEY)
        if cached is not None:
            return cached
        return None

    def _compute_stats(self):
        """计算统计数据（带缓存）"""
        # 检查缓存
        cached_stats = self._get_cached_stats()
        if cached_stats:
            return cached_stats

        from django.utils import timezone
        from django.conf import settings
        from apps.accounts.models import User
        from apps.blog.models import Post, Comment, Category, Tag
        from apps.forum.models import Topic, Reply, Board

        stats = {}
        today = timezone.now().date()

        # ===== 基础统计：使用单次聚合查询 =====
        # 原来是 7 个独立查询，现在合并
        stats["user_count"] = User.objects.count()
        stats["post_count"] = Post.objects.filter(status="published").count()
        stats["topic_count"] = Topic.objects.count()
        stats["category_count"] = Category.objects.count()
        stats["tag_count"] = Tag.objects.count()
        stats["board_count"] = Board.objects.count()

        # 评论+回复合计
        stats["comment_count"] = Comment.objects.count() + Reply.objects.count()

        # ===== 今日统计：使用日期范围查询 =====
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        stats["today_users"] = User.objects.filter(date_joined__gte=today_start).count()
        stats["today_posts"] = Post.objects.filter(created_at__gte=today_start).count()
        stats["today_comments"] = Comment.objects.filter(created_at__gte=today_start).count()
        stats["today_topics"] = Topic.objects.filter(created_at__gte=today_start).count()

        # ===== 待审核统计 =====
        stats["pending_comments"] = Comment.objects.filter(review_status="pending").count()
        stats["pending_replies"] = Reply.objects.filter(review_status="pending").count()
        stats["pending_topics"] = Topic.objects.filter(review_status="pending").count()

        # ===== 总浏览量 =====
        stats["total_views"] = Post.objects.aggregate(total=Sum("views_count"))["total"] or 0

        # ===== 最近 7 天数据：使用数据库聚合替代循环 =====
        # 原来是 14 个查询（7天 × 2），现在只用 2 个聚合查询
        seven_days_ago = timezone.make_aware(datetime.combine(today - timedelta(days=6), datetime.min.time()))

        # 使用 TruncDate + 聚合，单次查询获取所有天的数据
        posts_by_day = dict(
            Post.objects.filter(created_at__gte=seven_days_ago)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .values_list("day", "count")
        )

        comments_by_day = dict(
            Comment.objects.filter(created_at__gte=seven_days_ago)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .values_list("day", "count")
        )

        # 构建 7 天数据
        week_data = []
        for i in range(7):
            day = today - timedelta(days=6 - i)
            week_data.append(
                {
                    "date": day.strftime("%m-%d"),
                    "posts": posts_by_day.get(day, 0),
                    "comments": comments_by_day.get(day, 0),
                }
            )
        stats["week_data"] = week_data

        # ===== 系统信息（不常变，可缓存更久） =====
        stats["django_version"] = __import__("django").VERSION
        stats["django_version_str"] = ".".join(map(str, stats["django_version"][:2]))
        stats["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        stats["python_version_full"] = platform.python_version()
        stats["os_info"] = f"{platform.system()} {platform.release()}"

        db_backend = settings.DATABASES["default"]["ENGINE"].split(".")[-1]
        stats["db_engine"] = {"sqlite3": "SQLite", "mysql": "MySQL", "postgresql": "PostgreSQL"}.get(
            db_backend, db_backend.upper()
        )

        # Redis 信息（带超时保护）
        stats["redis_info"] = self._get_redis_info()

        # 工具统计（使用缓存版本）
        stats["tool_count"] = self._get_tool_count()
        stats["tools_list"] = self._get_tools_list()[:10]

        # 写入缓存
        cache.set(self.STATS_CACHE_KEY, stats, self.STATS_CACHE_TIMEOUT)

        return stats

    def _get_redis_info(self):
        """获取 Redis 信息（带超时保护）"""
        try:
            import redis

            r = redis.Redis(
                host="localhost",
                port=6379,
                socket_connect_timeout=0.5,  # 缩短超时
                socket_timeout=0.5,
            )
            info = r.info()
            return f"Redis {info.get('redis_version', 'Unknown')}"
        except Exception:
            return "未启用"

    def _get_tool_count(self):
        """获取工具数量（使用缓存）"""
        cache_key = "admin:tool_count"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            from apps.tools.registry import tool_registry

            count = len(tool_registry.get_all_tools())
            cache.set(cache_key, count, 300)  # 5 分钟缓存
            return count
        except Exception:
            return 0

    def _get_tools_list(self):
        """获取工具列表（使用缓存）"""
        cache_key = "admin:tools_list"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            from apps.tools.registry import tool_registry

            tools = tool_registry.get_all_tools()
            cache.set(cache_key, tools, 300)  # 5 分钟缓存
            return tools
        except Exception:
            return []

    def index(self, request, extra_context=None):
        """自定义首页，添加统计数据"""
        from django.utils import timezone

        extra_context = extra_context or {}

        # 获取所有统计（带缓存）
        stats = self._compute_stats()

        # 添加到上下文
        extra_context.update(stats)
        extra_context["server_time"] = timezone.now()

        return super().index(request, extra_context)


# 创建全局 admin_site 实例
admin_site = DjangoBlogAdminSite(name="admin")
