from django.test import TestCase
from django.urls import reverse
from .models import User
import os


class AccountsTestCase(TestCase):
    def setUp(self):
        """设置测试环境"""
        # 创建安装锁文件，避免被安装中间件重定向
        self.installed_lock_path = 'installed.lock'
        with open(self.installed_lock_path, 'w') as f:
            f.write('installed')

    def tearDown(self):
        """清理测试环境"""
        # 测试后移除安装锁文件
        if os.path.exists(self.installed_lock_path):
            os.remove(self.installed_lock_path)

    def test_register_page_accessible(self):
        """测试注册页可访问"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_user_registration_success(self):
        """测试用户注册成功"""
        # 先获取验证码
        response = self.client.get(reverse('accounts:register'))
        captcha_code = self.client.session.get('captcha_code')

        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'captcha': captcha_code
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 302)  # 重定向到首页
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')

    def test_login_success(self):
        """测试登录成功"""
        # 创建测试用户
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        # 先获取验证码
        response = self.client.get(reverse('accounts:login'))
        captcha_code = self.client.session.get('captcha_code')

        # 登录
        data = {
            'username': 'testuser',
            'password': 'testpassword123',
            'captcha': captcha_code
        }
        response = self.client.post(reverse('accounts:login'), data)
        self.assertEqual(response.status_code, 302)  # 重定向

        # 验证用户已登录
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'testuser')
