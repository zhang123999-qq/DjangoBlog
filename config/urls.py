"""URL configuration for project."""

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.admin import admin_site

urlpatterns = [
    # 核心路由
    path('', include('apps.core.urls', namespace='core')),
    # 认证路由
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    # 主要功能路由
    path('blog/', include('apps.blog.urls', namespace='blog')),
    path('forum/', include('apps.forum.urls', namespace='forum')),
    path('tools/', include('apps.tools.urls', namespace='tools')),
    # API路由
    path('api/', include('apps.api.urls', namespace='api')),
    # 管理路由
    path('admin/', admin_site.urls),
    path('moderation/', include('moderation.urls', namespace='moderation')),
]

# 开发模式下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
