"""
博客应用 Celery 任务

功能：
- 浏览量 Redis 计数同步
- 热门文章统计
"""

import logging

from celery import shared_task
from django.core.cache import cache

from apps.core.celery_lock import task_lock
from apps.core.constants import (
    CACHE_TTL_LONG,
    HOT_POSTS_MONTH_DAYS,
    HOT_POSTS_MONTH_LIMIT,
    HOT_POSTS_WEEK_DAYS,
    HOT_POSTS_WEEK_LIMIT,
)

logger = logging.getLogger(__name__)


# Redis key 前缀
VIEWS_CACHE_PREFIX = "post:views:"


@shared_task
def sync_views_to_db():
    """
    将 Redis 中的浏览量同步到数据库

    定时任务：每 5 分钟执行一次
    """
    from apps.core.views_counter import ViewsCounter

    try:
        with task_lock("sync_views_to_db", timeout=300) as acquired:
            if not acquired:
                logger.info("sync_views_to_db: 另一个实例正在运行，跳过")
                return {"synced": 0, "skipped": True}

            # 使用新的 ViewsCounter 同步
            result = ViewsCounter.sync_to_db("post")

            logger.info(f"同步了 {result['synced']} 篇文章的浏览量到数据库")
            return result

    except Exception as e:
        logger.error(f"同步浏览量失败: {e}")
        return {"synced": 0, "error": str(e)}


@shared_task
def update_hot_posts():
    """
    更新热门文章列表

    定时任务：每小时执行一次
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.blog.models import Post

    try:
        with task_lock("update_hot_posts", timeout=300) as acquired:
            if not acquired:
                logger.info("update_hot_posts: 另一个实例正在运行，跳过")
                return {"week": 0, "month": 0, "skipped": True}

            # 获取最近 7 天的热门文章
            week_ago = timezone.now() - timedelta(days=HOT_POSTS_WEEK_DAYS)

            hot_posts = list(
                Post.objects.filter(status="published", published_at__gte=week_ago)
                .order_by("-views_count")[:HOT_POSTS_WEEK_LIMIT]
                .values_list("id", flat=True)
            )

            # 缓存热门文章 ID 列表
            cache.set("blog:hot_posts:week", hot_posts, CACHE_TTL_LONG)

            # 获取最近 30 天的热门文章
            month_ago = timezone.now() - timedelta(days=HOT_POSTS_MONTH_DAYS)

            hot_posts_month = list(
                Post.objects.filter(status="published", published_at__gte=month_ago)
                .order_by("-views_count")[:HOT_POSTS_MONTH_LIMIT]
                .values_list("id", flat=True)
            )

            cache.set("blog:hot_posts:month", hot_posts_month, CACHE_TTL_LONG)

            logger.info(f"更新热门文章: 本周 {len(hot_posts)} 篇，本月 {len(hot_posts_month)} 篇")

            return {"week": len(hot_posts), "month": len(hot_posts_month)}

    except Exception as e:
        logger.error(f"更新热门文章失败: {e}")
        return {"error": str(e)}


@shared_task
def cleanup_old_drafts(days=90):
    """
    清理旧草稿

    定时任务：每周执行一次
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.blog.models import Post

    try:
        with task_lock("cleanup_old_drafts", timeout=300) as acquired:
            if not acquired:
                logger.info("cleanup_old_drafts: 另一个实例正在运行，跳过")
                return 0

            threshold = timezone.now() - timedelta(days=days)

            # 删除超过 90 天未更新的草稿
            deleted_count = Post.objects.filter(status="draft", updated_at__lt=threshold).delete()[0]

            logger.info(f"清理了 {deleted_count} 篇旧草稿（{days}天前）")
            return deleted_count

    except Exception as e:
        logger.error(f"清理旧草稿失败: {e}")
        return 0
