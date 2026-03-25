"""
Redis 内存优化和回收机制

功能：
- 内存使用监控
- 缓存键分析
- 过期键清理
- 内存回收建议
"""

import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RedisMemoryOptimizer:
    """Redis 内存优化器"""
    
    # 已知的缓存键前缀
    KNOWN_PREFIXES = [
        'site_config',
        'blog_categories',
        'blog_tags',
        'sensitive_words',
        'site_statistics',
        ':1:',  # Django 默认前缀
    ]
    
    @classmethod
    def get_memory_info(cls):
        """获取 Redis 内存信息"""
        try:
            from django_redis import get_redis_connection
            
            client = get_redis_connection('default')
            info = client.info()
            
            return {
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
            logger.error(f'获取 Redis 内存信息失败: {e}')
            return {}
    
    @classmethod
    def get_key_count(cls):
        """获取缓存键数量"""
        try:
            from django_redis import get_redis_connection
            
            client = get_redis_connection('default')
            
            # 获取键数量
            key_count = client.dbsize()
            
            return key_count
        except Exception as e:
            logger.error(f'获取键数量失败: {e}')
            return 0
    
    @classmethod
    def analyze_keys(cls):
        """分析缓存键"""
        try:
            from django_redis import get_redis_connection
            
            client = get_redis_connection('default')
            
            # 用 SCAN 采样，避免 KEYS * 阻塞
            sampled_keys = []
            for key in client.scan_iter(match='*', count=200):
                sampled_keys.append(key)
                if len(sampled_keys) >= 1000:
                    break

            # 分析键类型
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
                # 键类型
                key_type_raw = client.type(key)
                key_type = key_type_raw.decode() if isinstance(key_type_raw, bytes) else key_type_raw
                key_types[key_type] = key_types.get(key_type, 0) + 1

                # 键前缀
                key_str = key.decode() if isinstance(key, bytes) else key
                for prefix in cls.KNOWN_PREFIXES:
                    if key_str.startswith(prefix):
                        key_prefixes[prefix] = key_prefixes.get(prefix, 0) + 1
                        break

                # TTL 分布
                ttl = client.ttl(key)
                if ttl == -1:
                    ttl_distribution['no_expiry'] += 1
                elif ttl == -2:
                    pass  # 键不存在
                elif ttl < 3600:
                    ttl_distribution['< 1h'] += 1
                elif ttl < 86400:
                    ttl_distribution['< 1d'] += 1
                elif ttl < 604800:
                    ttl_distribution['< 7d'] += 1
                else:
                    ttl_distribution['> 7d'] += 1

            return {
                'total_keys': client.dbsize(),
                'sampled_keys': len(sampled_keys),
                'key_types': key_types,
                'key_prefixes': key_prefixes,
                'ttl_distribution': ttl_distribution,
            }
        except Exception as e:
            logger.error(f'分析缓存键失败: {e}')
            return {}
    
    @classmethod
    def cleanup_expired_keys(cls):
        """清理过期键（Redis 会自动清理，这是补充）"""
        try:
            from django_redis import get_redis_connection
            
            client = get_redis_connection('default')
            
            # Redis 4.0+ 可以使用 LAZY FREE
            # 检查是否有大量过期键
            
            info = client.info()
            expired_keys = info.get('expired_keys', 0)
            evicted_keys = info.get('evicted_keys', 0)
            
            # 如果有内存压力，可以手动触发清理
            if evicted_keys > 0:
                logger.warning(f'Redis 已驱逐 {evicted_keys} 个键，考虑增加内存或优化缓存策略')
            
            return {
                'expired_keys': expired_keys,
                'evicted_keys': evicted_keys,
            }
        except Exception as e:
            logger.error(f'清理过期键失败: {e}')
            return {}
    
    @classmethod
    def get_optimization_suggestions(cls):
        """获取优化建议"""
        suggestions = []
        
        memory_info = cls.get_memory_info()
        key_analysis = cls.analyze_keys()
        
        # 检查内存使用
        used_memory_mb = memory_info.get('used_memory', 0) / (1024 * 1024)
        if used_memory_mb > 500:
            suggestions.append({
                'level': 'warning',
                'message': f'Redis 内存使用较高 ({used_memory_mb:.2f}MB)，考虑清理不必要的缓存或增加内存',
            })
        
        # 检查内存碎片
        fragmentation = memory_info.get('mem_fragmentation_ratio', 0)
        if fragmentation > 1.5:
            suggestions.append({
                'level': 'info',
                'message': f'内存碎片率较高 ({fragmentation:.2f})，可以考虑重启 Redis 或使用 MEMORY PURGE',
            })
        
        # 检查 TTL 分布
        ttl_dist = key_analysis.get('ttl_distribution', {})
        no_expiry = ttl_dist.get('no_expiry', 0)
        if no_expiry > 100:
            suggestions.append({
                'level': 'info',
                'message': f'有 {no_expiry} 个键没有设置过期时间，可能导致内存泄漏',
            })
        
        return suggestions
    
    @classmethod
    def get_full_report(cls):
        """获取完整报告"""
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
        """预热所有缓存"""
        results = {}
        
        # 预热 SiteConfig
        try:
            from apps.core.models import SiteConfig
            SiteConfig.get_solo()
            results['site_config'] = 'warmed'
        except Exception as e:
            results['site_config'] = f'error: {e}'
        
        # 预热分类和标签
        try:
            from apps.blog.views import get_categories_and_tags
            get_categories_and_tags()
            results['categories_tags'] = 'warmed'
        except Exception as e:
            results['categories_tags'] = f'error: {e}'
        
        # 预热敏感词
        try:
            from moderation.utils import get_sensitive_words
            get_sensitive_words()
            results['sensitive_words'] = 'warmed'
        except Exception as e:
            results['sensitive_words'] = f'error: {e}'
        
        # 预热统计数据
        try:
            from apps.core.maintenance_tasks import generate_statistics
            generate_statistics()
            results['statistics'] = 'warmed'
        except Exception as e:
            results['statistics'] = f'error: {e}'
        
        return results


class CacheInvalidator:
    """缓存失效器"""
    
    # 缓存键映射
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
        """失效指定模型的缓存"""
        keys_to_delete = cls.KEY_MAPPING.get(model_name, [])
        
        for key in keys_to_delete:
            try:
                cache.delete(key)
                logger.info(f'缓存已失效: {key}')
            except Exception as e:
                logger.error(f'失效缓存 {key} 失败: {e}')
        
        return keys_to_delete
    
    @classmethod
    def invalidate_all(cls):
        """失效所有缓存"""
        try:
            from django_redis import get_redis_connection
            
            client = get_redis_connection('default')
            
            # 清空当前数据库
            client.flushdb()
            
            logger.warning('所有缓存已清空')
            return True
        except Exception as e:
            logger.error(f'清空缓存失败: {e}')
            return False


def get_redis_optimizer():
    """获取 Redis 优化器"""
    return RedisMemoryOptimizer()


def get_cache_report():
    """获取缓存报告"""
    return RedisMemoryOptimizer.get_full_report()
