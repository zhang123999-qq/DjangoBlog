"""
连接池监控和回收机制

功能：
- 数据库连接池监控
- Redis 连接池监控
- 连接健康检查
- 自动回收机制
"""

import time
import logging
import threading
from django.db import connections
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class ConnectionPoolMonitor:
    """连接池监控器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._last_check = 0
            self._check_interval = 60  # 60秒检查一次
    
    def check_database_connections(self):
        """检查数据库连接状态"""
        status = {}
        
        for alias in connections:
            conn = connections[alias]
            
            try:
                # 测试连接是否可用
                is_usable = conn.is_usable() if hasattr(conn, 'is_usable') else True
                
                # 获取连接信息
                conn_info = {
                    'alias': alias,
                    'engine': conn.settings_dict.get('ENGINE', 'unknown'),
                    'is_usable': is_usable,
                }
                
                # MySQL 连接池信息
                if hasattr(conn, 'connection') and conn.connection:
                    if hasattr(conn.connection, 'open'):
                        conn_info['is_open'] = conn.connection.open
                    
                    # 连接存活时间
                    if hasattr(conn, 'connection') and hasattr(conn.connection, 'connect_time'):
                        conn_info['connect_time'] = conn.connection.connect_time
                
                status[alias] = conn_info
                
                # 如果连接不可用，尝试重新建立
                if not is_usable:
                    logger.warning(f'数据库连接 {alias} 不可用，尝试重连...')
                    conn.close_if_unusable_or_obsolete()
                    
            except Exception as e:
                logger.error(f'检查数据库连接 {alias} 失败: {e}')
                status[alias] = {'error': str(e)}
        
        return status
    
    def check_redis_connection(self):
        """检查 Redis 连接状态"""
        status = {}
        
        try:
            from django_redis import get_redis_connection
            
            client = get_redis_connection('default')
            
            # 执行 PING 测试
            ping_result = client.ping()
            
            # 获取连接池信息
            pool = client.connection_pool
            
            status = {
                'ping': ping_result,
                'pool_max_connections': pool.max_connections if pool else 'N/A',
                'pool_created_connections': len(pool._created_connections) if pool and hasattr(pool, '_created_connections') else 'N/A',
            }
            
            # 获取 Redis 统计信息
            info = client.info()
            status.update({
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'N/A'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
            })
            
            # 计算命中率
            hits = status['keyspace_hits']
            misses = status['keyspace_misses']
            total = hits + misses
            status['hit_rate'] = f'{(hits / total * 100):.2f}%' if total > 0 else 'N/A'
            
        except Exception as e:
            logger.error(f'检查 Redis 连接失败: {e}')
            status = {'error': str(e)}
        
        return status
    
    def recycle_stale_connections(self):
        """回收过期连接"""
        recycled = {'database': 0, 'redis': 0}
        
        # 回收数据库连接
        for alias in connections:
            try:
                conn = connections[alias]
                
                # Django 4.1+ 的连接健康检查
                if hasattr(conn, 'close_if_unusable_or_obsolete'):
                    old_conn = conn.connection
                    conn.close_if_unusable_or_obsolete()
                    if conn.connection != old_conn:
                        recycled['database'] += 1
                        
            except Exception as e:
                logger.error(f'回收数据库连接 {alias} 失败: {e}')
        
        # Redis 连接池会自动管理，无需手动回收
        
        if recycled['database'] > 0:
            logger.info(f'回收了 {recycled["database"]} 个数据库连接')
        
        return recycled
    
    def get_pool_status(self):
        """获取连接池状态报告"""
        return {
            'database': self.check_database_connections(),
            'redis': self.check_redis_connection(),
            'timestamp': time.time(),
        }


class ConnectionHealthChecker:
    """连接健康检查器"""
    
    @staticmethod
    def ping_database():
        """Ping 数据库"""
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute('SELECT 1')
            return True
        except Exception as e:
            logger.error(f'数据库 Ping 失败: {e}')
            return False
    
    @staticmethod
    def ping_redis():
        """Ping Redis"""
        try:
            result = cache.get(':1:healthcheck', None)
            cache.set(':1:healthcheck', int(time.time()), 10)
            return True
        except Exception as e:
            logger.error(f'Redis Ping 失败: {e}')
            return False
    
    @classmethod
    def health_check(cls):
        """健康检查"""
        return {
            'database': cls.ping_database(),
            'redis': cls.ping_redis(),
            'status': 'healthy' if (cls.ping_database() and cls.ping_redis()) else 'unhealthy',
        }


def get_connection_monitor():
    """获取连接监控器实例"""
    return ConnectionPoolMonitor()


def get_health_status():
    """获取健康状态"""
    return ConnectionHealthChecker.health_check()
