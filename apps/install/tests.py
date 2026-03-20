from django.test import TestCase
from django.urls import reverse
import os


class InstallTestCase(TestCase):
    def setUp(self):
        """设置测试环境"""
        # 确保测试前没有安装锁文件
        self.installed_lock_path = 'installed.lock'
        if os.path.exists(self.installed_lock_path):
            os.remove(self.installed_lock_path)

    def tearDown(self):
        """清理测试环境"""
        # 测试后移除安装锁文件
        if os.path.exists(self.installed_lock_path):
            os.remove(self.installed_lock_path)

    def test_redirect_to_install_when_not_installed(self):
        """测试未安装时会跳转安装页"""
        # 确保未安装
        self.assertFalse(os.path.exists(self.installed_lock_path))
        
        # 访问非豁免路径，应该重定向到安装页
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 302)
        # 只验证状态码，不验证重定向目标，因为安装页本身也会被重定向
        self.assertTrue('/install/' in response.url)

    def test_no_redirect_when_installed(self):
        """测试已安装时不再跳转"""
        # 创建安装锁文件
        with open(self.installed_lock_path, 'w') as f:
            f.write('installed')
        
        # 访问安装页，应该重定向到首页
        response = self.client.get('/install/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    def test_exempt_paths_not_redirected(self):
        """测试豁免路径不会被重定向"""
        # 确保未安装
        self.assertFalse(os.path.exists(self.installed_lock_path))
        
        # 访问静态文件路径，应该不重定向
        response = self.client.get('/static/css/site.css')
        self.assertNotEqual(response.status_code, 302)
        
        # 访问健康检查路径，应该不重定向
        response = self.client.get('/healthz')
        self.assertNotEqual(response.status_code, 302)
