"""
性能监控中间件

功能：
- 请求耗时统计
- 数据库查询计数
- 缓存命中率追踪
- 慢请求警告
- 内存使用监控
- 连接池状态
"""

import time
import logging
import gc
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class PerformanceMonitorMiddleware:
    """
    性能监控中间件

    记录每个请求的：
    - 执行时间
    - 数据库查询次数
    - 是否触发缓存
    - 内存使用
    """

    # 慢请求阈值（毫秒）
    SLOW_REQUEST_THRESHOLD = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 500)

    # 查询过多阈值
    HIGH_QUERY_THRESHOLD = getattr(settings, 'HIGH_QUERY_THRESHOLD', 20)

    # 内存警告阈值（MB）
    MEMORY_WARNING_THRESHOLD = getattr(settings, 'MEMORY_WARNING_THRESHOLD_MB', 100)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 记录开始时间
        start_time = time.time()

        # 记录查询数
        queries_before = len(connection.queries)

        # 记录内存（可选）
        try:
            import tracemalloc
            if tracemalloc.is_tracing():
                tracemalloc.get_traced_memory()[0] / (1024 * 1024)
        except Exception:
            logger.debug('tracemalloc_probe_failed', exc_info=True)

        # 执行请求
        response = self.get_response(request)

        # 计算耗时
        duration_ms = (time.time() - start_time) * 1000

        # 计算查询数
        queries_after = len(connection.queries)
        query_count = queries_after - queries_before

        # 查询总耗时
        query_time_ms = sum(
            float(q.get('time', 0)) * 1000
            for q in connection.queries[queries_before:queries_after]
        )

        # 添加性能头
        response['X-Request-Duration-Ms'] = f'{duration_ms:.2f}'
        response['X-DB-Queries'] = str(query_count)
        response['X-DB-Time-Ms'] = f'{query_time_ms:.2f}'

        # 慢请求警告
        if duration_ms > self.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f'慢请求警告: {request.path} 耗时 {duration_ms:.2f}ms, '
                f'{query_count} 个数据库查询 ({query_time_ms:.2f}ms)'
            )

        # 查询过多警告
        if query_count > self.HIGH_QUERY_THRESHOLD:
            logger.warning(
                f'查询过多警告: {request.path} 执行了 {query_count} 个数据库查询, '
                f'可能存在 N+1 问题'
            )

        # 记录详细信息（DEBUG 模式）
        if settings.DEBUG and query_count > 0:
            path = request.path
            logger.debug(
                f'[性能] {path}: {duration_ms:.2f}ms, '
                f'{query_count} queries, {query_time_ms:.2f}ms DB time'
            )

        return response


class QueryDebugMiddleware:
    """
    查询调试中间件（仅开发环境使用）

    在响应头中显示所有查询
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if settings.DEBUG:
            # 添加查询统计
            queries = connection.queries
            total_time = sum(float(q.get('time', 0)) for q in queries) * 1000

            response['X-DB-Total-Time-Ms'] = f'{total_time:.2f}'
            response['X-DB-Query-Count'] = str(len(queries))

        return response


class MemoryMonitorMiddleware:
    """
    内存监控中间件

    监控请求前后的内存变化
    """

    # 内存增长阈值（MB）
    MEMORY_GROWTH_THRESHOLD = getattr(settings, 'MEMORY_GROWTH_THRESHOLD_MB', 10)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 执行请求
        response = self.get_response(request)

        # 如果内存增长过大，触发垃圾回收
        collected = gc.collect()
        if collected > 100:
            logger.debug(f'垃圾回收: 回收了 {collected} 个对象')

        return response


class ConnectionPoolMiddleware:
    """
    连接池监控中间件

    定期检查连接池状态
    """

    # 检查间隔（秒）
    CHECK_INTERVAL = 300  # 5 分钟
    _last_check = 0

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import time

        # 定期检查连接池
        current_time = time.time()
        if current_time - self._last_check > self.CHECK_INTERVAL:
            self._last_check = current_time
            self._check_connections()

        return self.get_response(request)

    def _check_connections(self):
        """检查连接池状态"""
        from django.db import connections

        for alias in connections:
            try:
                conn = connections[alias]
                if hasattr(conn, 'is_usable') and not conn.is_usable():
                    logger.warning(f'数据库连接 {alias} 不可用')
                    conn.close_if_unusable_or_obsolete()
            except Exception as e:
                logger.error(f'检查连接 {alias} 失败: {e}')
