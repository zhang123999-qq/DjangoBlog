"""
WebSocket 消费者

处理 WebSocket 连接、消息推送等
"""

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    通知消费者

    处理实时通知推送

    连接格式：
        ws://domain/ws/notifications/

    消息格式：
        {
            "type": "notification",
            "data": {
                "title": "标题",
                "content": "内容",
                "link": "/path/to/content",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    """

    # 用户组名前缀
    USER_GROUP_PREFIX = "user_notifications_"

    async def connect(self):
        """
        连接处理

        验证用户身份并加入用户专属组
        """
        # 获取用户
        user = self.scope.get("user")

        if user is None or not user.is_authenticated:
            # 未认证用户拒绝连接
            logger.warning("WebSocket 连接被拒绝：未认证用户")
            await self.close()
            return

        # 设置用户
        self.user = user
        self.user_group = f"{self.USER_GROUP_PREFIX}{user.id}"

        # 加入用户专属组
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        # 接受连接
        await self.accept()

        # 更新在线状态
        await self.set_online_status(True)

        logger.info(f"用户 {user.username} 已连接 WebSocket")

        # 发送连接成功消息
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connected",
                    "message": "WebSocket 连接成功",
                    "user_id": user.id,
                }
            )
        )

    async def disconnect(self, close_code):
        """
        断开连接处理
        """
        if hasattr(self, "user_group"):
            # 离开用户组
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

        # 更新在线状态
        if hasattr(self, "user"):
            await self.set_online_status(False)
            logger.info(f"用户 {self.user.username} 已断开 WebSocket")

    async def receive(self, text_data):
        """
        接收消息处理

        处理客户端发送的消息
        """
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "ping":
                # 心跳检测
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "pong",
                            "timestamp": str(timezone.now()),
                        }
                    )
                )

            elif message_type == "mark_read":
                # 标记消息已读
                notification_id = data.get("notification_id")
                if notification_id:
                    await self.mark_notification_read(notification_id)

            else:
                logger.warning(f"未知的消息类型: {message_type}")

        except json.JSONDecodeError:
            logger.error("无效的 JSON 数据")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")

    async def send_notification(self, event):
        """
        发送通知

        由 Channel Layer 调用
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "data": event["data"],
                }
            )
        )

    async def send_system_message(self, event):
        """
        发送系统消息
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "system",
                    "data": event["data"],
                }
            )
        )

    @database_sync_to_async
    def set_online_status(self, is_online: bool):
        """
        设置用户在线状态

        Args:
            is_online: 是否在线
        """
        try:
            from django.core.cache import cache

            cache_key = f"user_online:{self.user.id}"

            if is_online:
                cache.set(cache_key, True, 300)  # 5 分钟过期
            else:
                cache.delete(cache_key)

        except Exception as e:
            logger.error(f"设置在线状态失败: {e}")

    @database_sync_to_async
    def mark_notification_read(self, notification_id: int):
        """标记通知已读"""
        try:
            # 这里需要根据实际的通知模型来实现
            pass
        except Exception as e:
            logger.error(f"标记通知已读失败: {e}")


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    """
    在线状态消费者

    广播用户在线/离线状态
    """

    ONLINE_GROUP = "online_users"

    async def connect(self):
        """连接处理"""
        user = self.scope.get("user")

        if user is None or not user.is_authenticated:
            await self.close()
            return

        self.user = user

        # 加入在线用户组
        await self.channel_layer.group_add(self.ONLINE_GROUP, self.channel_name)

        await self.accept()

        # 广播上线消息
        await self.channel_layer.group_send(
            self.ONLINE_GROUP,
            {
                "type": "user_online",
                "user_id": user.id,
                "username": user.username,
            },
        )

    async def disconnect(self, close_code):
        """断开连接处理"""
        if hasattr(self, "user"):
            # 广播离线消息
            await self.channel_layer.group_send(
                self.ONLINE_GROUP,
                {
                    "type": "user_offline",
                    "user_id": self.user.id,
                    "username": self.user.username,
                },
            )

            # 离开组
            await self.channel_layer.group_discard(self.ONLINE_GROUP, self.channel_name)

    async def user_online(self, event):
        """广播上线消息"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_online",
                    "user_id": event["user_id"],
                    "username": event["username"],
                }
            )
        )

    async def user_offline(self, event):
        """广播离线消息"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_offline",
                    "user_id": event["user_id"],
                    "username": event["username"],
                }
            )
        )


class ChatConsumer(AsyncWebsocketConsumer):
    """
    聊天消费者

    处理实时聊天消息
    """

    async def connect(self):
        """连接处理"""
        self.room_name = self.scope["url_route"]["kwargs"].get("room_name", "public")
        self.room_group = f"chat_{self.room_name}"

        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close()
            return

        self.user = user

        # 加入聊天室
        await self.channel_layer.group_add(self.room_group, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        """断开连接"""
        if hasattr(self, "room_group"):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        """接收消息"""
        try:
            data = json.loads(text_data)
            message = data.get("message", "")

            if not message.strip():
                return

            # 广播消息到聊天室
            await self.channel_layer.group_send(
                self.room_group,
                {
                    "type": "chat_message",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "message": message,
                    "timestamp": str(timezone.now()),
                },
            )

        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"处理聊天消息失败: {e}")

    async def chat_message(self, event):
        """发送聊天消息"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "message": event["message"],
                    "timestamp": event["timestamp"],
                }
            )
        )
