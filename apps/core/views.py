"""核心视图"""
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from apps.blog.models import Post, Category, Comment
from apps.forum.models import Topic, Board
from apps.accounts.models import User
from apps.tools.registry import registry as tool_registry


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
    
    # 使用科技风格模板
    return render(request, 'home_tech.html', context)


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
    """健康检查"""
    return JsonResponse({'status': 'ok'})


def contact_view(request):
    """联系页面"""
    if request.method == 'POST':
        # 这里可以添加邮件发送逻辑
        messages.success(request, '感谢您的留言，我们会尽快回复！')
        return redirect('core:contact')
    return render(request, 'core/contact.html')
