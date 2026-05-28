"""
WebSocket 路由配置
"""

from django.urls import path, re_path

from .consumers import ChatConsumer, NotificationConsumer, OnlineStatusConsumer

websocket_urlpatterns = [
    # 通知 WebSocket
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    # 在线状态 WebSocket
    path("ws/online/", OnlineStatusConsumer.as_asgi()),
    # 聊天室 WebSocket
    re_path(r"ws/chat/(?P<room_name>\w+)/$", ChatConsumer.as_asgi()),
]
