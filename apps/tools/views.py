import logging
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from .registry import registry
from .models import ToolConfig
from .categories import TOOL_CATEGORIES

logger = logging.getLogger(__name__)


@cache_page(60)  # 缓存 1 分钟
def tool_list(request):
    """工具列表视图"""
    # 获取分类后的工具（使用 registry 内部缓存）
    categories = registry.get_categories_with_tools()

    # 获取所有工具（兼容旧版）
    all_tools = registry.get_all_tools()

    # 记录日志（开发调试使用）
    logger.debug(f'工具列表视图：发现 {len(all_tools)} 个工具')

    # 渲染响应
    return render(request, 'tools/tool_list.html', {
        'categories': categories,
        'tools': all_tools,
        'total_tools': len(all_tools),
        'enabled_tools_count': len(all_tools),
        'category_info': TOOL_CATEGORIES,
    })


def tool_detail(request, tool_slug):
    """工具详情视图"""
    # 获取工具
    tool = registry.get_tool(tool_slug)
    if not tool:
        return render(request, 'tools/tool_list.html', {
            'error': f"工具 '{tool_slug}' 不存在",
            'tools': registry.get_all_tools(),
        })

    # 检查工具是否启用
    tool_config = ToolConfig.objects.filter(slug=tool_slug).first()
    if tool_config and not tool_config.is_enabled:
        return render(request, 'tools/tool_list.html', {
            'error': f"工具 '{tool.name}' 已被禁用",
            'tools': registry.get_all_tools(),
        })

    form = tool.get_form()
    result = None

    if request.method == 'POST':
        form = tool.get_form(request.POST)
        if form.is_valid():
            result = tool.handle(request, form)

    context = tool.get_context(request, form, result)
    return render(request, tool.template_name, context)
