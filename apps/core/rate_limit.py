"""
速率限制工具

功能：
- 基于 Redis Lua 脚本的原子速率限制（修复竞态条件）
- 支持多种限制策略
- 向后兼容原 API

v2.1 - 使用 Lua 脚本保证 check+increment 原子性，消除并发竞态条件
"""

from functools import wraps
import logging

from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Lua 脚本：原子性地检查并递增计数器
# 返回值：当前计数（递增后）
# 如果 key 不存在则初始化为 1 并设置过期时间
RATE_LIMIT_LUA_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = tonumber(redis.call('GET', key) or "0")

if current >= limit then
    -- 已达上限，不递增，返回当前值 + TTL
    local ttl = redis.call('TTL', key)
    if ttl < 0 then ttl = window end
    return {current, ttl}
end

-- 递增计数
if current == 0 then
    redis.call('SET', key, 1, 'EX', window)
else
    redis.call('INCR', key)
end

local new_count = current + 1
local ttl = redis.call('TTL', key)
if ttl < 0 then ttl = window end
return {new_count, ttl}
"""

# 缓存编译后的 Lua 脚本 SHA1 hash
_rate_limit_script_sha = None


def _execute_rate_limit_script(cache_key, limit, window):
    """
    通过 Redis Lua 脚本原子执行速率限制检查+递增。
    支持普通 cache 后端（降级）和 Redis 后端（Lua 脚本）。

    Returns:
        tuple: (current_count, ttl_seconds, is_limited)
    """
    global _rate_limit_script_sha

    try:
        # 尝试获取底层 Redis 客户端
        client = None
        if hasattr(cache, 'client'):
            client = cache.client
        elif hasattr(cache, 'get_client'):
            client = cache.get_client()
        elif hasattr(cache, '_client'):
            client = cache._client

        if client is None:
            raise ValueError("无法获取 Redis 客户端")

        # 确保 key 是字符串
        if isinstance(cache_key, bytes):
            cache_key = cache_key.decode()

        # 使用 EVALSHA 执行（已缓存 SHA1）
        if _rate_limit_script_sha is not None:
            try:
                result = client.evalsha(
                    _rate_limit_script_sha, 1, cache_key, str(limit), str(window)
                )
                return int(result[0]), int(result[1]), int(result[0]) >= limit
            except Exception:
                # SHA1 可能失效（Redis 重启/flush），重新 EVAL
                _rate_limit_script_sha = None

        if _rate_limit_script_sha is None:
            # EVAL 执行并缓存 SHA1
            result = client.eval(
                RATE_LIMIT_LUA_SCRIPT, 1, cache_key, str(limit), str(window)
            )
            try:
                _rate_limit_script_sha = client.script_load(RATE_LIMIT_LUA_SCRIPT)
            except Exception:
                pass  # SHA1 缓存失败不影响功能

            return int(result[0]), int(result[1]), int(result[0]) >= limit

    except Exception as e:
        # 降级方案：使用 Django cache 的 get/set（非原子，但不会崩溃）
        logger.warning("Lua 速率限制脚本执行失败，降级到 get/set 模式: %s", e)
        return _fallback_rate_limit(cache_key, limit, window)


def _fallback_rate_limit(cache_key, limit, window):
    """降级方案：使用 Django cache（非原子，但向后兼容）"""
    current = cache.get(cache_key, 0)
    if current >= limit:
        ttl = cache.ttl(cache_key) if hasattr(cache, 'ttl') else window
        return current, ttl, True
    if current == 0:
        cache.set(cache_key, 1, window)
    else:
        try:
            cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, window)
    return current + 1, window, False


def _parse_rate(rate):
    """解析速率字符串，返回 (count, window_seconds)"""
    try:
        count, period = rate.split('/')
        count = int(count)
        period_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        window = period_map.get(period.lower(), 60)
    except (ValueError, TypeError):
        logger.warning("无效的速率格式: %s，使用默认值 10/m", rate)
        count = 10
        window = 60
    return count, window


def rate_limit(key_prefix, rate='10/m', method='POST'):
    """
    速率限制装饰器（使用原子 Lua 脚本）

    用法:
        @rate_limit('comment', rate='5/m')
        def comment_create_view(request):
            ...

    参数:
        key_prefix: 缓存 key 前缀
        rate: 限制格式，如 '10/m'（10次/分钟）, '100/h'（100次/小时）
        method: 限制的 HTTP 方法，默认 POST

    返回:
        被限制时返回 429 JsonResponse
    """
    limit, window = _parse_rate(rate)

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 只对指定方法限制
            if request.method != method:
                return view_func(request, *args, **kwargs)

            # 生成缓存 key
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None

            if user_id:
                cache_key = f'ratelimit:{key_prefix}:user:{user_id}'
            else:
                cache_key = f'ratelimit:{key_prefix}:ip:{ip}'

            # 原子执行速率限制检查
            current, ttl, is_limited = _execute_rate_limit_script(cache_key, limit, window)

            if is_limited:
                return JsonResponse({
                    'error': '请求过于频繁，请稍后再试',
                    'retry_after': ttl,
                    'limit': limit,
                    'window': f'{window}s',
                }, status=429, headers={'Retry-After': str(ttl)})

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def rate_limit_by_user(key_prefix, rate='10/m', method='POST'):
    """
    基于用户的速率限制（仅对登录用户，使用原子 Lua 脚本）

    用法:
        @rate_limit_by_user('post', rate='5/h')
        def post_create_view(request):
            ...
    """
    limit, window = _parse_rate(rate)

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method != method:
                return view_func(request, *args, **kwargs)

            # 未登录用户不限制
            if not (hasattr(request, 'user') and request.user.is_authenticated):
                return view_func(request, *args, **kwargs)

            cache_key = f'ratelimit:{key_prefix}:user:{request.user.id}'

            # 原子执行速率限制检查
            current, ttl, is_limited = _execute_rate_limit_script(cache_key, limit, window)

            if is_limited:
                return JsonResponse({
                    'error': '操作过于频繁，请稍后再试',
                    'retry_after': ttl,
                    'limit': limit,
                    'window': f'{window}s',
                }, status=429, headers={'Retry-After': str(ttl)})

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def get_rate_limit_status(key_prefix, identifier, limit=10, window=60):
    """
    获取速率限制状态

    返回:
        {
            'current': 当前计数,
            'limit': 限制数,
            'ttl': 剩余重置时间,
            'is_limited': 是否已达上限,
        }
    """
    cache_key = f'ratelimit:{key_prefix}:{identifier}'
    current = cache.get(cache_key, 0)
    ttl = cache.ttl(cache_key) if hasattr(cache, 'ttl') else window

    return {
        'current': current,
        'limit': limit,
        'ttl': ttl if ttl > 0 else window,
        'is_limited': current >= limit,
    }
