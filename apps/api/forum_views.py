"""
论坛写操作 API 视图

提供创建主题、创建回复、点赞回复三个端点。
Optimistic UI 前端依赖这些端点实现无刷新交互。
"""

import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.api.response import APIResponse
from apps.forum import services as forum_services
from apps.forum.services import TopicLockedError

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_topic_api(request, board_slug: str):
    """
    POST /api/boards/<board_slug>/topics/create/

    创建主题帖。需要登录。
    请求体: {"title": "...", "content": "..."}
    """
    title = request.data.get("title", "").strip()
    content = request.data.get("content", "").strip()

    # 输入验证（仅协议层，业务规则在 services 中）
    errors = {}
    if not title:
        errors["title"] = ["标题不能为空"]
    elif len(title) > 200:
        errors["title"] = ["标题不能超过200个字符"]
    if not content:
        errors["content"] = ["内容不能为空"]

    if errors:
        return APIResponse.bad_request(message="表单验证失败", errors=errors)

    try:
        result = forum_services.create_topic(
            board_slug=board_slug,
            user=request.user,
            title=title,
            content=content,
        )
    except Exception:
        return APIResponse.not_found(message="版块不存在")

    status = result["status"]
    data = result["result"]

    if status == "approved":
        return APIResponse.success(data=data, message="主题已发布")
    elif status == "rejected":
        return APIResponse.error(message=f"主题未通过审核: {result['message']}", code=400)
    else:
        return APIResponse.success(data=data, message="主题已提交，等待审核后显示")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_reply_api(request, topic_id: int):
    """
    POST /api/topics/<topic_id>/replies/create/

    创建回复。需要登录。
    请求体: {"content": "..."}
    """
    content = request.data.get("content", "").strip()

    if not content:
        return APIResponse.bad_request(message="内容不能为空", errors={"content": ["内容不能为空"]})

    try:
        result = forum_services.create_reply(
            topic_id=topic_id,
            user=request.user,
            content=content,
        )
    except TopicLockedError:
        return APIResponse.forbidden("主题已被锁定，无法回复")
    except Exception:
        return APIResponse.not_found(message="主题不存在或未审核通过")

    status = result["status"]
    data = result["result"]

    if status == "approved":
        return APIResponse.success(data=data, message="回复已发布")
    elif status == "rejected":
        return APIResponse.error(message=f"回复未通过审核: {result['message']}", code=400)
    else:
        return APIResponse.success(data=data, message="回复已提交，等待审核后显示")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def like_reply_api(request, reply_id: int):
    """
    POST /api/replies/<reply_id>/like/

    切换点赞状态（Optimistic UI）。需要登录。
    返回: {"liked": true/false, "like_count": N}
    """
    try:
        data = forum_services.toggle_reply_like(reply_id=reply_id, user=request.user)
    except Exception:
        return APIResponse.not_found(message="回复不存在")

    return APIResponse.success(data=data)
