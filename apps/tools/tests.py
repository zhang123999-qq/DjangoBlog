from django.test import TestCase
import os


class ToolsTestCase(TestCase):
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

    def test_tool_registry(self):
        """测试工具注册表"""
        from .registry import registry

        # 测试获取所有工具
        tools = registry.get_all_tools()
        self.assertGreater(len(tools), 0)

        # 测试获取单个工具
        base64_tool = registry.get_tool('base64-codec')
        self.assertIsNotNone(base64_tool)
        self.assertEqual(base64_tool.slug, 'base64-codec')

    def test_base64_codec_logic(self):
        """测试Base64编解码逻辑"""
        from .registry import registry

        # 获取Base64工具
        tool = registry.get_tool('base64-codec')
        self.assertIsNotNone(tool)

        # 测试编码功能
        form_data = {'action': 'encode', 'text': 'test'}
        form = tool.get_form(form_data)
        self.assertTrue(form.is_valid())

        # 测试解码功能
        form_data = {'action': 'decode', 'text': 'dGVzdA=='}
        form = tool.get_form(form_data)
        self.assertTrue(form.is_valid())

    def test_text_counter_logic(self):
        """测试文本计数逻辑"""
        from .registry import registry

        # 获取文本计数工具
        tool = registry.get_tool('text-counter')
        self.assertIsNotNone(tool)

        # 测试文本计数
        form_data = {'text': 'Hello world! This is a test.'}
        form = tool.get_form(form_data)
        self.assertTrue(form.is_valid())
