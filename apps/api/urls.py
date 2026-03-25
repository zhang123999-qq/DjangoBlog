"""API URL 配置"""

from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.core.upload_views import upload_file, upload_image, upload_status
from .views import BoardViewSet, CategoryViewSet, PostViewSet, TagViewSet, TopicViewSet

app_name = 'api'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'topics', TopicViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
    # 文件上传（鉴权+限流在视图中处理）
    path('upload/image/', upload_image, name='upload-image'),
    path('upload/file/', upload_file, name='upload-file'),
    path('upload/status/<str:upload_id>/', upload_status, name='upload-status'),
    # API Schema（保留）
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
]

# API 文档页：仅开发环境开放
if settings.DEBUG:
    urlpatterns += [
        path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
        path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    ]
