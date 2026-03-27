"""
博客应用 Celery 任务

功能：
- 浏览量 Redis 计数同步
- 热门文章统计
"""

import logging
from celery import shared_task
from django.core.cache import cache
from django.db.models import F

logger = logging.getLogger(__name__)


# Redis key 前缀
VIEWS_CACHE_PREFIX = 'post:views:'
VIEWS_SYNC_BATCH_SIZE = 100  # 每次同步的最大数量


@shared_task
def sync_views_to_db():
    """
    将 Redis 中的浏览量同步到数据库

    定时任务：每 5 分钟执行一次
    """
    from apps.blog.models import Post

    try:
        # 获取所有浏览量 key（优先使用 iter_keys，避免 KEYS * 阻塞）
        if hasattr(cache, 'iter_keys'):
            keys = list(cache.iter_keys(f'{VIEWS_CACHE_PREFIX}*'))
        else:
            keys = []

        if not keys:
            return {'synced': 0, 'message': '没有需要同步的浏览量'}

        synced_count = 0
        batch_updates = {}

        for key in keys:
            try:
                key_str = key.decode() if isinstance(key, bytes) else str(key)
                # 提取 post_id
                post_id = key_str.replace(VIEWS_CACHE_PREFIX, '')
                views = cache.get(key_str, 0)

                if views and isinstance(views, int):
                    batch_updates[int(post_id)] = views
                    # 清除已同步的计数
                    cache.delete(key_str)

            except (ValueError, TypeError) as e:
                logger.warning(f'无效的 key: {key_str}, 错误: {e}')
                continue

        # 批量更新数据库
        if batch_updates:
            for post_id, views in batch_updates.items():
                try:
                    Post.objects.filter(pk=post_id).update(
                        views_count=F('views_count') + views
                    )
                    synced_count += 1
                except Exception as e:
                    logger.error(f'更新文章 {post_id} 浏览量失败: {e}')
                    # 恢复缓存中的计数
                    cache.set(f'{VIEWS_CACHE_PREFIX}{post_id}', views, 3600)

        logger.info(f'同步了 {synced_count} 篇文章的浏览量到数据库')
        return {
            'synced': synced_count,
            'total_views': sum(batch_updates.values())
        }

    except Exception as e:
        logger.error(f'同步浏览量失败: {e}')
        return {'synced': 0, 'error': str(e)}


@shared_task
def update_hot_posts():
    """
    更新热门文章列表

    定时任务：每小时执行一次
    """
    from apps.blog.models import Post
    from django.utils import timezone
    from datetime import timedelta

    try:
        # 获取最近 7 天的热门文章
        week_ago = timezone.now() - timedelta(days=7)

        hot_posts = list(
            Post.objects.filter(
                status='published',
                published_at__gte=week_ago
            ).order_by('-views_count')[:10].values_list('id', flat=True)
        )

        # 缓存热门文章 ID 列表
        cache.set('blog:hot_posts:week', hot_posts, 3600)

        # 获取最近 30 天的热门文章
        month_ago = timezone.now() - timedelta(days=30)

        hot_posts_month = list(
            Post.objects.filter(
                status='published',
                published_at__gte=month_ago
            ).order_by('-views_count')[:20].values_list('id', flat=True)
        )

        cache.set('blog:hot_posts:month', hot_posts_month, 3600)

        logger.info(f'更新热门文章: 本周 {len(hot_posts)} 篇，本月 {len(hot_posts_month)} 篇')

        return {
            'week': len(hot_posts),
            'month': len(hot_posts_month)
        }

    except Exception as e:
        logger.error(f'更新热门文章失败: {e}')
        return {'error': str(e)}


@shared_task
def cleanup_old_drafts(days=90):
    """
    清理旧草稿

    定时任务：每周执行一次
    """
    from apps.blog.models import Post
    from django.utils import timezone
    from datetime import timedelta

    try:
        threshold = timezone.now() - timedelta(days=days)

        # 删除超过 90 天未更新的草稿
        deleted_count = Post.objects.filter(
            status='draft',
            updated_at__lt=threshold
        ).delete()[0]

        logger.info(f'清理了 {deleted_count} 篇旧草稿（{days}天前）')
        return deleted_count

    except Exception as e:
        logger.error(f'清理旧草稿失败: {e}')
        return 0
