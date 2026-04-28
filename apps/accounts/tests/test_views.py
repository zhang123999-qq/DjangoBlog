"""
用户视图测试
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAccountViews:
    """用户视图测试"""

    def test_login_view_get(self, client):
        """测试登录页面 GET 请求"""
        response = client.get(reverse('accounts:login'))
        assert response.status_code == 200

    def test_register_view_get(self, client):
        """测试注册页面 GET 请求"""
        response = client.get(reverse('accounts:register'))
        assert response.status_code == 200

    def test_user_registration(self, client, user_data):
        """测试用户注册"""
        response = client.post(
            reverse('accounts:register'),
            {
                'username': user_data['username'],
                'email': user_data['email'],
                'password1': user_data['password'],
                'password2': user_data['password'],
                'captcha': '123456',  # 测试环境会跳过验证码验证
            },
            follow=True
        )

        # 注册成功后应该重定向
        assert response.status_code == 200
        # 用户应该已创建
        assert User.objects.filter(username=user_data['username']).exists()

    def test_user_login(self, client, user_data):
        """测试用户登录"""
        # 先创建用户
        User.objects.create_user(**user_data)

        # 登录
        response = client.post(
            reverse('accounts:login'),
            {
                'username': user_data['username'],
                'password': user_data['password'],
            },
            follow=True
        )

        assert response.status_code == 200

    def test_profile_view_requires_login(self, client):
        """测试个人资料页面需要登录"""
        response = client.get(reverse('accounts:profile'))
        # 未登录应该重定向到登录页面
        assert response.status_code in [302, 403]

    def test_profile_update(self, client, user_data):
        """测试更新个人资料"""
        # 创建用户并登录
        User.objects.create_user(**user_data)
        client.login(username=user_data['username'], password=user_data['password'])

        response = client.post(
            reverse('accounts:profile'),
            {
                'nickname': '新昵称',
                'bio': '新的个人简介',
            },
            follow=True
        )

        assert response.status_code == 200


@pytest.mark.django_db
class TestAccountSecurity:
    """账户安全测试"""

    def test_password_minimum_length(self, client, user_data):
        """测试密码最小长度"""
        response = client.post(
            reverse('accounts:register'),
            {
                'username': user_data['username'],
                'email': user_data['email'],
                'password1': 'short',  # 太短的密码
                'password2': 'short',
            }
        )

        # 应该返回表单错误
        assert response.status_code == 200
        assert not User.objects.filter(username=user_data['username']).exists()

    def test_password_confirmation_mismatch(self, client, user_data):
        """测试密码确认不匹配"""
        response = client.post(
            reverse('accounts:register'),
            {
                'username': user_data['username'],
                'email': user_data['email'],
                'password1': user_data['password'],
                'password2': 'DifferentPassword123!',
            }
        )

        assert response.status_code == 200
        assert not User.objects.filter(username=user_data['username']).exists()

    def test_duplicate_username(self, client, user_data):
        """测试重复用户名"""
        # 创建第一个用户
        User.objects.create_user(**user_data)

        # 尝试用相同用户名注册
        response = client.post(
            reverse('accounts:register'),
            {
                'username': user_data['username'],
                'email': 'another@example.com',
                'password1': user_data['password'],
                'password2': user_data['password'],
            }
        )

        assert response.status_code == 200
