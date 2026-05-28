from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.blog.models import Comment
from apps.forum.models import Reply, Topic

from .services import approve_instance, reject_instance


def is_moderator(user):
    """检查用户是否为管理员。"""
    return user.is_staff or user.is_superuser


def get_content_model(content_type):
    """根据内容类型获取对应的模型。"""
    mapping = {
        "comment": Comment,
        "topic": Topic,
        "reply": Reply,
    }
    return mapping.get(content_type)


@user_passes_test(is_moderator, login_url="accounts:login")
def moderation_dashboard(request):
    """审核中心仪表板。"""
    pending_comments = Comment.objects.filter(review_status="pending")
    pending_topics = Topic.objects.filter(review_status="pending")
    pending_replies = Reply.objects.filter(review_status="pending")

    context = {
        "pending_comments": pending_comments,
        "pending_topics": pending_topics,
        "pending_replies": pending_replies,
    }
    return render(request, "moderation/dashboard.html", context)


@require_POST
@user_passes_test(is_moderator, login_url="accounts:login")
def approve_content(request, content_type, content_id):
    """页面模式：通过审核。"""
    model = get_content_model(content_type)
    if model is None:
        messages.error(request, "不支持的内容类型")
        return redirect("moderation:dashboard")

    content = get_object_or_404(model, id=content_id)
    try:
        approve_instance(content, request.user, note="")
        messages.success(request, "内容已通过审核")
    except DatabaseError:
        messages.error(request, "审核通过失败，请稍后重试")

    return redirect("moderation:dashboard")


@user_passes_test(is_moderator, login_url="accounts:login")
def reject_content(request, content_type, content_id):
    """页面模式：拒绝审核。"""
    model = get_content_model(content_type)
    if model is None:
        messages.error(request, "不支持的内容类型")
        return redirect("moderation:dashboard")

    content = get_object_or_404(model, id=content_id)

    if request.method == "POST":
        review_note = request.POST.get("review_note", "")
        try:
            reject_instance(content, request.user, note=review_note)
            messages.success(request, "内容已拒绝")
        except DatabaseError:
            messages.error(request, "审核拒绝失败，请稍后重试")
        return redirect("moderation:dashboard")

    context = {
        "content": content,
        "content_type": content_type,
    }
    return render(request, "moderation/reject.html", context)


@require_POST
@user_passes_test(is_moderator, login_url="accounts:login")
def approve_content_api(request, content_type, content_id):
    """API 模式：通过审核（使用统一响应格式）。"""
    from apps.api.response import APIResponse

    model = get_content_model(content_type)
    if model is None:
        return APIResponse.error("不支持的内容类型", code=400, error_code="INVALID_CONTENT_TYPE")

    content = model.objects.filter(id=content_id).first()
    if content is None:
        return APIResponse.not_found("内容不存在")

    try:
        approve_instance(content, request.user, note="")
        return APIResponse.success(data={"status": "approved", "id": content_id})
    except DatabaseError:
        return APIResponse.server_error("审核通过失败，请稍后重试")


@require_POST
@user_passes_test(is_moderator, login_url="accounts:login")
def reject_content_api(request, content_type, content_id):
    """API 模式：拒绝审核（使用统一响应格式）。"""
    from apps.api.response import APIResponse

    model = get_content_model(content_type)
    if model is None:
        return APIResponse.error("不支持的内容类型", code=400, error_code="INVALID_CONTENT_TYPE")

    content = model.objects.filter(id=content_id).first()
    if content is None:
        return APIResponse.not_found("内容不存在")

    review_note = request.POST.get("review_note", "")
    try:
        reject_instance(content, request.user, note=review_note)
        return APIResponse.success(data={"status": "rejected", "id": content_id})
    except DatabaseError:
        return APIResponse.server_error("审核拒绝失败，请稍后重试")
