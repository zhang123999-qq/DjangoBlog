from django.test import TestCase
from django.urls import reverse
import os


class CoreTestCase(TestCase):
    def test_healthz_view(self):
        """测试健康检查视图返回200和ok"""
        # healthz路径在安装中间件的豁免列表中，不需要创建安装锁文件
        response = self.client.get(reverse('core:healthz'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
