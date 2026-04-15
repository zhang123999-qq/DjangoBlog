"""核心视图"""
import logging
import os
import time
from django.shortcuts import render, redirect
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.db import connection
from django.db.utils import DatabaseError, OperationalError
from django.core.cache import cache
from apps.blog.models import Post, Comment
from apps.forum.models import Topic
from apps.accounts.models import User
from apps.tools.registry import registry as tool_registry

logger = logging.getLogger(__name__)

# 常量定义
SEARCH_QUERY_MAX_LENGTH = 100  # 搜索词最大长度
SEARCH_RESULT_LIMIT = 20       # 搜索结果最大数量
HOME_CACHE_TTL = 60            # 首页缓存时间（秒）
HEALTH_CHECK_CACHE_TTL = 10    # 健康检查缓存时间（秒）
ENV_CONFIG_DATE = '2026-03-20' # 环境配置生成日期
MS_CONVERSION_FACTOR = 1000    # 毫秒转换因子

# 首页显示数量常量
HOME_POSTS_COUNT = 6           # 首页显示文章数量
HOME_TOPICS_COUNT = 5          # 首页显示热门主题数量
HOME_TOOLS_COUNT = 8           # 首页显示工具数量

# 设置页面字段长度常量
SITE_NAME_MAX_LENGTH = 100     # 站点名称最大长度
SITE_DESC_MAX_LENGTH = 500     # 站点描述最大长度
SITE_URL_MAX_LENGTH = 200      # 站点URL最大长度

# .env 文件路径
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')


def get_env_config():
    """读取 .env 配置"""
    config = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config


def save_env_config(config):
    """保存 .env 配置"""
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write('# Django 配置\n')
        f.write(f'# 生成时间: {ENV_CONFIG_DATE}\n\n')
        for key, value in config.items():
            f.write(f'{key}={value}\n')


def home_view(request):
    """首页 - 科技风格（P0：缓存 + SQL 聚合优化）"""
    cache_key = 'core:home:v1'
    cached_context = cache.get(cache_key)
    if cached_context is not None:
        return render(request, 'home.html', cached_context)

    latest_posts = list(
        Post.objects.filter(status='published')
        .select_related('author', 'category')
        .only(
            'id', 'title', 'slug', 'summary', 'created_at', 'published_at',
            'views_count', 'author__username', 'author__nickname',
            'category__name', 'category__slug'
        )
        .order_by('-created_at')[:HOME_POSTS_COUNT]
    )

    hot_topics = list(
        Topic.objects.filter(review_status='approved')
        .select_related('board', 'author')
        .only(
            'id', 'title', 'reply_count', 'views_count', 'last_reply_at',
            'board__name', 'board__slug', 'author__username', 'author__nickname'
        )
        .order_by('-reply_count')[:HOME_TOPICS_COUNT]
    )

    all_tools = tool_registry.get_all_tools()
    popular_tools = all_tools[:HOME_TOOLS_COUNT] if len(all_tools) >= HOME_TOOLS_COUNT else all_tools

    published_posts = Post.objects.filter(status='published')
    post_count = published_posts.count()
    topic_count = Topic.objects.filter(review_status='approved').count()
    comment_count = Comment.objects.filter(review_status='approved').count()
    user_count = User.objects.count()
    tool_count = len(all_tools)
    view_count = published_posts.aggregate(total_views=Sum('views_count')).get('total_views') or 0

    context = {
        'latest_posts': latest_posts,
        'hot_topics': hot_topics,
        'popular_tools': popular_tools,
        'post_count': post_count,
        'topic_count': topic_count,
        'comment_count': comment_count,
        'user_count': user_count,
        'tool_count': tool_count,
        'view_count': view_count,
    }

    cache.set(cache_key, context, HOME_CACHE_TTL)
    return render(request, 'home.html', context)


def search_view(request):
    """全局搜索"""
    query = request.GET.get('q', '').strip()
    
    # 验证搜索词长度
    if len(query) > SEARCH_QUERY_MAX_LENGTH:
        query = query[:SEARCH_QUERY_MAX_LENGTH]
    
    # 清理搜索词（移除潜在的危险字符）
    query = _sanitize_search_query(query)
    
    results = {
        'posts': [],
        'topics': [],
        'query': query,
    }

    if query:
        results['posts'] = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(summary__icontains=query),
            status='published'
        ).distinct()[:SEARCH_RESULT_LIMIT]

        results['topics'] = Topic.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query),
            review_status='approved'
        ).distinct()[:SEARCH_RESULT_LIMIT]

    return render(request, 'search/results.html', results)


def _sanitize_search_query(query):
    """清理搜索查询，移除潜在的危险字符"""
    # 移除SQL注入相关字符
    dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'exec', 'execute', 'select', 'drop', 'delete', 'update', 'insert']
    sanitized = query
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # 移除XSS相关字符
    xss_chars = ['<', '>', 'script', 'javascript:', 'onload=', 'onerror=']
    for char in xss_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def healthz_view(request):
    """增强健康检查端点"""
    start_time = time.time()
    checks = {
        'database': _check_database(),
        'cache': _check_cache(),
    }

    duration_ms = (time.time() - start_time) * MS_CONVERSION_FACTOR
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    response_data = {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'duration_ms': round(duration_ms, 2),
        'version': '2.3.2',
    }

    return JsonResponse(response_data, status=status_code)


def _check_database():
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return True
    except (OperationalError, DatabaseError, OSError):
        logger.exception('health_check_database_failed')
        return False


def _check_cache():
    try:
        test_key = 'health_check_test'
        test_value = str(time.time())
        cache.set(test_key, test_value, HEALTH_CHECK_CACHE_TTL)
        result = cache.get(test_key)
        cache.delete(test_key)
        return result == test_value
    except (ConnectionError, TimeoutError, OSError, ValueError):
        logger.exception('health_check_cache_failed')
        return False


def readiness_view(request):
    checks = {
        'database': _check_database(),
        'cache': _check_cache(),
    }
    all_ready = all(checks.values())

    return JsonResponse({'ready': all_ready, 'checks': checks}, status=200 if all_ready else 503)


def liveness_view(request):
    return JsonResponse({'alive': True})


def contact_view(request):
    if request.method == 'POST':
        messages.success(request, '感谢您的留言，我们会尽快回复！')
        return redirect('core:contact')
    return render(request, 'core/contact.html')


@login_required
@user_passes_test(lambda u: u.is_staff)
def settings_view(request):
    """系统设置页面（仅管理员，生产环境禁用）"""
    if not settings.DEBUG:
        return HttpResponseForbidden('生产环境已禁用在线设置页面')

    if request.method == 'POST':
        config = get_env_config()
        
        # 验证和清理站点名称
        site_name = request.POST.get('site_name', 'Django Blog').strip()
        if len(site_name) > SITE_NAME_MAX_LENGTH:
            site_name = site_name[:SITE_NAME_MAX_LENGTH]
        config['SITE_NAME'] = site_name
        
        # 验证和清理站点描述
        site_description = request.POST.get('site_description', '').strip()
        if len(site_description) > SITE_DESC_MAX_LENGTH:
            site_description = site_description[:SITE_DESC_MAX_LENGTH]
        config['SITE_DESCRIPTION'] = site_description
        
        # 验证和清理站点URL
        site_url = request.POST.get('site_url', '').strip()
        if len(site_url) > SITE_URL_MAX_LENGTH:
            site_url = site_url[:SITE_URL_MAX_LENGTH]
        # 验证URL格式
        if site_url and not site_url.startswith(('http://', 'https://')):
            site_url = 'https://' + site_url
        config['SITE_URL'] = site_url

        # 验证LAN设置
        allow_lan = request.POST.get('allow_lan') == 'on'
        if allow_lan:
            config['ALLOWED_HOSTS'] = 'localhost,127.0.0.1,0.0.0.0,*'
        else:
            config['ALLOWED_HOSTS'] = 'localhost,127.0.0.1'

        save_env_config(config)
        messages.success(request, '设置已保存！')
        return redirect('core:settings')

    config = get_env_config()
    context = {
        'site_name': config.get('SITE_NAME', 'Django Blog'),
        'site_description': config.get('SITE_DESCRIPTION', ''),
        'site_url': config.get('SITE_URL', ''),
        'allow_lan': '*' in config.get('ALLOWED_HOSTS', ''),
        'debug': config.get('DEBUG', 'True') == 'True',
    }

    return render(request, 'core/settings.html', context)
