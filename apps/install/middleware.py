import os
from django.shortcuts import redirect


class InstallMiddleware:
    """安装中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 检查是否已安装
        is_installed = os.path.exists('installed.lock')
        
        # 不需要拦截的路径
        exempt_paths = [
            '/static/',
            '/media/',
            '/healthz',
            '/favicon.ico',
            '/robots.txt',
            '/install/'
        ]
        
        # 检查当前路径是否需要拦截
        current_path = request.path
        should_exempt = any(current_path.startswith(path) for path in exempt_paths)
        
        # 未安装且不在豁免列表中，重定向到安装页
        if not is_installed and not should_exempt:
            return redirect('/install/')
        
        # 已安装且访问安装页，重定向到首页
        if is_installed and current_path.startswith('/install/'):
            return redirect('/')
        
        response = self.get_response(request)
        return response