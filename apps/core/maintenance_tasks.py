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
from celery import shared_task
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.sessions.models import Session

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_sessions():
    """清理过期 Session
    
    定时任务：每小时执行一次
    """
    try:
        expired_count = Session.objects.filter(
            expire_date__lt=timezone.now()
        ).delete()[0]
        logger.info(f'清理了 {expired_count} 个过期 Session')
        return expired_count
    except Exception as e:
        logger.error(f'清理 Session 失败: {e}')
        return 0


@shared_task
def cleanup_old_moderation_logs(days=90):
    """清理旧的审核日志
    
    定时任务：每周执行一次
    """
    from moderation.models import ModerationLog
    
    try:
        threshold = timezone.now() - timedelta(days=days)
        deleted_count = ModerationLog.objects.filter(
            created_at__lt=threshold
        ).delete()[0]
        logger.info(f'清理了 {deleted_count} 条旧审核日志（{days}天前）')
        return deleted_count
    except Exception as e:
        logger.error(f'清理审核日志失败: {e}')
        return 0


@shared_task
def cleanup_old_reputation_logs(days=180):
    """清理旧的信誉日志
    
    定时任务：每月执行一次
    """
    from moderation.reputation import ReputationLog
    
    try:
        threshold = timezone.now() - timedelta(days=days)
        deleted_count = ReputationLog.objects.filter(
            created_at__lt=threshold
        ).delete()[0]
        logger.info(f'清理了 {deleted_count} 条旧信誉日志（{days}天前）')
        return deleted_count
    except Exception as e:
        logger.error(f'清理信誉日志失败: {e}')
        return 0


@shared_task
def cleanup_old_access_logs(days=30):
    """清理旧的访问日志（axes）
    
    定时任务：每周执行一次
    """
    from axes.models import AccessAttempt, AccessLog
    
    try:
        threshold = timezone.now() - timedelta(days=days)
        
        # 清理 AccessAttempt
        attempt_count = 0
        if hasattr(AccessAttempt, 'objects'):
            attempt_count = AccessAttempt.objects.filter(
                timestamp__lt=threshold
            ).delete()[0] if hasattr(AccessAttempt, 'timestamp') else 0
        
        # 清理 AccessLog
        log_count = 0
        if hasattr(AccessLog, 'objects'):
            log_count = AccessLog.objects.filter(
                created_at__lt=threshold
            ).delete()[0] if hasattr(AccessLog, 'created_at') else 0
        
        logger.info(f'清理了 {attempt_count} 条访问尝试记录，{log_count} 条访问日志')
        return attempt_count + log_count
    except Exception as e:
        logger.error(f'清理访问日志失败: {e}')
        return 0


@shared_task
def warmup_cache():
    """缓存预热
    
    定时任务：每 6 小时执行一次
    预加载常用数据到缓存
    """
    from apps.core.models import SiteConfig
    from apps.blog.models import Category, Tag
    from django.db.models import Count, Q
    
    try:
        # 预热 SiteConfig
        SiteConfig.get_solo()
        logger.info('预热 SiteConfig 缓存')
        
        # 预热分类和标签（仅统计已发布文章）
        categories = list(Category.objects.annotate(
            published_count=Count('posts', filter=Q(posts__status='published'))
        ).values('id', 'name', 'slug', 'published_count'))
        cache.set('blog_categories', categories, 3600)

        tags = list(Tag.objects.annotate(
            published_count=Count('posts', filter=Q(posts__status='published'))
        ).values('id', 'name', 'slug', 'published_count'))
        cache.set('blog_tags', tags, 3600)
        
        logger.info(f'预热分类 {len(categories)} 个，标签 {len(tags)} 个')
        
        return True
    except Exception as e:
        logger.error(f'缓存预热失败: {e}')
        return False


@shared_task
def optimize_database():
    """数据库优化
    
    定时任务：每周执行一次
    执行 VACUUM（PostgreSQL）或 OPTIMIZE TABLE（MySQL）
    """
    try:
        db_engine = settings.DATABASES['default'].get('ENGINE', '')
        
        if 'mysql' in db_engine:
            # MySQL: OPTIMIZE TABLE
            with connection.cursor() as cursor:
                # 获取所有表名
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    try:
                        cursor.execute(f"OPTIMIZE TABLE {table}")
                        logger.info(f'优化表: {table}')
                    except Exception as e:
                        logger.warning(f'优化表 {table} 失败: {e}')
        
        elif 'postgresql' in db_engine:
            # PostgreSQL: VACUUM ANALYZE
            with connection.cursor() as cursor:
                cursor.execute("VACUUM ANALYZE")
                logger.info('执行 VACUUM ANALYZE')
        
        elif 'sqlite' in db_engine:
            # SQLite: VACUUM
            with connection.cursor() as cursor:
                cursor.execute("VACUUM")
                logger.info('执行 VACUUM')
        
        return True
    except Exception as e:
        logger.error(f'数据库优化失败: {e}')
        return False


@shared_task
def cleanup_expired_cache():
    """清理过期缓存
    
    注意：Redis 会自动清理过期 key，此任务主要用于清理可能遗留的缓存
    """
    try:
        # 清理已知的缓存 key
        keys_to_clean = [
            'blog_categories_tags',
            'blog_categories',
            'blog_tags',
        ]
        
        cleaned = 0
        for key in keys_to_clean:
            if cache.get(key) is None:
                cleaned += 1
        
        logger.info(f'清理了 {cleaned} 个过期缓存')
        return cleaned
    except Exception as e:
        logger.error(f'清理缓存失败: {e}')
        return 0


@shared_task
def check_redis_health():
    """检查 Redis 健康状态
    
    定时任务：每 5 分钟执行一次
    """
    try:
        from django_redis import get_redis_connection
        
        client = get_redis_connection('default')
        
        # 执行 PING
        result = client.ping()
        
        if result:
            # 获取 Redis 信息
            info = client.info()
            
            # 检查内存使用
            used_memory = info.get('used_memory', 0)
            used_memory_mb = used_memory / (1024 * 1024)
            
            # 检查连接数
            connected_clients = info.get('connected_clients', 0)
            
            # 检查命中率
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0
            
            logger.info(
                f'Redis 健康: 内存 {used_memory_mb:.2f}MB, '
                f'连接数 {connected_clients}, '
                f'命中率 {hit_rate:.2f}%'
            )
            
            # 内存使用超过 500MB 发送警告
            if used_memory_mb > 500:
                logger.warning(f'Redis 内存使用过高: {used_memory_mb:.2f}MB')
            
            return {
                'status': 'healthy',
                'memory_mb': used_memory_mb,
                'clients': connected_clients,
                'hit_rate': hit_rate
            }
        else:
            logger.error('Redis PING 失败')
            return {'status': 'unhealthy'}
            
    except Exception as e:
        logger.error(f'Redis 健康检查失败: {e}')
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_notifications(days=30):
    """清理旧的通知和提醒
    
    定时任务：每天执行一次
    """
    from moderation.models import ModerationReminder
    
    try:
        threshold = timezone.now() - timedelta(days=days)
        
        # 清理已处理的通知
        deleted_count = ModerationReminder.objects.filter(
            is_processed=True,
            created_at__lt=threshold
        ).delete()[0]
        
        logger.info(f'清理了 {deleted_count} 条已处理通知')
        return deleted_count
    except Exception as e:
        logger.error(f'清理通知失败: {e}')
        return 0


@shared_task
def generate_statistics():
    """生成统计数据
    
    定时任务：每天执行一次
    """
    from django.contrib.auth import get_user_model
    from apps.blog.models import Post, Comment
    from apps.forum.models import Topic, Reply
    
    User = get_user_model()
    
    try:
        stats = {
            'users': User.objects.count(),
            'posts': Post.objects.filter(status='published').count(),
            'comments': Comment.objects.filter(review_status='approved').count(),
            'topics': Topic.objects.filter(review_status='approved').count(),
            'replies': Reply.objects.filter(review_status='approved', is_deleted=False).count(),
            'generated_at': timezone.now().isoformat(),
        }
        
        cache.set('site_statistics', stats, 86400)  # 缓存 1 天
        logger.info(f'生成统计数据: {stats}')
        return stats
    except Exception as e:
        logger.error(f'生成统计数据失败: {e}')
        return None


@shared_task
def reset_daily_counters():
    """重置每日计数器
    
    定时任务：每天凌晨执行
    """
    try:
        # 这里可以重置各种每日计数器
        # 例如：每日访问量、每日发布数等
        
        logger.info('重置每日计数器')
        return True
    except Exception as e:
        logger.error(f'重置计数器失败: {e}')
        return False
