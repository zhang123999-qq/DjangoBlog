"""论坛业务逻辑层

封装主题创建、回复创建、点赞切换等核心业务操作。
视图层仅负责 HTTP 协议处理，所有业务规则在此模块中实现。
"""

import logging

from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.forum.models import Board, Reply, ReplyLike, Topic
from apps.notifications.services import notify_topic_reply

logger = logging.getLogger(__name__)


def create_topic(board_slug: str, user, title: str, content: str) -> dict:
    """创建主题帖并执行智能审核。

    Args:
        board_slug: 版块 slug
        user: 当前登录用户
        title: 主题标题
        content: 主题内容

    Returns:
        dict: 包含 topic, status, message 的结果字典

    Raises:
        Board.DoesNotExist: 版块不存在
    """
    board = get_object_or_404(Board, slug=board_slug)

    topic = Topic.objects.create(
        board=board,
        author=user,
        title=title,
        content=content,
        review_status="pending",
    )

    from moderation.services import moderate_with_fallback

    status, message = moderate_with_fallback(topic)

    board.update_counts()

    return {
        "topic": topic,
        "status": status,
        "message": message,
        "result": {
            "id": topic.id,
            "title": topic.title,
            "review_status": status,
            "message": _moderation_message(status, message),
            "created_at": topic.created_at.isoformat(),
        },
    }


def create_reply(topic_id: int, user, content: str) -> dict:
    """创建回复并执行智能审核。

    Args:
        topic_id: 主题 ID
        user: 当前登录用户
        content: 回复内容

    Returns:
        dict: 包含 reply, status, message 的结果字典

    Raises:
        Topic.DoesNotExist: 主题不存在或未审核通过
        TopicLockedError: 主题已被锁定（自定义异常）
    """
    topic = get_object_or_404(Topic, id=topic_id, review_status="approved")

    if topic.is_locked:
        raise TopicLockedError("主题已被锁定，无法回复")

    reply = Reply.objects.create(
        topic=topic,
        author=user,
        content=content,
        review_status="pending",
    )

    from moderation.services import moderate_with_fallback

    status, message = moderate_with_fallback(reply)

    topic.update_reply_count()

    if topic.author != user:
        try:
            notify_topic_reply(topic, reply)
        except Exception as e:
            logger.warning("发送通知失败: %s", e)

    return {
        "reply": reply,
        "status": status,
        "message": message,
        "result": {
            "id": reply.id,
            "content": reply.content,
            "review_status": status,
            "message": _moderation_message(status, message),
            "created_at": reply.created_at.isoformat(),
            "author": {
                "id": user.id,
                "username": user.username,
            },
        },
    }


def toggle_reply_like(reply_id: int, user) -> dict:
    """切换回复点赞状态。

    使用 select_for_update 保证并发安全。

    Args:
        reply_id: 回复 ID
        user: 当前登录用户

    Returns:
        dict: {"liked": bool, "like_count": int}

    Raises:
        Reply.DoesNotExist: 回复不存在或已删除
    """
    with transaction.atomic():
        reply = get_object_or_404(
            Reply.objects.select_for_update(),
            id=reply_id,
            review_status="approved",
            is_deleted=False,
        )

        like, created = ReplyLike.objects.get_or_create(user=user, reply=reply)

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        reply.update_like_count()

    return {
        "liked": liked,
        "like_count": reply.like_count,
    }


def _moderation_message(status: str, message: str) -> str:
    """生成审核状态提示消息"""
    if status == "approved":
        return "已通过审核"
    elif status == "rejected":
        return f"未通过审核: {message}"
    else:
        return "等待审核中"


class TopicLockedError(Exception):
    """主题已被锁定时抛出的业务异常"""

    pass
