from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from apps.blog.models import Comment
from apps.forum.models import Topic, Reply
from .services import approve_instance, reject_instance


def is_moderator(user):
    """检查用户是否为管理员"""
    return user.is_staff or user.is_superuser


@user_passes_test(is_moderator, login_url='accounts:login')
def moderation_dashboard(request):
    """审核中心仪表板"""
    # 获取待审核的内容
    pending_comments = Comment.objects.filter(review_status='pending')
    pending_topics = Topic.objects.filter(review_status='pending')
    pending_replies = Reply.objects.filter(review_status='pending')
    
    context = {
        'pending_comments': pending_comments,
        'pending_topics': pending_topics,
        'pending_replies': pending_replies,
    }
    
    return render(request, 'moderation/dashboard.html', context)


@user_passes_test(is_moderator, login_url='accounts:login')
def approve_content(request, content_type, content_id):
    """通过审核"""
    content = get_object_or_404(get_content_model(content_type), id=content_id)
    
    # 使用统一的审核服务
    approve_instance(content, request.user, note="")
    
    messages.success(request, '内容已通过审核')
    return redirect('moderation:dashboard')


@user_passes_test(is_moderator, login_url='accounts:login')
def reject_content(request, content_type, content_id):
    """拒绝审核"""
    content = get_object_or_404(get_content_model(content_type), id=content_id)
    
    if request.method == 'POST':
        review_note = request.POST.get('review_note', '')
        
        # 使用统一的审核服务
        reject_instance(content, request.user, note=review_note)
        
        messages.success(request, '内容已拒绝')
        return redirect('moderation:dashboard')
    
    context = {
        'content': content,
        'content_type': content_type,
    }
    
    return render(request, 'moderation/reject.html', context)


def get_content_model(content_type):
    """根据内容类型获取对应的模型"""
    if content_type == 'comment':
        return Comment
    elif content_type == 'topic':
        return Topic
    elif content_type == 'reply':
        return Reply
    else:
        raise ValueError('Invalid content type')
