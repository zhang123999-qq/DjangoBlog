import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, CustomLoginForm
from .captcha import generate_captcha, store_captcha

logger = logging.getLogger(__name__)


def register_view(request):
    """用户注册视图"""
    try:
        if request.method == "POST":
            form = UserRegisterForm(request.POST, request=request)
            if form.is_valid():
                user = form.save()
                # 指定认证后端
                from django.conf import settings

                backend = settings.AUTHENTICATION_BACKENDS[0]
                user.backend = backend
                login(request, user, backend=backend)
                messages.success(request, "注册成功！")
                return redirect("core:home")
            else:
                # 验证失败时，重新生成验证码
                captcha_code, captcha_image = generate_captcha()
                store_captcha(request, captcha_code)
        else:
            # GET请求时生成验证码
            captcha_code, captcha_image = generate_captcha()
            store_captcha(request, captcha_code)
            form = UserRegisterForm(request=request)
        return render(request, "accounts/register.html", {"form": form, "captcha_image": captcha_image})
    except Exception as e:
        logger.error(f"用户注册失败: {e}", exc_info=True)
        messages.error(request, "注册失败，请稍后重试")
        return render(
            request,
            "accounts/register.html",
            {"form": UserRegisterForm(request=request), "captcha_image": generate_captcha()[1]},
        )


@login_required
def profile_view(request):
    """个人中心视图"""
    # 获取用户的待审核内容
    from apps.blog.models import Comment
    from apps.forum.models import Topic, Reply

    pending_comments = Comment.objects.filter(user=request.user, review_status="pending").order_by("-created_at")

    pending_topics = Topic.objects.filter(author=request.user, review_status="pending").order_by("-created_at")

    pending_replies = Reply.objects.filter(author=request.user, review_status="pending").order_by("-created_at")

    # 获取用户的已拒绝内容
    rejected_comments = Comment.objects.filter(user=request.user, review_status="rejected").order_by("-created_at")

    rejected_topics = Topic.objects.filter(author=request.user, review_status="rejected").order_by("-created_at")

    rejected_replies = Reply.objects.filter(author=request.user, review_status="rejected").order_by("-created_at")

    context = {
        "pending_comments": pending_comments,
        "pending_topics": pending_topics,
        "pending_replies": pending_replies,
        "rejected_comments": rejected_comments,
        "rejected_topics": rejected_topics,
        "rejected_replies": rejected_replies,
    }

    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit_view(request):
    """编辑资料视图"""
    try:
        if request.method == "POST":
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, "资料更新成功！")
                return redirect("accounts:profile")
        else:
            user_form = UserUpdateForm(instance=request.user)
            profile_form = ProfileUpdateForm(instance=request.user.profile)
        return render(request, "accounts/profile_edit.html", {"user_form": user_form, "profile_form": profile_form})
    except Exception as e:
        logger.error(f"资料编辑失败: {e}", exc_info=True)
        messages.error(request, "资料更新失败，请稍后重试")
        return redirect("accounts:profile")


def login_view(request):
    """用户登录视图"""
    try:
        if request.method == "POST":
            form = CustomLoginForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get("username")
                password = form.cleaned_data.get("password")
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, "登录成功！")
                    return redirect("core:home")
            else:
                # 验证失败时，记录登录失败尝试（复用验证码的防暴力机制）
                from .captcha import record_failed_attempt

                record_failed_attempt(request)

            # 验证失败时，重新生成验证码
            captcha_code, captcha_image = generate_captcha()
            store_captcha(request, captcha_code)
        else:
            # 检查是否被锁定
            from .captcha import is_locked_out

            if is_locked_out(request):
                form = CustomLoginForm(request=request)
                captcha_code, captcha_image = generate_captcha()
                store_captcha(request, captcha_code)
                # 添加锁定提示
                form.add_error(None, "登录尝试次数过多，请 5 分钟后再试")
                return render(request, "accounts/login.html", {"form": form, "captcha_image": captcha_image})

            # GET请求时生成验证码
            captcha_code, captcha_image = generate_captcha()
            store_captcha(request, captcha_code)
            form = CustomLoginForm(request=request)
        return render(request, "accounts/login.html", {"form": form, "captcha_image": captcha_image})
    except Exception as e:
        logger.error(f"用户登录失败: {e}", exc_info=True)
        messages.error(request, "登录失败，请稍后重试")
        captcha_code, captcha_image = generate_captcha()
        store_captcha(request, captcha_code)
        return render(
            request, "accounts/login.html", {"form": CustomLoginForm(request=request), "captcha_image": captcha_image}
        )


def logout_view(request):
    """用户登出视图（仅允许 POST，避免 Django 5.0 弃用告警）。"""
    try:
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        logout(request)
        messages.success(request, "已成功登出")
        return redirect("core:home")
    except Exception as e:
        logger.error(f"用户登出失败: {e}", exc_info=True)
        messages.error(request, "登出失败，请稍后重试")
        return redirect("core:home")


@require_GET
def captcha_refresh(request):
    """AJAX 刷新验证码

    返回 JSON 格式:
    {
        "image": "base64_encoded_image",
        "success": true
    }
    """
    captcha_code, captcha_image = generate_captcha()
    store_captcha(request, captcha_code)
    return JsonResponse(
        {
            "image": captcha_image,
            "success": True,
        }
    )
