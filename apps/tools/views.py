import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from .registry import registry
from .models import ToolConfig
from .categories import TOOL_CATEGORIES

logger = logging.getLogger(__name__)


@cache_page(300)  # 缓存 5 分钟
def tool_list(request):
    """工具列表视图（公开访问）"""
    # 获取分类后的工具（使用 registry 内部缓存）
    categories = registry.get_categories_with_tools()

    # 获取所有工具（兼容旧版）
    all_tools = registry.get_all_tools()

    # 记录日志（开发调试使用）
    logger.debug(f"工具列表视图：发现 {len(all_tools)} 个工具")

    # 渲染响应
    return render(
        request,
        "tools/tool_list.html",
        {
            "categories": categories,
            "tools": all_tools,
            "total_tools": len(all_tools),
            "enabled_tools_count": len(all_tools),
            "category_info": TOOL_CATEGORIES,
        },
    )


@login_required
def tool_detail(request, tool_slug):
    """工具详情视图（需要登录）"""
    # 获取工具
    tool = registry.get_tool(tool_slug)
    if not tool:
        return render(
            request,
            "tools/tool_list.html",
            {
                "error": f"工具 '{tool_slug}' 不存在",
                "tools": registry.get_all_tools(),
            },
        )

    # 使用缓存检查工具是否启用（避免重复数据库查询）
    cache_key = f"tool_config_{tool_slug}"
    tool_config = cache.get(cache_key)
    if tool_config is None:
        tool_config = ToolConfig.objects.filter(slug=tool_slug).first()
        cache.set(cache_key, tool_config, 300)  # 缓存 5 分钟

    if tool_config and not tool_config.is_enabled:
        return render(
            request,
            "tools/tool_list.html",
            {
                "error": f"工具 '{tool.name}' 已被禁用",
                "tools": registry.get_all_tools(),
            },
        )

    form = tool.get_form()
    result = None
    error_message = None

    if request.method == "POST":
        form = tool.get_form(request.POST)
        if form.is_valid():
            try:
                result = tool.handle(request, form)
            except Exception as e:
                # 捕获工具执行异常
                logger.error(f"工具 {tool_slug} 执行失败: {e}", exc_info=True)
                error_message = f"工具执行失败: {str(e)}"
        else:
            # 表单验证失败，收集错误信息
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(f"{field}: {error}")
            error_message = "; ".join(errors) if errors else "输入数据验证失败"

    context = tool.get_context(request, form, result)
    context["error_message"] = error_message
    return render(request, tool.template_name, context)


@login_required
def my_ip_json(request):
    """返回访问者 IP（供 NAT 工具前端回退获取公网 IP）。"""
    tool = registry.get_tool("ip-query")
    if not tool:
        return JsonResponse({"ok": False, "error": "my-ip tool not found"}, status=404)

    ip = tool._get_client_ip(request)
    return JsonResponse({"ok": True, "ip": ip})
