from typing import ClassVar

from django import forms

from .categories import TOOL_CATEGORIES, ToolCategory


class BaseTool:
    """工具基类"""

    name: ClassVar[str] = "工具"
    slug: ClassVar[str] = "tool"
    description: ClassVar[str] = "工具描述"
    icon: ClassVar[str] = "bi-tools"
    category: ClassVar[str] = ToolCategory.OTHER
    template_name: ClassVar[str] = "tools/tool_detail.html"
    form_class: ClassVar[type[forms.Form] | None] = None

    def get_form(self, data=None, files=None):
        """获取表单实例"""
        if self.form_class:
            return self.form_class(data, files)
        return None

    def get_context(self, request, form=None, result=None):
        """获取上下文数据"""
        return {
            "tool": self,
            "form": form,
            "result": result,
            "category_info": TOOL_CATEGORIES.get(self.category, TOOL_CATEGORIES[ToolCategory.OTHER]),
        }

    def handle(self, request, form):
        """处理工具逻辑，返回结果"""
        raise NotImplementedError("子类必须实现 handle 方法")
