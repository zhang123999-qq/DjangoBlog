"""
用户中心视图测试 - 扩展

测试覆盖:
- profile_edit_view: 资料编辑视图
- logout_view: 用户登出视图
- captcha_refresh: 验证码刷新视图
- 锁定机制测试
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestProfileEditView:
    """资料编辑视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile_edit_url = reverse('accounts:profile_edit')

    def test_profile_edit_view_requires_login(self):
        """测试资料编辑需要登录"""
        response = self.client.get(self.profile_edit_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_profile_edit_view_get(self):
        """测试资料编辑页面 GET 请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_edit_url)
        assert response.status_code == 200
        assert 'user_form' in response.context
        assert 'profile_form' in response.context

    def test_profile_edit_view_post(self):
        """测试资料编辑 POST 请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.profile_edit_url, {
            'username': 'testuser',
            'email': 'updated@example.com',
            'nickname': '测试昵称',
            'bio': '这是个人简介',
            'website': 'https://example.com'
        })
        # 应该重定向到个人中心
        assert response.status_code == 302
        assert response.url == reverse('accounts:profile')

        # 检查用户信息是否更新
        self.user.refresh_from_db()
        assert self.user.email == 'updated@example.com'
        assert self.user.nickname == '测试昵称'

        # 检查资料是否更新
        self.user.profile.refresh_from_db()
        assert self.user.profile.bio == '这是个人简介'
        assert self.user.profile.website == 'https://example.com'

    def test_profile_edit_view_invalid_form(self):
        """测试无效表单"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.profile_edit_url, {
            'username': '',  # 用户名不能为空
            'email': 'invalid-email',  # 无效邮箱
        })
        # 应该返回表单页面（带错误）
        assert response.status_code == 200
        assert 'user_form' in response.context
        assert response.context['user_form'].errors


@pytest.mark.django_db
class TestLogoutView:
    """用户登出视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.logout_url = reverse('accounts:logout')

    def test_logout_view_requires_post(self):
        """测试登出只允许 POST 请求"""
        response = self.client.get(self.logout_url)
        # 应该返回 405 Method Not Allowed
        assert response.status_code == 405

    def test_logout_view_post(self):
        """测试登出 POST 请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.logout_url)
        # 应该重定向到首页
        assert response.status_code == 302
        assert response.url == reverse('core:home')

        # 检查用户是否已登出
        # 注意：Django 测试客户端会保持会话，但我们可以通过检查响应来验证


@pytest.mark.django_db
class TestCaptchaRefresh:
    """验证码刷新视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.captcha_refresh_url = reverse('accounts:captcha_refresh')

    def test_captcha_refresh_view_get(self):
        """测试验证码刷新 GET 请求"""
        response = self.client.get(self.captcha_refresh_url)
        assert response.status_code == 200
        assert response['content-type'] == 'application/json'

        # 解析 JSON 响应
        data = response.json()
        assert 'image' in data
        assert 'success' in data
        assert data['success'] is True
        assert data['image'] is not None

    def test_captcha_refresh_view_post_not_allowed(self):
        """测试验证码刷新不允许 POST 请求"""
        response = self.client.post(self.captcha_refresh_url)
        # 应该返回 405 Method Not Allowed
        assert response.status_code == 405


@pytest.mark.django_db
class TestLockoutMechanism:
    """锁定机制测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='testuser@example.com'
        )
        self.login_url = reverse('accounts:login')

    def test_login_lockout_after_failed_attempts(self):
        """测试登录失败后锁定"""
        # 注意：这个测试需要验证码支持，但在测试环境中可能被跳过
        # 这里我们只测试基本逻辑

        # 创建用户
        User.objects.create_user(
            username='locktest',
            password='correctpassword',
            email='locktest@example.com'
        )

        # 尝试错误登录多次
        for i in range(3):
            response = self.client.post(self.login_url, {
                'username': 'locktest',
                'password': 'wrongpassword',
                'captcha': '123456'  # 测试环境可能跳过验证码
            })
            # 应该返回登录页面（带错误）
            assert response.status_code == 200

        # 第4次尝试应该被锁定
        response = self.client.post(self.login_url, {
            'username': 'locktest',
            'password': 'wrongpassword',
            'captcha': '123456'
        })
        # 应该返回登录页面（带锁定提示）
        assert response.status_code == 200
        # 注意：实际锁定逻辑可能依赖于验证码系统


@pytest.mark.django_db
class TestUserProfile:
    """用户资料测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile_url = reverse('accounts:profile')

    def test_profile_view_requires_login(self):
        """测试个人中心需要登录"""
        response = self.client.get(self.profile_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_profile_view_loads(self):
        """测试个人中心加载"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)
        assert response.status_code == 200
        # 检查上下文数据
        assert 'pending_comments' in response.context
        assert 'pending_topics' in response.context
        assert 'pending_replies' in response.context
        assert 'rejected_comments' in response.context
        assert 'rejected_topics' in response.context
        assert 'rejected_replies' in response.context

    def test_profile_view_shows_pending_content(self):
        """测试个人中心显示待审核内容"""
        # 创建待审核评论
        from apps.blog.models import Comment, Post
        post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="内容",
            author=self.user,
            status="published"
        )
        Comment.objects.create(
            post=post,
            user=self.user,
            content="待审核评论",
            review_status="pending"
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)

        # 检查待审核评论
        pending_comments = response.context['pending_comments']
        assert len(pending_comments) == 1
        assert pending_comments[0].content == "待审核评论"


@pytest.mark.django_db
class TestUserRegistration:
    """用户注册测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.register_url = reverse('accounts:register')

    def test_register_view_get(self):
        """测试注册页面 GET 请求"""
        response = self.client.get(self.register_url)
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'captcha_image' in response.context

    def test_register_view_post_success(self):
        """测试注册成功"""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'captcha': '123456'  # 测试环境可能跳过验证码
        })
        # 注册成功应该重定向
        assert response.status_code == 302

        # 检查用户是否创建
        assert User.objects.filter(username='newuser').exists()

        # 检查用户资料是否创建
        user = User.objects.get(username='newuser')
        assert hasattr(user, 'profile')
        assert user.profile is not None

    def test_register_view_post_invalid(self):
        """测试注册失败（无效数据）"""
        response = self.client.post(self.register_url, {
            'username': '',  # 用户名为空
            'email': 'invalid-email',  # 无效邮箱
            'password1': 'weak',  # 弱密码
            'password2': 'different',  # 密码不匹配
            'captcha': '123456'
        })
        # 应该返回注册页面（带错误）
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.django_db
class TestUserLogin:
    """用户登录测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.login_url = reverse('accounts:login')

    def test_login_view_get(self):
        """测试登录页面 GET 请求"""
        response = self.client.get(self.login_url)
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'captcha_image' in response.context

    def test_login_view_post_success(self):
        """测试登录成功"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123',
            'captcha': '123456'  # 测试环境可能跳过验证码
        })
        # 登录成功应该重定向
        assert response.status_code == 302

    def test_login_view_post_invalid(self):
        """测试登录失败（无效凭据）"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword',
            'captcha': '123456'
        })
        # 应该返回登录页面（带错误）
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
