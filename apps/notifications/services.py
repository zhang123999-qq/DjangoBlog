"""
通知服务

提供统一的通知发送接口
"""

import logging
from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


class NotificationService:
    """
    通知服务

    使用方法：
        from apps.notifications.services import NotificationService

        # 发送通知给单个用户
        NotificationService.send_to_user(
            user_id=1,
            title='新评论',
            content='有人评论了你的文章',
            link='/blog/post/xxx/'
        )

        # 发送通知给多个用户
        NotificationService.send_to_users(
            user_ids=[1, 2, 3],
            title='系统公告',
            content='系统维护通知'
        )

        # 广播系统消息
        NotificationService.broadcast(
            title='系统公告',
            content='服务器将于今晚维护'
        )
    """

    # Channel Layer
    _channel_layer = None

    @classmethod
    def get_channel_layer(cls):
        """获取 Channel Layer"""
        if cls._channel_layer is None:
            from channels.layers import get_channel_layer

            cls._channel_layer = get_channel_layer()
        return cls._channel_layer

    @classmethod
    async def async_send_to_user(cls, user_id: int, data: Dict[str, Any]) -> bool:
        """
        异步发送通知给单个用户

        Args:
            user_id: 用户 ID
            data: 通知数据

        Returns:
            bool: 是否发送成功
        """
        try:
            channel_layer = cls.get_channel_layer()
            if channel_layer is None:
                logger.warning("Channel Layer 未配置")
                return False

            group_name = f"user_notifications_{user_id}"

            await channel_layer.group_send(
                group_name,
                {
                    "type": "send_notification",
                    "data": data,
                },
            )

            return True

        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False

    @classmethod
    def send_to_user(
        cls,
        user_id: int,
        title: str,
        content: str,
        link: Optional[str] = None,
        notification_type: str = "info",
        **extra,
    ) -> bool:
        """
        发送通知给单个用户（同步版本）

        Args:
            user_id: 用户 ID
            title: 通知标题
            content: 通知内容
            link: 跳转链接
            notification_type: 通知类型
            **extra: 额外数据

        Returns:
            bool: 是否发送成功
        """
        from asgiref.sync import async_to_sync

        data = {"title": title, "content": content, "link": link, "type": notification_type, **extra}

        try:
            return async_to_sync(cls.async_send_to_user)(user_id, data)
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False

    @classmethod
    def send_to_users(
        cls,
        user_ids: List[int],
        title: str,
        content: str,
        link: Optional[str] = None,
        notification_type: str = "info",
        **extra,
    ) -> Dict[int, bool]:
        """
        发送通知给多个用户

        Args:
            user_ids: 用户 ID 列表
            title: 通知标题
            content: 通知内容
            link: 跳转链接
            notification_type: 通知类型
            **extra: 额外数据

        Returns:
            Dict[int, bool]: 每个用户的发送结果
        """
        results = {}

        for user_id in user_ids:
            results[user_id] = cls.send_to_user(
                user_id=user_id, title=title, content=content, link=link, notification_type=notification_type, **extra
            )

        return results

    @classmethod
    async def async_broadcast(cls, data: Dict[str, Any]) -> bool:
        """
        异步广播消息

        Args:
            data: 消息数据

        Returns:
            bool: 是否发送成功
        """
        try:
            channel_layer = cls.get_channel_layer()
            if channel_layer is None:
                return False

            # 发送到所有在线用户
            # 注意：这需要有一个公共的广播组
            await channel_layer.group_send(
                "broadcast",
                {
                    "type": "send_system_message",
                    "data": data,
                },
            )

            return True

        except Exception as e:
            logger.error(f"广播消息失败: {e}")
            return False

    @classmethod
    def broadcast(cls, title: str, content: str, link: Optional[str] = None, **extra) -> bool:
        """
        广播系统消息（同步版本）

        Args:
            title: 消息标题
            content: 消息内容
            link: 跳转链接
            **extra: 额外数据

        Returns:
            bool: 是否发送成功
        """
        from asgiref.sync import async_to_sync

        data = {"title": title, "content": content, "link": link, **extra}

        try:
            return async_to_sync(cls.async_broadcast)(data)
        except Exception as e:
            logger.error(f"广播消息失败: {e}")
            return False


class NotificationType:
    """通知类型常量"""

    # 评论相关
    NEW_COMMENT = "new_comment"
    COMMENT_REPLY = "comment_reply"
    COMMENT_LIKE = "comment_like"

    # 文章相关
    POST_PUBLISHED = "post_published"
    POST_LIKE = "post_like"

    # 论坛相关
    NEW_TOPIC = "new_topic"
    TOPIC_REPLY = "topic_reply"
    TOPIC_LIKE = "topic_like"

    # 系统通知
    SYSTEM = "system"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_UPDATE = "system_update"

    # 审核相关
    MODERATION_APPROVED = "moderation_approved"
    MODERATION_REJECTED = "moderation_rejected"


# 便捷函数
def notify_comment_reply(comment):
    """通知评论被回复"""
    if comment.user:
        NotificationService.send_to_user(
            user_id=comment.user.id,
            title="收到新回复",
            content=f"有人回复了你在「{comment.post.title}」中的评论",
            link=comment.post.get_absolute_url(),
            notification_type=NotificationType.COMMENT_REPLY,
            comment_id=comment.id,
        )


def notify_post_comment(post, comment):
    """通知文章被评论"""
    if post.author != comment.user:
        NotificationService.send_to_user(
            user_id=post.author.id,
            title="文章收到新评论",
            content=f'{comment.user.username if comment.user else "游客"} 评论了「{post.title}」',
            link=post.get_absolute_url(),
            notification_type=NotificationType.NEW_COMMENT,
            comment_id=comment.id,
        )


def notify_topic_reply(topic, reply):
    """通知主题被回复"""
    if topic.author != reply.author:
        NotificationService.send_to_user(
            user_id=topic.author.id,
            title="主题收到新回复",
            content=f"{reply.author.username} 回复了「{topic.title}」",
            link=topic.get_absolute_url(),
            notification_type=NotificationType.TOPIC_REPLY,
            reply_id=reply.id,
        )


def notify_moderation_result(content, approved: bool, reason: str = ""):
    """通知审核结果"""
    user = getattr(content, "author", None) or getattr(content, "user", None)
    if user:
        NotificationService.send_to_user(
            user_id=user.id,
            title="审核通过" if approved else "审核未通过",
            content="你的内容已通过审核" if approved else f"你的内容未通过审核：{reason}",
            notification_type=(
                NotificationType.MODERATION_APPROVED if approved else NotificationType.MODERATION_REJECTED
            ),
        )
