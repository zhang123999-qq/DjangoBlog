import importlib
import logging
import os
from django.core.cache import cache
from .base_tool import BaseTool
from .categories import TOOL_CATEGORIES, CATEGORY_ORDER

logger = logging.getLogger(__name__)

# 缓存 key
TOOLS_CACHE_KEY = "tools:all_tools"
TOOLS_CATEGORY_CACHE_KEY = "tools:by_category"
CACHE_TIMEOUT = 3600  # 1 小时


class ToolRegistry:
    """工具注册表（优化版：懒加载 + 缓存）"""

    def __init__(self):
        self.tools = {}
        self._discovered = False

    def discover_tools(self):
        """自动发现工具类"""
        if self._discovered:
            return

        # 工具模块目录
        tool_modules_dir = os.path.join(os.path.dirname(__file__), "tool_modules")
        if not os.path.exists(tool_modules_dir):
            os.makedirs(tool_modules_dir)
            self._discovered = True
            return

        # 遍历工具模块文件
        for filename in os.listdir(tool_modules_dir):
            if filename.endswith(".py") and not filename.startswith("__init__"):
                module_name = f"apps.tools.tool_modules.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    # 查找 BaseTool 子类
                    for name, obj in module.__dict__.items():
                        if isinstance(obj, type) and issubclass(obj, BaseTool) and obj is not BaseTool:
                            tool_instance = obj()
                            slug = tool_instance.slug
                            if slug in self.tools:
                                raise ValueError(f"工具 slug '{slug}' 重复")
                            self.tools[slug] = tool_instance
                except Exception as e:
                    logger.warning(f"加载工具模块 {module_name} 失败: {e}")

        self._discovered = True

    def get_tool(self, slug):
        """
        根据 slug 获取工具（懒加载）

        性能优化：
        - 只加载请求的工具
        - 不触发全量发现
        """
        # 先检查内存缓存
        if slug in self.tools:
            return self.tools[slug]

        # 触发发现（只执行一次）
        if not self._discovered:
            self.discover_tools()

        return self.tools.get(slug)

    def get_all_tools(self):
        """
        获取所有工具（带缓存）

        性能优化：
        - 使用 Django 缓存
        - 避免每次请求都发现工具
        - 支持手动刷新
        """
        # 尝试从缓存获取
        cached_tools = cache.get(TOOLS_CACHE_KEY)
        if cached_tools is not None:
            return cached_tools

        # 缓存未命中，发现工具
        if not self._discovered:
            self.discover_tools()

        tools = list(self.tools.values())

        # 写入缓存
        cache.set(TOOLS_CACHE_KEY, tools, CACHE_TIMEOUT)

        return tools

    def get_tools_by_category(self):
        """按分类获取工具（带缓存）"""
        # 尝试从缓存获取
        cached = cache.get(TOOLS_CATEGORY_CACHE_KEY)
        if cached is not None:
            return cached

        if not self._discovered:
            self.discover_tools()

        # 按分类组织工具
        categorized = {}
        for tool in self.tools.values():
            cat = tool.category
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(tool)

        # 对每个分类内的工具按名称排序
        for cat in categorized:
            categorized[cat].sort(key=lambda t: t.name)

        # 写入缓存
        cache.set(TOOLS_CATEGORY_CACHE_KEY, categorized, CACHE_TIMEOUT)

        return categorized

    def get_categories_with_tools(self):
        """获取包含工具的分类列表（按排序顺序）"""
        categorized = self.get_tools_by_category()

        result = []
        for cat_key in CATEGORY_ORDER:
            if cat_key in categorized and categorized[cat_key]:
                cat_info = TOOL_CATEGORIES.get(cat_key, {})
                result.append(
                    {
                        "key": cat_key,
                        "name": cat_info.get("name", cat_key),
                        "icon": cat_info.get("icon", "bi-folder"),
                        "color": cat_info.get("color", "#999"),
                        "description": cat_info.get("description", ""),
                        "tools": categorized[cat_key],
                        "count": len(categorized[cat_key]),
                    }
                )

        return result

    def clear_cache(self):
        """清除工具缓存"""
        cache.delete(TOOLS_CACHE_KEY)
        cache.delete(TOOLS_CATEGORY_CACHE_KEY)
        logger.info("工具缓存已清除")

    def reset_discovered(self):
        """重置发现状态并清除缓存"""
        self._discovered = False
        self.tools = {}
        self.clear_cache()


# 全局工具注册表实例
registry = ToolRegistry()

# 导出为 tool_registry 以保持兼容性
tool_registry = registry
