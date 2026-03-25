from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, CustomLoginForm
from .captcha import generate_captcha


def register_view(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            # 指定认证后端
            from django.conf import settings
            backend = settings.AUTHENTICATION_BACKENDS[0]
            user.backend = backend
            login(request, user, backend=backend)
            return redirect('core:home')
        else:
            # 验证失败时，重新生成验证码
            captcha_code, captcha_image = generate_captcha()
            request.session['captcha_code'] = captcha_code
    else:
        # GET请求时生成验证码
        captcha_code, captcha_image = generate_captcha()
        request.session['captcha_code'] = captcha_code
        form = UserRegisterForm(request=request)
    return render(request, 'accounts/register.html', {'form': form, 'captcha_image': captcha_image})


@login_required
def profile_view(request):
    """个人中心视图"""
    # 获取用户的待审核内容
    from apps.blog.models import Comment
    from apps.forum.models import Topic, Reply
    
    pending_comments = Comment.objects.filter(
        user=request.user,
        review_status='pending'
    ).order_by('-created_at')
    
    pending_topics = Topic.objects.filter(
        author=request.user,
        review_status='pending'
    ).order_by('-created_at')
    
    pending_replies = Reply.objects.filter(
        author=request.user,
        review_status='pending'
    ).order_by('-created_at')
    
    # 获取用户的已拒绝内容
    rejected_comments = Comment.objects.filter(
        user=request.user,
        review_status='rejected'
    ).order_by('-created_at')
    
    rejected_topics = Topic.objects.filter(
        author=request.user,
        review_status='rejected'
    ).order_by('-created_at')
    
    rejected_replies = Reply.objects.filter(
        author=request.user,
        review_status='rejected'
    ).order_by('-created_at')
    
    context = {
        'pending_comments': pending_comments,
        'pending_topics': pending_topics,
        'pending_replies': pending_replies,
        'rejected_comments': rejected_comments,
        'rejected_topics': rejected_topics,
        'rejected_replies': rejected_replies,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    """编辑资料视图"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'accounts/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


def login_view(request):
    """用户登录视图"""
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('core:home')
        # 验证失败时，重新生成验证码
        captcha_code, captcha_image = generate_captcha()
        request.session['captcha_code'] = captcha_code
    else:
        # GET请求时生成验证码
        captcha_code, captcha_image = generate_captcha()
        request.session['captcha_code'] = captcha_code
        form = CustomLoginForm(request=request)
    return render(request, 'accounts/login.html', {'form': form, 'captcha_image': captcha_image})


def logout_view(request):
    """用户登出视图（仅允许 POST，避免 Django 5.0 弃用告警）。"""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    logout(request)
    return redirect('core:home')
