"""
工具栏应用视图模块

处理工具相关的HTTP请求，包括：
- 工具列表展示
- 工具详情/执行
- 工具分类筛选

Author: zhang123999-qq
Date: 2026-03-20
"""

import logging
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .registry import registry
from .models import ToolConfig

logger = logging.getLogger(__name__)


def tool_list(request):
    """工具列表视图"""
    # 重置工具发现状态，确保发现所有工具
    registry.reset_discovered()
    
    # 获取所有工具
    all_tools = registry.get_all_tools()
    
    # 直接使用所有工具，不进行过滤
    # 这样可以确保所有工具都能显示
    tools = all_tools
    
    # 记录日志（开发调试使用）
    logger.debug(f'工具列表视图：发现 {len(tools)} 个工具')
    for i, tool in enumerate(tools, 1):
        logger.debug(f'{i}. {tool.name} ({tool.slug})')
    
    # 渲染响应
    response = render(request, 'tools/tool_list.html', {
        'tools': tools,
        'total_tools': len(tools),
        'enabled_tools_count': len(tools),
    })
    
    # 添加缓存控制头，确保浏览器每次都获取最新的页面
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['ETag'] = str(hash(str(tools)))
    
    return response


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
