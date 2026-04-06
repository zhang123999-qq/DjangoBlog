"""
通知 API 视图
"""

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .models import Notification
from apps.api.response import APIResponse


class NotificationSerializer(serializers.ModelSerializer):
    """通知序列化器"""

    class Meta:
        model = Notification
        fields = ['id', 'title', 'content', 'notification_type', 'link', 'is_read', 'created_at']


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    通知 API

    list: 获取通知列表
    retrieve: 获取通知详情
    mark_read: 标记为已读
    mark_all_read: 标记所有已读
    unread_count: 获取未读数量
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @extend_schema(
        operation_id='get_notifications',
        summary='获取通知列表',
    )
    def list(self, request):
        """获取通知列表"""
        queryset = self.get_queryset()
        is_read = request.query_params.get('is_read')

        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [
                {
                    'id': n.id,
                    'title': n.title,
                    'content': n.content,
                    'type': n.notification_type,
                    'link': n.link,
                    'is_read': n.is_read,
                    'created_at': n.created_at.isoformat(),
                }
                for n in page
            ]
            return self.get_paginated_response(data)

        data = [
            {
                'id': n.id,
                'title': n.title,
                'content': n.content,
                'type': n.notification_type,
                'link': n.link,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
            }
            for n in queryset
        ]

        return APIResponse.success(data=data)

    @extend_schema(
        operation_id='mark_notification_read',
        summary='标记通知为已读',
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记单个通知为已读"""
        notification = self.get_object()
        notification.mark_as_read()

        return APIResponse.success(message='已标记为已读')

    @extend_schema(
        operation_id='mark_all_notifications_read',
        summary='标记所有通知为已读',
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """标记所有通知为已读"""
        from django.utils import timezone

        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        return APIResponse.success(message=f'已标记 {updated} 条通知为已读')

    @extend_schema(
        operation_id='get_unread_notification_count',
        summary='获取未读通知数量',
    )
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """获取未读通知数量"""
        count = Notification.get_unread_count(request.user)

        return APIResponse.success(data={'count': count})

    @extend_schema(
        operation_id='clear_read_notifications',
        summary='清除已读通知',
    )
    @action(detail=False, methods=['post'])
    def clear_read(self, request):
        """清除已读通知"""
        deleted, _ = Notification.objects.filter(
            user=request.user,
            is_read=True
        ).delete()

        return APIResponse.success(message=f'已清除 {deleted} 条通知')
