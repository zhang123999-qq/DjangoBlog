"""
安装中间件
"""
import os
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class InstallMiddleware:
    """安装中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.lock_path = BASE_DIR / 'installed.lock'
    
    def __call__(self, request):
        # 检查是否已安装（使用绝对路径）
        is_installed = self.lock_path.exists()
        
        # 不需要拦截的路径
        exempt_paths = [
            '/static/',
            '/media/',
            '/healthz',
            '/favicon.ico',
            '/robots.txt',
            '/install/',
            '/admin/',  # 允许访问管理后台
            '/accounts/login/',  # 允许登录
            '/accounts/logout/',  # 允许登出
        ]
        
        # 检查当前路径是否需要拦截
        current_path = request.path
        should_exempt = any(current_path.startswith(path) for path in exempt_paths)
        
        # 静态文件和媒体文件也不拦截
        if current_path.startswith('/static/') or current_path.startswith('/media/'):
            should_exempt = True
        
        # 未安装且不在豁免列表中，重定向到安装页
        if not is_installed and not should_exempt:
            from django.shortcuts import redirect
            return redirect('/install/')
        
        # 已安装且访问安装页，重定向到首页
        if is_installed and current_path.startswith('/install/'):
            from django.shortcuts import redirect
            return redirect('/')
        
        response = self.get_response(request)
        return response
