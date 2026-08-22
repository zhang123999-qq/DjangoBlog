"""API URL 配置"""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.core.upload_views import upload_file, upload_image, upload_status
from apps.notifications.api_views import NotificationViewSet

from .auth_views import api_csrf_token, api_login, api_logout, api_register, api_user_info
from .comment_views import api_create_comment
from .forum_views import create_reply_api, create_topic_api, like_reply_api
from .moderation_views import moderation_approve_api, moderation_metrics_api, moderation_reject_api
from .search_views import GlobalSearchView, PostSearchView, SearchHealthView, TopicSearchView
from .tool_views import tool_detail_api, tool_execute_api, tool_list_api
from .views import BoardViewSet, CategoryViewSet, PostViewSet, TagViewSet, TopicViewSet

app_name = "api"

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"posts", PostViewSet, basename="post")
router.register(r"boards", BoardViewSet, basename="board")
router.register(r"topics", TopicViewSet, basename="topic")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
    # 认证 API
    path("auth/login/", api_login, name="auth-login"),
    path("auth/register/", api_register, name="auth-register"),
    path("auth/logout/", api_logout, name="auth-logout"),
    path("auth/user/", api_user_info, name="auth-user-info"),
    path("auth/csrf/", api_csrf_token, name="auth-csrf"),
    # 评论 API
    path("posts/<slug:slug>/comments/create/", api_create_comment, name="post-comment-create"),
    # 搜索 API
    path("search/", GlobalSearchView.as_view(), name="search"),
    path("search/posts/", PostSearchView.as_view(), name="search-posts"),
    path("search/topics/", TopicSearchView.as_view(), name="search-topics"),
    path("search/health/", SearchHealthView.as_view(), name="search-health"),
    # 文件上传（鉴权+限流在视图中处理）
    path("upload/image/", upload_image, name="upload-image"),
    path("upload/file/", upload_file, name="upload-file"),
    path("upload/status/<str:upload_id>/", upload_status, name="upload-status"),
    # 论坛写操作 API
    path("boards/<slug:board_slug>/topics/create/", create_topic_api, name="forum-create-topic"),
    path("topics/<int:topic_id>/replies/create/", create_reply_api, name="forum-create-reply"),
    path("replies/<int:reply_id>/like/", like_reply_api, name="forum-like-reply"),
    # 工具 API
    path("tools/", tool_list_api, name="tool-list"),
    path("tools/<slug:slug>/", tool_detail_api, name="tool-detail"),
    path("tools/<slug:slug>/execute/", tool_execute_api, name="tool-execute"),
    # Moderation JSON API（统一错误码 + OpenAPI）
    path("moderation/metrics/", moderation_metrics_api, name="moderation-metrics"),
    path("moderation/approve/<str:content_type>/<int:content_id>/", moderation_approve_api, name="moderation-approve"),
    path("moderation/reject/<str:content_type>/<int:content_id>/", moderation_reject_api, name="moderation-reject"),
    # API Schema（始终注册，测试环境也需要 schema 端点可用）
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # API 文档页（DEBUG 或测试环境可用）
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
]
