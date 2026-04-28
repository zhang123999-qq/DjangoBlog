"""
工具配置模型测试

测试覆盖:
- ToolConfig: 创建、slug自动生成、缓存清除
"""

import pytest
from django.core.cache import cache
from apps.tools.models import ToolConfig


@pytest.mark.django_db
class TestToolConfigModel:
    """工具配置模型测试"""

    def test_create_toolconfig(self):
        """测试创建工具配置"""
        config = ToolConfig.objects.create(
            name='测试工具',
            slug='test-tool',
            is_enabled=True,
            sort_order=1
        )
        assert config.name == '测试工具'
        assert config.slug == 'test-tool'
        assert config.is_enabled is True
        assert config.sort_order == 1

    def test_toolconfig_slug_auto_generate(self):
        """测试 slug 自动生成"""
        config = ToolConfig.objects.create(name='哈希计算工具')
        assert config.slug == '哈希计算工具'  # slugify 会处理中文

    def test_toolconfig_str(self):
        """测试字符串表示"""
        config = ToolConfig.objects.create(name='AES加密')
        assert str(config) == 'AES加密'

    def test_toolconfig_ordering(self):
        """测试排序"""
        # 创建不同排序的工具配置
        ToolConfig.objects.create(name='工具C', sort_order=3)
        ToolConfig.objects.create(name='工具A', sort_order=1)
        ToolConfig.objects.create(name='工具B', sort_order=2)

        configs = list(ToolConfig.objects.all())
        assert configs[0].name == '工具A'
        assert configs[1].name == '工具B'
        assert configs[2].name == '工具C'

    def test_toolconfig_cache_clear(self):
        """测试保存时清除缓存"""
        # 设置一些缓存
        cache.set('toolconfig_test-tool', 'old_value', 300)
        cache.set('tool_list', 'old_list', 300)
        cache.set('tool_categories', 'old_categories', 300)

        # 创建工具配置（应该清除缓存）
        ToolConfig.objects.create(
            name='测试工具',
            slug='test-tool'
        )

        # 验证缓存已被清除
        assert cache.get('toolconfig_test-tool') is None
        assert cache.get('tool_list') is None
        assert cache.get('tool_categories') is None

    def test_toolconfig_update_cache_clear(self):
        """测试更新时清除缓存"""
        # 创建工具配置
        config = ToolConfig.objects.create(
            name='测试工具',
            slug='test-tool'
        )

        # 设置缓存
        cache.set('toolconfig_test-tool', 'old_value', 300)

        # 更新工具配置（应该清除缓存）
        config.name = '更新后的工具'
        config.save()

        # 验证缓存已被清除
        assert cache.get('toolconfig_test-tool') is None

    def test_toolconfig_is_enabled_default(self):
        """测试默认启用状态"""
        config = ToolConfig.objects.create(name='新工具')
        assert config.is_enabled is True

    def test_toolconfig_sort_order_default(self):
        """测试默认排序"""
        config = ToolConfig.objects.create(name='新工具')
        assert config.sort_order == 0

    def test_toolconfig_unique_slug(self):
        """测试 slug 唯一性"""
        ToolConfig.objects.create(name='工具1', slug='unique-slug')
        # 同名工具应该因为 slug 冲突而失败
        with pytest.raises(Exception):
            ToolConfig.objects.create(name='工具2', slug='unique-slug')


@pytest.mark.django_db
class TestToolConfigProperties:
    """工具配置属性测试"""

    def test_toolconfig_enabled_status(self):
        """测试启用状态"""
        config = ToolConfig.objects.create(
            name='启用工具',
            is_enabled=True
        )
        assert config.is_enabled is True

        config.is_enabled = False
        config.save()
        assert config.is_enabled is False

    def test_toolconfig_disabled_status(self):
        """测试禁用状态"""
        config = ToolConfig.objects.create(
            name='禁用工具',
            is_enabled=False
        )
        assert config.is_enabled is False

    def test_toolconfig_sort_order(self):
        """测试排序顺序"""
        ToolConfig.objects.create(name='工具1', sort_order=10)
        ToolConfig.objects.create(name='工具2', sort_order=5)

        configs = list(ToolConfig.objects.all())
        assert configs[0].name == '工具2'  # sort_order=5 排在前面
        assert configs[1].name == '工具1'  # sort_order=10 排在后面
