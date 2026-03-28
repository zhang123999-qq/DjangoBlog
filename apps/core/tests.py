from django.test import TestCase
from django.urls import reverse


class CoreTestCase(TestCase):
    def test_healthz_view(self):
        """测试健康检查视图返回200和健康检查详情"""
        # healthz路径在安装中间件的豁免列表中，不需要创建安装锁文件
        response = self.client.get(reverse('core:healthz'))
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload.get('status'), 'healthy')
        self.assertIn('checks', payload)
        self.assertTrue(payload['checks'].get('database'))
        self.assertTrue(payload['checks'].get('cache'))
        self.assertIn('duration_ms', payload)
        self.assertIn('version', payload)
