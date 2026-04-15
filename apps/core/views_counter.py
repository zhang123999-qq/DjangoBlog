"""
浏览量计数服务

优化策略：
1. 本地内存缓冲：减少 Redis 写入频率
2. 批量聚合：定时批量写入，减少数据库压力
3. 防刷机制：同一 IP/用户短时间内只计一次
4. 降级保护：Redis 不可用时自动降级

使用方法：
    from apps.core.views_counter import ViewsCounter

    # 记录浏览量
    ViewsCounter.increment('post', post_id, request)

    # 获取浏览量
    views = ViewsCounter.get_views('post', post_id)
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Dict, Optional, Set

from django.core.cache import cache
from django.db.models import F
from django.http import HttpRequest
from django.conf import settings

logger = logging.getLogger(__name__)


class ViewsBuffer:
    """
    本地内存缓冲区

    收集浏览量记录，定时批量写入 Redis
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化缓冲区"""
        # 缓冲区：{model_type: {object_id: count}}
        self._buffer: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        # 缓冲区锁
        self._buffer_lock = threading.Lock()
        # 缓冲区大小限制
        self._max_size = getattr(settings, "VIEWS_BUFFER_MAX_SIZE", 10000)
        # 最后刷新时间
        self._last_flush = time.time()
        # 刷新间隔（秒）
        self._flush_interval = getattr(settings, "VIEWS_FLUSH_INTERVAL", 10)
        # 已记录的请求（防刷）: {model_type: {object_id: set(ip_or_user_id)}}
        self._recorded: Dict[str, Dict[int, Set[str]]] = defaultdict(lambda: defaultdict(set))
        # 防刷过期时间（秒）
        self._anti_spam_ttl = getattr(settings, "VIEWS_ANTI_SPAM_TTL", 300)  # 5分钟
        # 防刷记录时间戳
        self._recorded_timestamp: Dict[str, Dict[int, float]] = defaultdict(dict)

    def add(self, model_type: str, object_id: int, identifier: str) -> bool:
        """
        添加浏览记录

        Args:
            model_type: 模型类型（如 'post', 'topic'）
            object_id: 对象 ID
            identifier: 唯一标识（IP 或用户 ID）

        Returns:
            bool: 是否成功添加（False 表示重复记录）
        """
        # 检查是否已记录（防刷）
        if self._is_recorded(model_type, object_id, identifier):
            return False

        with self._buffer_lock:
            # 记录到缓冲区
            self._buffer[model_type][object_id] += 1
            # 标记为已记录
            self._recorded[model_type][object_id].add(identifier)
            self._recorded_timestamp[model_type][object_id] = time.time()

            # 检查是否需要刷新
            if self._should_flush():
                self._flush_to_redis()

        return True

    def _is_recorded(self, model_type: str, object_id: int, identifier: str) -> bool:
        """检查是否已记录"""
        # 清理过期的防刷记录
        self._cleanup_recorded(model_type, object_id)

        return identifier in self._recorded[model_type][object_id]

    def _cleanup_recorded(self, model_type: str, object_id: int):
        """清理过期的防刷记录"""
        timestamp = self._recorded_timestamp[model_type].get(object_id, 0)
        if time.time() - timestamp > self._anti_spam_ttl:
            self._recorded[model_type][object_id].clear()
            self._recorded_timestamp[model_type].pop(object_id, None)

    def _should_flush(self) -> bool:
        """检查是否应该刷新"""
        # 按大小
        total_size = sum(len(items) for items in self._buffer.values())
        if total_size >= self._max_size:
            return True

        # 按时间
        if time.time() - self._last_flush >= self._flush_interval:
            return True

        return False

    def _flush_to_redis(self):
        """刷新到 Redis"""
        if not self._buffer:
            return

        try:
            for model_type, items in self._buffer.items():
                for object_id, count in items.items():
                    cache_key = f"views:{model_type}:{object_id}"
                    try:
                        # 原子递增
                        if hasattr(cache, "incr"):
                            try:
                                cache.incr(cache_key, count)
                            except ValueError:
                                cache.set(cache_key, count, 3600)
                        else:
                            # 不支持 incr，直接设置
                            current = cache.get(cache_key, 0)
                            cache.set(cache_key, current + count, 3600)
                    except Exception as e:
                        logger.warning(f"Redis 写入失败: {e}")

            # 清空缓冲区
            self._buffer.clear()
            self._last_flush = time.time()

        except Exception as e:
            logger.error(f"刷新浏览量到 Redis 失败: {e}")

    def force_flush(self):
        """强制刷新"""
        with self._buffer_lock:
            self._flush_to_redis()

    def get_buffer_stats(self) -> Dict:
        """获取缓冲区统计"""
        with self._buffer_lock:
            return {
                "total_items": sum(len(items) for items in self._buffer.values()),
                "model_types": {k: len(v) for k, v in self._buffer.items()},
                "last_flush": self._last_flush,
            }


class ViewsCounter:
    """
    浏览量计数器

    统一的浏览量记录和查询接口
    """

    # Redis key 前缀
    KEY_PREFIX = "views"
    # 支持的模型类型
    MODEL_MAPPING = {
        "post": "blog.Post",
        "topic": "forum.Topic",
    }

    _buffer = ViewsBuffer()

    @classmethod
    def increment(
        cls, model_type: str, object_id: int, request: Optional[HttpRequest] = None, identifier: Optional[str] = None
    ) -> bool:
        """
        记录浏览量

        Args:
            model_type: 模型类型（'post', 'topic'）
            object_id: 对象 ID
            request: HTTP 请求对象（用于提取标识）
            identifier: 自定义标识（优先级高于 request）

        Returns:
            bool: 是否成功记录
        """
        if model_type not in cls.MODEL_MAPPING:
            logger.warning(f"不支持的模型类型: {model_type}")
            return False

        # 获取唯一标识
        if identifier is None:
            identifier = cls._get_identifier(request)

        # 添加到缓冲区
        return cls._buffer.add(model_type, object_id, identifier)

    @classmethod
    def _get_identifier(cls, request: Optional[HttpRequest]) -> str:
        """获取唯一标识（用于防刷）"""
        if request is None:
            return f"anon_{time.time()}"

        # 优先使用用户 ID
        if request.user.is_authenticated:
            return f"user_{request.user.id}"

        # 使用 IP + User-Agent
        ip = cls._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:50]
        return f"ip_{ip}_{hash(user_agent) % 10000}"

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """获取客户端 IP"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip

        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    @classmethod
    def get_views(cls, model_type: str, object_id: int, include_buffer: bool = True) -> int:
        """
        获取浏览量

        Args:
            model_type: 模型类型
            object_id: 对象 ID
            include_buffer: 是否包含缓冲区中的计数

        Returns:
            int: 浏览量
        """
        # 从 Redis 获取
        cache_key = f"{cls.KEY_PREFIX}:{model_type}:{object_id}"
        views = cache.get(cache_key, 0)

        # 从数据库获取基础值
        db_views = cls._get_db_views(model_type, object_id)

        # 加上缓冲区中的值
        if include_buffer:
            buffer_views = cls._buffer._buffer.get(model_type, {}).get(object_id, 0)
        else:
            buffer_views = 0

        return db_views + views + buffer_views

    @classmethod
    def _get_db_views(cls, model_type: str, object_id: int) -> int:
        """从数据库获取浏览量"""
        try:
            model_path = cls.MODEL_MAPPING.get(model_type)
            if not model_path:
                return 0

            # 动态导入模型
            from django.apps import apps

            model = apps.get_model(model_path)

            instance = model.objects.filter(pk=object_id).first()
            if instance:
                return getattr(instance, "views_count", 0)

        except Exception as e:
            logger.warning(f"获取数据库浏览量失败: {e}")

        return 0

    @classmethod
    def sync_to_db(cls, model_type: Optional[str] = None) -> Dict:
        """
        同步浏览量到数据库

        Args:
            model_type: 指定模型类型（None 表示全部）

        Returns:
            Dict: 同步结果
        """
        result = {"synced": 0, "errors": 0}

        # 先刷新缓冲区
        cls._buffer.force_flush()

        # 获取所有需要同步的 key
        try:
            if hasattr(cache, "iter_keys"):
                keys = list(cache.iter_keys(f"{cls.KEY_PREFIX}:*"))
            else:
                keys = []
                # 尝试从已知 ID 列表获取
                for mt in cls.MODEL_MAPPING.keys():
                    if model_type and mt != model_type:
                        continue
                    # 这里需要根据实际情况获取 ID 列表
                    # 暂时跳过

            for key in keys:
                try:
                    key_str = key.decode() if isinstance(key, bytes) else str(key)
                    parts = key_str.split(":")

                    if len(parts) != 3:
                        continue

                    _, mt, obj_id = parts
                    obj_id = int(obj_id)

                    if model_type and mt != model_type:
                        continue

                    views = cache.get(key_str, 0)
                    if not views:
                        continue

                    # 更新数据库
                    if cls._update_db_views(mt, obj_id, views):
                        cache.delete(key_str)
                        result["synced"] += 1
                    else:
                        result["errors"] += 1

                except Exception as e:
                    logger.error(f"同步 {key} 失败: {e}")
                    result["errors"] += 1

        except Exception as e:
            logger.error(f"同步浏览量到数据库失败: {e}")
            result["error"] = str(e)

        return result

    @classmethod
    def _update_db_views(cls, model_type: str, object_id: int, views: int) -> bool:
        """更新数据库浏览量"""
        try:
            model_path = cls.MODEL_MAPPING.get(model_type)
            if not model_path:
                return False

            from django.apps import apps

            model = apps.get_model(model_path)

            model.objects.filter(pk=object_id).update(views_count=F("views_count") + views)
            return True

        except Exception as e:
            logger.error(f"更新数据库浏览量失败: {e}")
            return False


# 定时刷新任务
def start_background_flusher():
    """启动后台刷新线程"""
    import threading

    def flusher():
        while True:
            time.sleep(10)  # 每 10 秒刷新一次
            try:
                ViewsCounter._buffer.force_flush()
            except Exception as e:
                logger.error(f"后台刷新失败: {e}")

    thread = threading.Thread(target=flusher, daemon=True)
    thread.start()

    return thread
