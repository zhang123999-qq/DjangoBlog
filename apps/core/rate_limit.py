"""
速率限制工具

功能：
- 基于缓存的速率限制
- 支持多种限制策略
"""

import time
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings


def rate_limit(key_prefix, rate='10/m', method='POST'):
    """
    速率限制装饰器
    
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
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 只对指定方法限制
            if request.method != method:
                return view_func(request, *args, **kwargs)
            
            # 解析速率
            try:
                count, period = rate.split('/')
                count = int(count)
                
                # 计算时间窗口（秒）
                if period == 's':
                    window = 1
                elif period == 'm':
                    window = 60
                elif period == 'h':
                    window = 3600
                elif period == 'd':
                    window = 86400
                else:
                    window = 60  # 默认 1 分钟
                    
            except (ValueError, TypeError):
                count = 10
                window = 60
            
            # 生成缓存 key
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            user_id = request.user.id if request.user.is_authenticated else None
            
            if user_id:
                cache_key = f'ratelimit:{key_prefix}:user:{user_id}'
            else:
                cache_key = f'ratelimit:{key_prefix}:ip:{ip}'
            
            # 检查计数
            current = cache.get(cache_key, 0)
            
            if current >= count:
                # 超出限制
                return JsonResponse({
                    'error': '请求过于频繁，请稍后再试',
                    'retry_after': window
                }, status=429)
            
            # 递增计数
            if current == 0:
                cache.set(cache_key, 1, window)
            else:
                cache.incr(cache_key)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_by_user(key_prefix, rate='10/m', method='POST'):
    """
    基于用户的速率限制（仅对登录用户）
    
    用法:
        @rate_limit_by_user('post', rate='5/h')
        def post_create_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method != method:
                return view_func(request, *args, **kwargs)
            
            # 未登录用户不限制（由其他装饰器处理）
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            try:
                count, period = rate.split('/')
                count = int(count)
                
                if period == 's':
                    window = 1
                elif period == 'm':
                    window = 60
                elif period == 'h':
                    window = 3600
                elif period == 'd':
                    window = 86400
                else:
                    window = 60
                    
            except (ValueError, TypeError):
                count = 10
                window = 60
            
            cache_key = f'ratelimit:{key_prefix}:user:{request.user.id}'
            
            current = cache.get(cache_key, 0)
            
            if current >= count:
                return JsonResponse({
                    'error': '操作过于频繁，请稍后再试',
                    'retry_after': window
                }, status=429)
            
            if current == 0:
                cache.set(cache_key, 1, window)
            else:
                cache.incr(cache_key)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def get_rate_limit_status(key_prefix, identifier):
    """
    获取速率限制状态
    
    返回:
        {
            'current': 当前计数,
            'limit': 限制数,
            'reset_at': 重置时间戳
        }
    """
    cache_key = f'ratelimit:{key_prefix}:{identifier}'
    current = cache.get(cache_key, 0)
    ttl = cache.ttl(cache_key) if hasattr(cache, 'ttl') else 60
    
    return {
        'current': current,
        'reset_in': ttl
    }
