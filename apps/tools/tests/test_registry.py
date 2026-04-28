"""
工具注册表测试

测试覆盖:
- ToolRegistry: 发现工具、获取工具、缓存管理
"""

import pytest
from django.core.cache import cache
from apps.tools.registry import ToolRegistry, registry


@pytest.mark.django_db
class TestToolRegistry:
    """工具注册表测试"""

    def test_registry_singleton(self):
        """测试注册表单例"""
        # 全局注册表应该是单例
        from apps.tools.registry import registry as global_registry
        assert global_registry is registry

    def test_registry_discover_tools(self):
        """测试工具发现"""
        # 创建新的注册表实例
        test_registry = ToolRegistry()
        test_registry.discover_tools()

        # 应该发现一些工具
        assert len(test_registry.tools) > 0
        assert test_registry._discovered is True

    def test_registry_get_tool(self):
        """测试获取工具"""
        # 获取一个已知的工具
        tool = registry.get_tool('hash')
        assert tool is not None
        assert tool.slug == 'hash'

    def test_registry_get_nonexistent_tool(self):
        """测试获取不存在的工具"""
        tool = registry.get_tool('nonexistent-tool')
        assert tool is None

    def test_registry_get_all_tools(self):
        """测试获取所有工具"""
        tools = registry.get_all_tools()
        assert len(tools) > 0
        # 应该包含一些已知工具
        tool_slugs = [t.slug for t in tools]
        assert 'hash' in tool_slugs
        assert 'base64' in tool_slugs or 'base64-codec' in tool_slugs

    def test_registry_get_tools_by_category(self):
        """测试按分类获取工具"""
        categorized = registry.get_tools_by_category()
        assert len(categorized) > 0
        # 应该有一些分类
        assert 'encrypt' in categorized or 'ENCRYPT' in str(categorized)

    def test_registry_get_categories_with_tools(self):
        """测试获取包含工具的分类"""
        categories = registry.get_categories_with_tools()
        assert len(categories) > 0
        # 每个分类应该有必要的字段
        for category in categories:
            assert 'key' in category
            assert 'name' in category
            assert 'tools' in category
            assert 'count' in category
            assert category['count'] > 0

    def test_registry_caching(self):
        """测试注册表缓存"""
        # 清除缓存
        registry.clear_cache()

        # 第一次获取应该发现工具
        tools1 = registry.get_all_tools()
        assert len(tools1) > 0

        # 第二次获取应该命中缓存
        tools2 = registry.get_all_tools()
        assert tools1 == tools2

    def test_registry_reset_discovered(self):
        """测试重置发现状态"""
        # 先发现工具
        registry.discover_tools()
        initial_count = len(registry.tools)

        # 重置
        registry.reset_discovered()

        # 应该清除所有状态
        assert registry._discovered is False
        assert len(registry.tools) == 0

        # 重新发现应该恢复
        registry.discover_tools()
        assert len(registry.tools) == initial_count

    def test_registry_clear_cache(self):
        """测试清除缓存"""
        # 设置一些缓存
        cache.set('tools:all_tools', 'test_value', 300)
        cache.set('tools:by_category', 'test_value', 300)

        # 清除缓存
        registry.clear_cache()

        # 验证缓存已被清除
        assert cache.get('tools:all_tools') is None
        assert cache.get('tools:by_category') is None


@pytest.mark.django_db
class TestToolRegistryIntegration:
    """工具注册表集成测试"""

    def test_registry_with_real_tools(self):
        """测试注册表与真实工具"""
        # 获取所有工具
        tools = registry.get_all_tools()
        assert len(tools) > 0

        # 检查每个工具都有必要的属性
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'slug')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'category')
            assert hasattr(tool, 'handle')

    def test_registry_tool_categories(self):
        """测试工具分类"""
        # 获取分类
        categories = registry.get_categories_with_tools()
        assert len(categories) > 0

        # 检查分类结构
        for category in categories:
            assert 'key' in category
            assert 'name' in category
            assert 'icon' in category
            assert 'color' in category
            assert 'description' in category
            assert 'tools' in category
            assert 'count' in category
            assert category['count'] > 0

    def test_registry_tool_slug_uniqueness(self):
        """测试工具 slug 唯一性"""
        tools = registry.get_all_tools()
        slugs = [t.slug for t in tools]
        # 所有 slug 应该唯一
        assert len(slugs) == len(set(slugs))

    def test_registry_tool_handle_method(self):
        """测试工具 handle 方法"""
        # 获取一个工具
        tool = registry.get_tool('hash')
        assert tool is not None

        # 检查 handle 方法存在
        assert hasattr(tool, 'handle')
        assert callable(tool.handle)

    def test_registry_tool_form_class(self):
        """测试工具表单类"""
        # 获取一个工具
        tool = registry.get_tool('hash')
        assert tool is not None

        # 检查表单类存在
        assert hasattr(tool, 'form_class')
        if tool.form_class:
            # 如果有表单类，应该可以实例化
            form = tool.get_form()
            assert form is not None
