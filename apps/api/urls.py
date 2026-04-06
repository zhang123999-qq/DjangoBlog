"""API URL 配置"""

from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.core.upload_views import upload_file, upload_image, upload_status
from apps.notifications.api_views import NotificationViewSet
from .moderation_views import moderation_approve_api, moderation_reject_api, moderation_metrics_api
from .views import BoardViewSet, CategoryViewSet, PostViewSet, TagViewSet, TopicViewSet
from .search_views import GlobalSearchView, PostSearchView, TopicSearchView, SearchHealthView

app_name = 'api'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),

    # 搜索 API
    path('search/', GlobalSearchView.as_view(), name='search'),
    path('search/posts/', PostSearchView.as_view(), name='search-posts'),
    path('search/topics/', TopicSearchView.as_view(), name='search-topics'),
    path('search/health/', SearchHealthView.as_view(), name='search-health'),

    # 文件上传（鉴权+限流在视图中处理）
    path('upload/image/', upload_image, name='upload-image'),
    path('upload/file/', upload_file, name='upload-file'),
    path('upload/status/<str:upload_id>/', upload_status, name='upload-status'),

    # Moderation JSON API（统一错误码 + OpenAPI）
    path('moderation/metrics/', moderation_metrics_api, name='moderation-metrics'),
    path('moderation/approve/<str:content_type>/<int:content_id>/', moderation_approve_api, name='moderation-approve'),
    path('moderation/reject/<str:content_type>/<int:content_id>/', moderation_reject_api, name='moderation-reject'),

    # API Schema（始终注册，测试环境也需要 schema 端点可用）
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # API 文档页（DEBUG 或测试环境可用）
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
]

