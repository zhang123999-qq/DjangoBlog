"""
性能优化工具模块

提供：
- 数据库连接池监控
- 缓存命中率统计
- 慢查询日志装饰器
- 批量操作优化
"""

import time
import logging
from functools import wraps
from django.core.cache import cache
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class CacheStats:
    """缓存统计工具"""
    
    _hits = 0
    _misses = 0
    
    @classmethod
    def record_hit(cls):
        cls._hits += 1
    
    @classmethod
    def record_miss(cls):
        cls._misses += 1
    
    @classmethod
    def get_stats(cls):
        total = cls._hits + cls._misses
        hit_rate = (cls._hits / total * 100) if total > 0 else 0
        return {
            'hits': cls._hits,
            'misses': cls._misses,
            'total': total,
            'hit_rate': f'{hit_rate:.2f}%'
        }
    
    @classmethod
    def reset(cls):
        cls._hits = 0
        cls._misses = 0


def cache_with_stats(key, timeout=300):
    """
    带统计的缓存装饰器
    
    用法:
        @cache_with_stats('my_key', timeout=600)
        def get_expensive_data():
            return expensive_operation()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试从缓存获取
            result = cache.get(key)
            
            if result is not None:
                CacheStats.record_hit()
                logger.debug(f'缓存命中: {key}')
                return result
            
            # 缓存未命中，执行函数
            CacheStats.record_miss()
            logger.debug(f'缓存未命中: {key}')
            
            result = func(*args, **kwargs)
            cache.set(key, result, timeout)
            
            return result
        return wrapper
    return decorator


def slow_query_log(threshold_ms=100):
    """
    慢查询日志装饰器
    
    用法:
        @slow_query_log(threshold_ms=50)
        def get_posts():
            return Post.objects.all()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # 记录执行前的查询数
            queries_before = len(connection.queries)
            
            result = func(*args, **kwargs)
            
            # 计算执行时间
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录执行后的查询数
            queries_after = len(connection.queries)
            query_count = queries_after - queries_before
            
            # 慢查询警告
            if duration_ms > threshold_ms:
                logger.warning(
                    f'慢查询警告: {func.__name__} 耗时 {duration_ms:.2f}ms, '
                    f'执行了 {query_count} 个数据库查询'
                )
            
            return result
        return wrapper
    return decorator


class QueryCounter:
    """
    查询计数器上下文管理器
    
    用法:
        with QueryCounter() as counter:
            posts = Post.objects.all()
            for post in posts:
                print(post.title)
        
        print(f'执行了 {counter.count} 个查询')
    """
    
    def __init__(self):
        self.count = 0
        self.queries = []
    
    def __enter__(self):
        self.queries_before = len(connection.queries)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.queries_after = len(connection.queries)
        self.count = self.queries_after - self.queries_before
        self.queries = connection.queries[self.queries_before:self.queries_after]
        return False


def get_db_connection_info():
    """获取数据库连接池信息"""
    from django.db import connections
    
    info = {}
    for alias in connections:
        conn = connections[alias]
        if hasattr(conn, 'connection'):
            info[alias] = {
                'engine': conn.settings_dict.get('ENGINE', 'unknown'),
                'max_age': conn.settings_dict.get('CONN_MAX_AGE', 0),
                'is_usable': conn.is_usable() if hasattr(conn, 'is_usable') else 'N/A',
            }
    
    return info


def optimize_queryset(queryset, select_related=None, prefetch_related=None, only=None):
    """
    优化 QuerySet 的辅助函数
    
    用法:
        posts = optimize_queryset(
            Post.objects.all(),
            select_related=['author', 'category'],
            prefetch_related=['tags', 'comments'],
            only=['id', 'title', 'slug', 'author__username']
        )
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
    
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    if only:
        queryset = queryset.only(*only)
    
    return queryset


def bulk_create_optimized(model, objects, batch_size=1000):
    """
    批量创建优化
    
    用法:
        posts = [Post(title=f'Post {i}') for i in range(10000)]
        bulk_create_optimized(Post, posts, batch_size=500)
    """
    created_count = 0
    
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        created = model.objects.bulk_create(batch)
        created_count += len(created)
    
    return created_count


def get_performance_report():
    """获取性能报告"""
    from django.core.cache import caches
    
    report = {
        'cache_stats': CacheStats.get_stats(),
        'db_connections': get_db_connection_info(),
    }
    
    # Redis 信息（如果使用）
    try:
        redis_cache = caches.get('default')
        if hasattr(redis_cache, 'client'):
            client = redis_cache.client.get_client()
            info = client.info()
            report['redis'] = {
                'connected_clients': info.get('connected_clients', 'N/A'),
                'used_memory_human': info.get('used_memory_human', 'N/A'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
    except Exception as e:
        report['redis_error'] = str(e)
    
    return report
