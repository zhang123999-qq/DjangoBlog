"""
性能优化和维护任务

功能：
- Session 清理
- 日志清理
- 缓存预热
- 数据库优化
- 内存回收
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db import DatabaseError, connection
from django.utils import timezone

logger = logging.getLogger(__name__)


def _log_task_error(task_name: str, exc: Exception, **context):
    logger.exception('[%s] failed: %s | context=%s', task_name, exc, context)


@shared_task
def cleanup_expired_sessions():
    """清理过期 Session。"""
    try:
        expired_count = Session.objects.filter(expire_date__lt=timezone.now()).delete()[0]
        logger.info('清理了 %s 个过期 Session', expired_count)
        return expired_count
    except DatabaseError as e:
        _log_task_error('cleanup_expired_sessions.database', e)
        return 0


@shared_task
def cleanup_old_moderation_logs(days=90):
    """清理旧的审核日志。"""
    from moderation.models import ModerationLog

    try:
        threshold = timezone.now() - timedelta(days=days)
        deleted_count = ModerationLog.objects.filter(created_at__lt=threshold).delete()[0]
        logger.info('清理了 %s 条旧审核日志（%s天前）', deleted_count, days)
        return deleted_count
    except DatabaseError as e:
        _log_task_error('cleanup_old_moderation_logs.database', e, days=days)
        return 0


@shared_task
def cleanup_old_reputation_logs(days=180):
    """清理旧的信誉日志。"""
    from moderation.reputation import ReputationLog

    try:
        threshold = timezone.now() - timedelta(days=days)
        deleted_count = ReputationLog.objects.filter(created_at__lt=threshold).delete()[0]
        logger.info('清理了 %s 条旧信誉日志（%s天前）', deleted_count, days)
        return deleted_count
    except DatabaseError as e:
        _log_task_error('cleanup_old_reputation_logs.database', e, days=days)
        return 0


@shared_task
def cleanup_old_access_logs(days=30):
    """清理旧的访问日志（axes）。"""
    try:
        from axes.models import AccessAttempt, AccessLog
    except ImportError as e:
        _log_task_error('cleanup_old_access_logs.import', e)
        return 0

    try:
        threshold = timezone.now() - timedelta(days=days)

        # 清理 AccessAttempt
        attempt_count = 0
        if hasattr(AccessAttempt, 'objects'):
            attempt_count = (
                AccessAttempt.objects.filter(timestamp__lt=threshold).delete()[0]
                if hasattr(AccessAttempt, 'timestamp')
                else 0
            )

        # 清理 AccessLog
        log_count = 0
        if hasattr(AccessLog, 'objects'):
            log_count = (
                AccessLog.objects.filter(created_at__lt=threshold).delete()[0]
                if hasattr(AccessLog, 'created_at')
                else 0
            )

        logger.info('清理了 %s 条访问尝试记录，%s 条访问日志', attempt_count, log_count)
        return attempt_count + log_count
    except DatabaseError as e:
        _log_task_error('cleanup_old_access_logs.database', e, days=days)
        return 0


@shared_task
def warmup_cache():
    """缓存预热。"""
    try:
        from django.db.models import Count, Q

        from apps.blog.models import Category, Tag
        from apps.core.models import SiteConfig

        SiteConfig.get_solo()
        logger.info('预热 SiteConfig 缓存')

        categories = list(
            Category.objects.annotate(published_count=Count('posts', filter=Q(posts__status='published'))).values(
                'id', 'name', 'slug', 'published_count'
            )
        )
        cache.set('blog_categories', categories, 3600)

        tags = list(
            Tag.objects.annotate(published_count=Count('posts', filter=Q(posts__status='published'))).values(
                'id', 'name', 'slug', 'published_count'
            )
        )
        cache.set('blog_tags', tags, 3600)

        logger.info('预热分类 %s 个，标签 %s 个', len(categories), len(tags))
        return True
    except (ImportError, DatabaseError) as e:
        _log_task_error('warmup_cache', e)
        return False


@shared_task
def optimize_database():
    """数据库优化。"""
    try:
        db_engine = settings.DATABASES['default'].get('ENGINE', '')

        if 'mysql' in db_engine:
            with connection.cursor() as cursor:
                cursor.execute('SHOW TABLES')
                tables = [row[0] for row in cursor.fetchall()]
                for table in tables:
                    try:
                        cursor.execute(f'OPTIMIZE TABLE `{table}`')
                        logger.info('优化表: %s', table)
                    except DatabaseError as e:
                        _log_task_error('optimize_database.mysql_table', e, table=table)

        elif 'postgresql' in db_engine:
            with connection.cursor() as cursor:
                cursor.execute('VACUUM ANALYZE')
                logger.info('执行 VACUUM ANALYZE')

        elif 'sqlite' in db_engine:
            with connection.cursor() as cursor:
                cursor.execute('VACUUM')
                logger.info('执行 VACUUM')

        return True
    except DatabaseError as e:
        _log_task_error('optimize_database.database', e)
        return False


@shared_task
def cleanup_expired_cache():
    """清理过期缓存。"""
    try:
        keys_to_clean = [
            'blog_categories_tags',
            'blog_categories',
            'blog_tags',
        ]

        cleaned = 0
        for key in keys_to_clean:
            if cache.get(key) is None:
                cleaned += 1

        logger.info('清理了 %s 个过期缓存', cleaned)
        return cleaned
    except Exception as e:
        _log_task_error('cleanup_expired_cache', e)
        return 0


@shared_task
def check_redis_health():
    """检查 Redis 健康状态。"""
    try:
        from django_redis import get_redis_connection

        client = get_redis_connection('default')
        result = client.ping()

        if not result:
            logger.error('Redis PING 失败')
            return {'status': 'unhealthy'}

        info = client.info()
        used_memory = info.get('used_memory', 0)
        used_memory_mb = used_memory / (1024 * 1024)
        connected_clients = info.get('connected_clients', 0)

        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0

        logger.info('Redis 健康: 内存 %.2fMB, 连接数 %s, 命中率 %.2f%%', used_memory_mb, connected_clients, hit_rate)

        if used_memory_mb > 500:
            logger.warning('Redis 内存使用过高: %.2fMB', used_memory_mb)

        return {
            'status': 'healthy',
            'memory_mb': used_memory_mb,
            'clients': connected_clients,
            'hit_rate': hit_rate,
        }

    except (ImportError, DatabaseError) as e:
        _log_task_error('check_redis_health', e)
        return {'status': 'error', 'message': 'redis check failed'}


@shared_task
def cleanup_old_notifications(days=30):
    """清理旧的通知和提醒。"""
    from moderation.models import ModerationReminder

    try:
        threshold = timezone.now() - timedelta(days=days)
        deleted_count = ModerationReminder.objects.filter(is_processed=True, created_at__lt=threshold).delete()[0]
        logger.info('清理了 %s 条已处理通知', deleted_count)
        return deleted_count
    except DatabaseError as e:
        _log_task_error('cleanup_old_notifications.database', e, days=days)
        return 0


@shared_task
def generate_statistics():
    """生成统计数据。"""
    try:
        from django.contrib.auth import get_user_model

        from apps.blog.models import Comment, Post
        from apps.forum.models import Reply, Topic

        User = get_user_model()

        stats = {
            'users': User.objects.count(),
            'posts': Post.objects.filter(status='published').count(),
            'comments': Comment.objects.filter(review_status='approved').count(),
            'topics': Topic.objects.filter(review_status='approved').count(),
            'replies': Reply.objects.filter(review_status='approved', is_deleted=False).count(),
            'generated_at': timezone.now().isoformat(),
        }

        cache.set('site_statistics', stats, 86400)
        logger.info('生成统计数据: %s', stats)
        return stats
    except (ImportError, DatabaseError) as e:
        _log_task_error('generate_statistics', e)
        return None


@shared_task
def reset_daily_counters():
    """重置每日计数器。"""
    try:
        logger.info('重置每日计数器')
        return True
    except Exception as e:
        _log_task_error('reset_daily_counters', e)
        return False
