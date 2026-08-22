"""博客业务逻辑层

封装评论创建等核心业务操作。
视图层仅负责 HTTP 协议处理，所有业务规则在此模块中实现。
"""

import logging

from apps.blog.models import Comment, Post

logger = logging.getLogger(__name__)


def create_comment(slug: str, user, content: str, ip_address: str | None = None) -> dict:
    """创建评论并执行智能审核。

    Args:
        slug: 文章 slug
        user: 当前登录用户
        content: 评论内容
        ip_address: 客户端 IP 地址

    Returns:
        dict: 包含 comment, status, message 的结果字典

    Raises:
        Post.DoesNotExist: 文章不存在或未发布
        CommentsClosedError: 文章已关闭评论
        ValidationError: 评论内容为空或超长
    """
    try:
        post = Post.objects.get(slug=slug, status="published")
    except Post.DoesNotExist:
        raise

    if not post.allow_comments:
        raise CommentsClosedError("该文章已关闭评论")

    if not content:
        raise ValidationError("评论内容不能为空")

    if len(content) > 2000:
        raise ValidationError("评论内容不能超过 2000 个字符")

    comment = Comment.objects.create(
        post=post,
        user=user,
        content=content,
        review_status="pending",
        ip_address=ip_address,
    )

    from moderation.services import moderate_with_fallback

    status, message = moderate_with_fallback(comment)

    return {
        "comment": comment,
        "status": status,
        "message": message,
        "result": {
            "id": comment.pk,
            "content": comment.content,
            "review_status": status,
            "created_at": comment.created_at.isoformat(),
            "user": {
                "id": user.pk,
                "username": user.username,
            },
        },
    }


class CommentsClosedError(Exception):
    """文章已关闭评论时抛出的业务异常"""

    pass


class ValidationError(Exception):
    """评论内容验证失败时抛出的业务异常"""

    pass
