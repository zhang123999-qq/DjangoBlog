"""
通知模块 URL 配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import NotificationViewSet

app_name = 'notifications'

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
