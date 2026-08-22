"""
分布式任务锁工具

使用 Redis SET NX 实现分布式锁，防止 Celery 任务重复执行
"""

import logging
from contextlib import contextmanager
from django.core.cache import cache

logger = logging.getLogger(__name__)


@contextmanager
def task_lock(lock_name: str, timeout: int = 300, blocking: bool = False, blocking_timeout: int = 10):
    """
    分布式任务锁上下文管理器

    Args:
        lock_name: 锁名称（建议使用 "task:任务名" 格式）
        timeout: 锁过期时间（秒），默认 5 分钟
        blocking: 是否阻塞等待锁释放
        blocking_timeout: 阻塞等待超时时间（秒）

    Yields:
        bool: 是否成功获取锁

    Raises:
        RuntimeError: 非阻塞模式下无法获取锁
    """
    lock_key = f"task_lock:{lock_name}"
    acquired = cache.add(lock_key, "1", timeout)  # SET NX EX

    if not acquired and blocking:
        import time
        start = time.time()
        while time.time() - start < blocking_timeout:
            if cache.add(lock_key, "1", timeout):
                acquired = True
                break
            time.sleep(0.1)

    if not acquired:
        logger.info(f"任务锁获取失败: {lock_name} (另一个实例正在运行)")
        if not blocking:
            raise RuntimeError(f"无法获取任务锁: {lock_name}")
        yield False
        return

    try:
        yield True
    finally:
        if acquired:
            cache.delete(lock_key)


class TaskLock:
    """任务锁类（支持手动获取/释放）"""

    def __init__(self, lock_name: str, timeout: int = 300):
        self.lock_key = f"task_lock:{lock_name}"
        self.timeout = timeout
        self._acquired = False

    def acquire(self, blocking: bool = False, blocking_timeout: int = 10) -> bool:
        """尝试获取锁"""
        self._acquired = cache.add(self.lock_key, "1", self.timeout)

        if not self._acquired and blocking:
            import time
            start = time.time()
            while time.time() - start < blocking_timeout:
                if cache.add(self.lock_key, "1", self.timeout):
                    self._acquired = True
                    break
                time.sleep(0.1)

        return self._acquired

    def release(self):
        """释放锁"""
        if self._acquired:
            cache.delete(self.lock_key)
            self._acquired = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()