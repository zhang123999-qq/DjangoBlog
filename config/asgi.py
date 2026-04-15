"""
ASGI config for project.

支持：
- HTTP 请求（Django）
- WebSocket 连接（Channels，可选）
"""

import os

from django.core.asgi import get_asgi_application

# Keep ASGI default aligned with production runtime (can be overridden by env)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# 获取 Django ASGI 应用
django_asgi_app = get_asgi_application()

# 尝试加载 Channels 支持（可选依赖）
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from apps.notifications.routing import websocket_urlpatterns

    # ASGI 应用配置（支持 WebSocket）
    application = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        }
    )
except ImportError:
    # Channels 未安装，使用标准 Django ASGI
    application = django_asgi_app
