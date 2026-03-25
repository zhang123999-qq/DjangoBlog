"""
Redis 内存优化和回收机制

功能：
- 内存使用监控
- 缓存键分析
- 过期键清理
- 内存回收建议
"""

import logging
from typing import Any, Dict

from django.core.cache import cache

logger = logging.getLogger(__name__)


def _log_cache_error(op: str, exc: Exception, **context):
    logger.exception('[cache_optimizer.%s] failed: %s | context=%s', op, exc, context)


def _error_payload(code: str, message: str = 'cache operation failed') -> Dict[str, Any]:
    return {'ok': False, 'error_code': code, 'message': message}


class RedisMemoryOptimizer:
    """Redis 内存优化器"""

    KNOWN_PREFIXES = [
        'site_config',
        'blog_categories',
        'blog_tags',
        'sensitive_words',
        'site_statistics',
        ':1:',
    ]

    @classmethod
    def _get_client(cls):
        from django_redis import get_redis_connection

        return get_redis_connection('default')

    @classmethod
    def get_memory_info(cls):
        """获取 Redis 内存信息。"""
        try:
            client = cls._get_client()
            info = client.info()
            return {
                'ok': True,
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', 'N/A'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', 'N/A'),
                'used_memory_rss': info.get('used_memory_rss', 0),
                'used_memory_dataset': info.get('used_memory_dataset', 0),
                'mem_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0),
                'total_system_memory': info.get('total_system_memory', 0),
                'maxmemory': info.get('maxmemory', 0),
            }
        except Exception as e:
            _log_cache_error('get_memory_info', e)
            return _error_payload('CACHE_MEMORY_INFO_FAILED')

    @classmethod
    def get_key_count(cls):
        """获取缓存键数量。"""
        try:
            client = cls._get_client()
            return client.dbsize()
        except Exception as e:
            _log_cache_error('get_key_count', e)
            return 0

    @classmethod
    def analyze_keys(cls):
        """分析缓存键（SCAN 采样，避免 KEYS * 阻塞）。"""
        try:
            client = cls._get_client()

            sampled_keys = []
            for key in client.scan_iter(match='*', count=200):
                sampled_keys.append(key)
                if len(sampled_keys) >= 1000:
                    break

            key_types = {}
            key_prefixes = {}
            ttl_distribution = {
                'no_expiry': 0,
                '< 1h': 0,
                '< 1d': 0,
                '< 7d': 0,
                '> 7d': 0,
            }

            for key in sampled_keys:
                key_type_raw = client.type(key)
                key_type = key_type_raw.decode() if isinstance(key_type_raw, bytes) else key_type_raw
                key_types[key_type] = key_types.get(key_type, 0) + 1

                key_str = key.decode() if isinstance(key, bytes) else key
                for prefix in cls.KNOWN_PREFIXES:
                    if key_str.startswith(prefix):
                        key_prefixes[prefix] = key_prefixes.get(prefix, 0) + 1
                        break

                ttl = client.ttl(key)
                if ttl == -1:
                    ttl_distribution['no_expiry'] += 1
                elif ttl == -2:
                    continue
                elif ttl < 3600:
                    ttl_distribution['< 1h'] += 1
                elif ttl < 86400:
                    ttl_distribution['< 1d'] += 1
                elif ttl < 604800:
                    ttl_distribution['< 7d'] += 1
                else:
                    ttl_distribution['> 7d'] += 1

            return {
                'ok': True,
                'total_keys': client.dbsize(),
                'sampled_keys': len(sampled_keys),
                'key_types': key_types,
                'key_prefixes': key_prefixes,
                'ttl_distribution': ttl_distribution,
            }
        except Exception as e:
            _log_cache_error('analyze_keys', e)
            return _error_payload('CACHE_ANALYZE_FAILED')

    @classmethod
    def cleanup_expired_keys(cls):
        """清理过期键（补充检查）。"""
        try:
            client = cls._get_client()
            info = client.info()
            expired_keys = info.get('expired_keys', 0)
            evicted_keys = info.get('evicted_keys', 0)

            if evicted_keys > 0:
                logger.warning('Redis 已驱逐 %s 个键，考虑增加内存或优化缓存策略', evicted_keys)

            return {
                'ok': True,
                'expired_keys': expired_keys,
                'evicted_keys': evicted_keys,
            }
        except Exception as e:
            _log_cache_error('cleanup_expired_keys', e)
            return _error_payload('CACHE_CLEANUP_FAILED')

    @classmethod
    def get_optimization_suggestions(cls):
        """获取优化建议。"""
        suggestions = []

        memory_info = cls.get_memory_info()
        key_analysis = cls.analyze_keys()

        if not memory_info.get('ok', False) or not key_analysis.get('ok', False):
            suggestions.append({'level': 'warning', 'message': '部分缓存分析失败，请检查 Redis 连接状态'})
            return suggestions

        used_memory_mb = memory_info.get('used_memory', 0) / (1024 * 1024)
        if used_memory_mb > 500:
            suggestions.append({'level': 'warning', 'message': f'Redis 内存使用较高 ({used_memory_mb:.2f}MB)'})

        fragmentation = memory_info.get('mem_fragmentation_ratio', 0)
        if fragmentation > 1.5:
            suggestions.append({'level': 'info', 'message': f'内存碎片率较高 ({fragmentation:.2f})'})

        ttl_dist = key_analysis.get('ttl_distribution', {})
        no_expiry = ttl_dist.get('no_expiry', 0)
        if no_expiry > 100:
            suggestions.append({'level': 'info', 'message': f'有 {no_expiry} 个键未设置过期时间'})

        return suggestions

    @classmethod
    def get_full_report(cls):
        """获取完整报告。"""
        return {
            'memory': cls.get_memory_info(),
            'keys': cls.get_key_count(),
            'analysis': cls.analyze_keys(),
            'suggestions': cls.get_optimization_suggestions(),
        }


class CacheWarmer:
    """缓存预热器"""

    @staticmethod
    def warmup_all():
        """预热所有缓存。"""
        results = {}

        try:
            from apps.core.models import SiteConfig

            SiteConfig.get_solo()
            results['site_config'] = 'warmed'
        except Exception as e:
            _log_cache_error('warmup_site_config', e)
            results['site_config'] = 'error'

        try:
            from apps.blog.views import get_categories_and_tags

            get_categories_and_tags()
            results['categories_tags'] = 'warmed'
        except Exception as e:
            _log_cache_error('warmup_categories_tags', e)
            results['categories_tags'] = 'error'

        try:
            from moderation.utils import get_sensitive_words

            get_sensitive_words()
            results['sensitive_words'] = 'warmed'
        except Exception as e:
            _log_cache_error('warmup_sensitive_words', e)
            results['sensitive_words'] = 'error'

        try:
            from apps.core.maintenance_tasks import generate_statistics

            generate_statistics()
            results['statistics'] = 'warmed'
        except Exception as e:
            _log_cache_error('warmup_statistics', e)
            results['statistics'] = 'error'

        return results


class CacheInvalidator:
    """缓存失效器"""

    KEY_MAPPING = {
        'post': ['blog_categories', 'blog_tags', 'site_statistics'],
        'comment': ['site_statistics'],
        'topic': ['site_statistics'],
        'reply': ['site_statistics'],
        'user': ['site_statistics'],
        'sensitive_word': ['sensitive_words'],
        'site_config': ['site_config_solo'],
    }

    @classmethod
    def invalidate(cls, model_name):
        """失效指定模型缓存。"""
        keys_to_delete = cls.KEY_MAPPING.get(model_name, [])

        for key in keys_to_delete:
            try:
                cache.delete(key)
                logger.info('缓存已失效: %s', key)
            except Exception as e:
                _log_cache_error('invalidate', e, key=key, model_name=model_name)

        return keys_to_delete

    @classmethod
    def invalidate_all(cls):
        """失效所有缓存。"""
        try:
            from django_redis import get_redis_connection

            client = get_redis_connection('default')
            client.flushdb()
            logger.warning('所有缓存已清空')
            return True
        except Exception as e:
            _log_cache_error('invalidate_all', e)
            return False


def get_redis_optimizer():
    return RedisMemoryOptimizer()


def get_cache_report():
    return RedisMemoryOptimizer.get_full_report()
