"""
工具 API 视图

提供工具列表、详情（含表单字段定义）、执行三个端点。
前端 DynamicFormGenerator 依赖字段字典来动态渲染表单。
"""

import logging
from typing import Any, Dict, List

from django import forms
from django.http import HttpRequest
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.api.response import APIResponse
from apps.tools.categories import TOOL_CATEGORIES, ToolCategory
from apps.tools.models import ToolConfig
from apps.tools.registry import registry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 表单字段 → JSON 字典序列化
# ---------------------------------------------------------------------------

# Django 内置 widget → 前端组件类型映射
WIDGET_TYPE_MAP = {
    "TextInput": "text",
    "Textarea": "textarea",
    "PasswordInput": "password",
    "EmailInput": "email",
    "URLInput": "url",
    "NumberInput": "number",
    "HiddenInput": "hidden",
    "DateInput": "date",
    "DateTimeInput": "datetime",
    "TimeInput": "time",
    "CheckboxInput": "checkbox",
    "Select": "select",
    "NullBooleanSelect": "select",
    "SelectMultiple": "select_multiple",
    "RadioSelect": "radio",
    "CheckboxSelectMultiple": "checkbox_multiple",
    "FileInput": "file",
    "ClearableFileInput": "file",
    "RangeInput": "range",
}


def _get_widget_type(widget) -> str:
    """从 widget 实例推断前端组件类型"""
    widget_class_name = widget.__class__.__name__

    # 先按 widget 类名精确匹配
    if widget_class_name in WIDGET_TYPE_MAP:
        return WIDGET_TYPE_MAP[widget_class_name]

    # 回退：遍历 MRO 链查找父类匹配
    for cls in type(widget).__mro__:
        if cls.__name__ in WIDGET_TYPE_MAP:
            return WIDGET_TYPE_MAP[cls.__name__]

    return "text"


def _get_widget_attrs(widget) -> Dict[str, Any]:
    """提取 widget 的 HTML 属性"""
    attrs = dict(widget.attrs)
    # 清理不可序列化的值
    cleaned: Dict[str, Any] = {}
    for k, v in attrs.items():
        if isinstance(v, (str, int, float, bool, type(None))):
            cleaned[k] = v
        elif isinstance(v, (list, tuple)):
            cleaned[k] = [str(i) for i in v]
        else:
            cleaned[k] = str(v)
    return cleaned


def serialize_form_fields(form_class: type[forms.Form]) -> List[Dict[str, Any]]:
    """
    将 Django Form 类的字段序列化为 JSON 字典列表。

    每个字段输出:
    {
        "name": "text",
        "label": "文本内容",
        "type": "textarea",          // 前端组件类型
        "required": true,
        "help_text": "",
        "attrs": {"rows": 10, "placeholder": "..."},
        "choices": [...],            // 仅 ChoiceField
        "max_length": 1000,          // 仅 CharField
        "min_value": 0,              // 仅 IntegerField
        "max_value": 100,            // 仅 IntegerField
        "initial": "...",            // 默认值
    }
    """
    fields = []
    form_instance = form_class()  # 实例化以获取 widget 信息

    for name, field in form_instance.fields.items():
        widget = field.widget

        field_dict: Dict[str, Any] = {
            "name": name,
            "label": str(field.label or name),
            "type": _get_widget_type(widget),
            "required": field.required,
            "help_text": str(field.help_text or ""),
            "attrs": _get_widget_attrs(widget),
            "initial": field.initial if field.initial is not None else None,
        }

        # ChoiceField 特有
        if isinstance(field, forms.ChoiceField):
            field_dict["choices"] = [
                {"value": str(val), "label": str(lbl)}
                for val, lbl in field.choices
            ]

        # CharField 特有
        if isinstance(field, forms.CharField):
            if field.max_length is not None:
                field_dict["max_length"] = field.max_length
            if field.min_length is not None:
                field_dict["min_value"] = field.min_length

        # IntegerField 特有
        if isinstance(field, forms.IntegerField):
            if field.min_value is not None:
                field_dict["min_value"] = field.min_value
            if field.max_value is not None:
                field_dict["max_value"] = field.max_value

        # FloatField 特有
        if isinstance(field, forms.FloatField):
            if field.min_value is not None:
                field_dict["min_value"] = field.min_value
            if field.max_value is not None:
                field_dict["max_value"] = field.max_value

        # FileField 特有
        if isinstance(field, forms.FileField):
            if hasattr(field, "max_length") and field.max_length:
                field_dict["max_length"] = field.max_length

        fields.append(field_dict)

    return fields


# ---------------------------------------------------------------------------
# 序列化工具元数据
# ---------------------------------------------------------------------------

def _serialize_tool(tool) -> Dict[str, Any]:
    """将工具实例序列化为 API 响应字典"""
    cat_info = TOOL_CATEGORIES.get(tool.category, TOOL_CATEGORIES[ToolCategory.OTHER])
    return {
        "slug": tool.slug,
        "name": tool.name,
        "description": tool.description,
        "icon": tool.icon,
        "category": tool.category,
        "category_name": cat_info.get("name", tool.category),
        "category_icon": cat_info.get("icon", "bi-folder"),
        "category_color": cat_info.get("color", "#999"),
        "has_form": tool.form_class is not None,
        "fields": serialize_form_fields(tool.form_class) if tool.form_class else [],
    }


def _serialize_tool_brief(tool) -> Dict[str, Any]:
    """轻量序列化（列表页用，不含字段详情）"""
    cat_info = TOOL_CATEGORIES.get(tool.category, TOOL_CATEGORIES[ToolCategory.OTHER])
    return {
        "slug": tool.slug,
        "name": tool.name,
        "description": tool.description,
        "icon": tool.icon,
        "category": tool.category,
        "category_name": cat_info.get("name", tool.category),
        "category_icon": cat_info.get("icon", "bi-folder"),
        "category_color": cat_info.get("color", "#999"),
        "has_form": tool.form_class is not None,
    }


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([AllowAny])
def tool_list_api(request: HttpRequest):
    """
    GET /api/tools/

    返回按分类组织的工具列表（轻量序列化，不含字段详情）。
    """
    categories_with_tools = registry.get_categories_with_tools()

    result = []
    for cat in categories_with_tools:
        result.append({
            "key": cat["key"],
            "name": cat["name"],
            "icon": cat["icon"],
            "color": cat["color"],
            "description": cat["description"],
            "count": cat["count"],
            "tools": [_serialize_tool_brief(t) for t in cat["tools"]],
        })

    return APIResponse.success(data=result)


@api_view(["GET"])
@permission_classes([AllowAny])
def tool_detail_api(request: HttpRequest, slug: str):
    """
    GET /api/tools/<slug>/

    返回工具详情，包含完整的表单字段定义（DynamicFormGenerator 依赖此数据）。
    """
    tool = registry.get_tool(slug)
    if not tool:
        return APIResponse.not_found(f"工具 '{slug}' 不存在")

    # 检查工具是否启用
    try:
        config = ToolConfig.objects.get(slug=slug)
        if not config.is_enabled:
            return APIResponse.forbidden("该工具已被管理员禁用")
    except ToolConfig.DoesNotExist:
        pass  # 无配置记录视为默认启用

    return APIResponse.success(data=_serialize_tool(tool))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tool_execute_api(request: HttpRequest, slug: str):
    """
    POST /api/tools/<slug>/execute/

    执行工具。请求体为表单字段的 JSON 键值对。
    文件上传字段通过 multipart/form-data 传递。

    返回格式与 apps/api/response.py 对齐:
    成功: {"code": 200, "success": true, "data": {...}}
    失败: {"code": 400, "success": false, "message": "...", "errors": {...}}
    """
    tool = registry.get_tool(slug)
    if not tool:
        return APIResponse.not_found(f"工具 '{slug}' 不存在")

    # 检查工具是否启用
    try:
        config = ToolConfig.objects.get(slug=slug)
        if not config.is_enabled:
            return APIResponse.forbidden("该工具已被管理员禁用")
    except ToolConfig.DoesNotExist:
        pass

    if not tool.form_class:
        return APIResponse.bad_request("该工具不支持表单提交")

    # 构造表单实例（区分文件上传和普通 JSON）
    has_file_fields = any(
        isinstance(f, (forms.FileField, forms.ImageField))
        for f in tool.form_class().fields.values()
    )

    if has_file_fields and request.FILES:
        form = tool.get_form(data=request.POST, files=request.FILES)
    else:
        form = tool.get_form(data=request.data)

    if not form.is_valid():
        # 将 Django 表单错误转为字段级错误字典
        errors = {}
        for field_name, error_list in form.errors.items():
            errors[field_name] = [str(e) for e in error_list]
        return APIResponse.bad_request(message="表单验证失败", errors=errors)

    try:
        result = tool.handle(request, form)
    except Exception:
        logger.exception("工具 %s 执行异常", slug)
        return APIResponse.server_error("工具执行失败，请稍后重试")

    if isinstance(result, dict) and "error" in result:
        return APIResponse.error(message=result["error"], code=400)

    return APIResponse.success(data=result)
