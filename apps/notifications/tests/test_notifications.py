"""
通知模块测试
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.notifications.models import Notification

User = get_user_model()


@pytest.mark.django_db
class TestNotificationModel:
    """通知模型测试"""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_notification(self, user):
        """测试创建通知"""
        notification = Notification.objects.create(
            user=user,
            title='测试通知',
            content='这是测试通知内容',
            notification_type='system'
        )

        assert notification.pk is not None
        assert notification.title == '测试通知'
        assert notification.is_read is False

    def test_mark_as_read(self, user):
        """测试标记已读"""
        notification = Notification.objects.create(
            user=user,
            title='测试通知',
            content='内容'
        )

        notification.mark_as_read()

        assert notification.is_read is True
        assert notification.read_at is not None

    def test_get_unread_count(self, user):
        """测试获取未读数量"""
        # 创建多个通知
        for i in range(5):
            Notification.objects.create(
                user=user,
                title=f'通知 {i}',
                content='内容'
            )

        count = Notification.get_unread_count(user)
        assert count == 5

    def test_get_recent(self, user):
        """测试获取最近通知"""
        for i in range(15):
            Notification.objects.create(
                user=user,
                title=f'通知 {i}',
                content='内容'
            )

        recent = Notification.get_recent(user, limit=10)
        assert len(recent) == 10


@pytest.mark.django_db
class TestNotificationAPI:
    """通知 API 测试"""

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        return user

    def test_list_notifications(self, client, user):
        """测试获取通知列表"""
        client.force_authenticate(user=user)

        # 创建通知
        Notification.objects.create(user=user, title='通知1', content='内容1')
        Notification.objects.create(user=user, title='通知2', content='内容2')

        response = client.get('/api/notifications/')

        assert response.status_code == 200

    def test_unread_count(self, client, user):
        """测试获取未读数量"""
        client.force_authenticate(user=user)

        # 创建通知
        Notification.objects.create(user=user, title='通知', content='内容')

        response = client.get('/api/notifications/unread_count/')

        assert response.status_code == 200

    def test_mark_read(self, client, user):
        """测试标记已读"""
        client.force_authenticate(user=user)

        notification = Notification.objects.create(
            user=user,
            title='通知',
            content='内容'
        )

        response = client.post(f'/api/notifications/{notification.id}/mark_read/')

        assert response.status_code == 200

        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_all_read(self, client, user):
        """测试标记所有已读"""
        client.force_authenticate(user=user)

        # 创建多个通知
        for i in range(5):
            Notification.objects.create(user=user, title=f'通知{i}', content='内容')

        response = client.post('/api/notifications/mark_all_read/')

        assert response.status_code == 200

        count = Notification.get_unread_count(user)
        assert count == 0


class TestNotificationService:
    """通知服务测试"""

    def test_notification_type_constants(self):
        """测试通知类型常量"""
        from apps.notifications.services import NotificationType

        assert NotificationType.NEW_COMMENT == 'new_comment'
        assert NotificationType.SYSTEM == 'system'
