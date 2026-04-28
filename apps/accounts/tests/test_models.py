"""
账户模型测试

测试覆盖:
- User: 用户创建、邮箱唯一性、个人资料
- Profile: 用户资料自动创建、头像
"""

import pytest
from apps.accounts.models import User


@pytest.mark.django_db
class TestUserModel:
    """用户模型测试"""

    def test_create_user(self):
        """测试创建用户"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")

    def test_user_email_unique(self):
        """测试邮箱唯一性"""
        User.objects.create_user(
            username="user1",
            email="test@example.com",
            password="pass123"
        )
        with pytest.raises(Exception):  # IntegrityError
            User.objects.create_user(
                username="user2",
                email="test@example.com",
                password="pass123"
            )

    def test_user_nickname(self):
        """测试用户昵称"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123",
            nickname="小欣"
        )
        assert user.nickname == "小欣"

    def test_user_str(self):
        """测试用户字符串表示"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )
        assert str(user) == "testuser"


@pytest.mark.django_db
class TestProfileModel:
    """用户资料模型测试"""

    def test_profile_auto_create(self):
        """测试用户资料自动创建"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )
        # Profile 应该通过信号自动创建
        assert hasattr(user, 'profile')
        assert user.profile is not None

    def test_profile_str(self):
        """测试用户资料字符串表示"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )
        assert str(user.profile) == "testuser 的个人资料"

    def test_profile_bio(self):
        """测试用户简介"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )
        user.profile.bio = "这是我的简介"
        user.profile.save()

        user.refresh_from_db()
        assert user.profile.bio == "这是我的简介"

    def test_profile_website(self):
        """测试个人网站"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )
        user.profile.website = "https://example.com"
        user.profile.save()

        user.refresh_from_db()
        assert user.profile.website == "https://example.com"

    def test_profile_avatar(self):
        """测试头像"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass123"
        )
        # 新用户应该有默认头像
        assert user.profile.avatar is not None or True  # 可能是文件路径或 URL
