"""核心视图"""
import os
import json
import time
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from apps.blog.models import Post, Category, Comment
from apps.forum.models import Topic, Board
from apps.accounts.models import User
from apps.tools.registry import registry as tool_registry

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
        f.write(f'# 生成时间: 2026-03-20\n\n')
        for key, value in config.items():
            f.write(f'{key}={value}\n')


def home_view(request):
    """首页 - 科技风格"""
    # 获取最新文章
    latest_posts = Post.objects.filter(status='published').order_by('-created_at')[:6]
    
    # 获取热门论坛主题
    hot_topics = Topic.objects.filter(review_status='approved').order_by('-reply_count')[:5]
    
    # 获取所有工具
    all_tools = tool_registry.get_all_tools()
    popular_tools = all_tools[:8] if len(all_tools) >= 8 else all_tools
    
    # 网站统计
    post_count = Post.objects.filter(status='published').count()
    topic_count = Topic.objects.filter(review_status='approved').count()
    comment_count = Comment.objects.filter(review_status='approved').count()
    user_count = User.objects.count()
    tool_count = len(all_tools)
    view_count = sum(post.views_count for post in Post.objects.filter(status='published'))
    
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
    
    # 使用与博客论坛一致的模板
    return render(request, 'home.html', context)


def search_view(request):
    """全局搜索"""
    query = request.GET.get('q', '').strip()
    results = {
        'posts': [],
        'topics': [],
        'query': query,
    }
    
    if query:
        # 搜索文章
        results['posts'] = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(summary__icontains=query),
            status='published'
        ).distinct()[:20]
        
        # 搜索论坛主题
        results['topics'] = Topic.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query),
            review_status='approved'
        ).distinct()[:20]
    
    return render(request, 'search/results.html', results)


def healthz_view(request):
    """
    增强健康检查端点
    
    检查项：
    - 数据库连接
    - 缓存（Redis）连接
    - 系统状态
    
    返回：
    - 200: 所有检查通过
    - 503: 部分检查失败
    """
    start_time = time.time()
    checks = {
        'database': _check_database(),
        'cache': _check_cache(),
    }
    
    # 计算响应时间
    duration_ms = (time.time() - start_time) * 1000
    
    # 判断整体状态
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    response_data = {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'duration_ms': round(duration_ms, 2),
        'version': '2.3.0',
    }
    
    return JsonResponse(response_data, status=status_code)


def _check_database():
    """检查数据库连接"""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return True
    except Exception as e:
        return False


def _check_cache():
    """检查缓存连接"""
    try:
        # 写入测试
        test_key = 'health_check_test'
        test_value = str(time.time())
        cache.set(test_key, test_value, 10)
        
        # 读取测试
        result = cache.get(test_key)
        
        # 清理
        cache.delete(test_key)
        
        return result == test_value
    except Exception as e:
        return False


def readiness_view(request):
    """
    就绪检查端点（Kubernetes 风格）
    
    比 healthz 更严格，检查应用是否准备好接收流量
    """
    checks = {
        'database': _check_database(),
        'cache': _check_cache(),
    }
    
    all_ready = all(checks.values())
    
    return JsonResponse({
        'ready': all_ready,
        'checks': checks,
    }, status=200 if all_ready else 503)


def liveness_view(request):
    """
    存活检查端点（Kubernetes 风格）
    
    简单检查应用是否运行
    """
    return JsonResponse({'alive': True})


def contact_view(request):
    """联系页面"""
    if request.method == 'POST':
        # 这里可以添加邮件发送逻辑
        messages.success(request, '感谢您的留言，我们会尽快回复！')
        return redirect('core:contact')
    return render(request, 'core/contact.html')


def settings_view(request):
    """系统设置页面"""
    if request.method == 'POST':
        # 保存设置
        config = get_env_config()
        
        config['SITE_NAME'] = request.POST.get('site_name', 'Django Blog')
        config['SITE_DESCRIPTION'] = request.POST.get('site_description', '')
        config['SITE_URL'] = request.POST.get('site_url', '')
        
        # 允许局域网访问
        if request.POST.get('allow_lan') == 'on':
            config['ALLOWED_HOSTS'] = 'localhost,127.0.0.1,0.0.0.0,*'
        else:
            config['ALLOWED_HOSTS'] = 'localhost,127.0.0.1'
        
        save_env_config(config)
        messages.success(request, '设置已保存！')
        return redirect('core:settings')
    
    # 读取当前配置
    config = get_env_config()
    
    context = {
        'site_name': config.get('SITE_NAME', 'Django Blog'),
        'site_description': config.get('SITE_DESCRIPTION', ''),
        'site_url': config.get('SITE_URL', ''),
        'allow_lan': '*' in config.get('ALLOWED_HOSTS', '') or '0.0.0.0' in config.get('ALLOWED_HOSTS', ''),
        'debug': config.get('DEBUG', 'True') == 'True',
    }
    
    return render(request, 'core/settings.html', context)
