"""
安全中间件
用于记录可疑请求、防止路径遍历攻击等
"""
import logging
from django.http import HttpResponseNotFound

logger = logging.getLogger('security')


class SecurityMonitorMiddleware:
    """安全监控中间件（监测可疑请求，不与 Django 内置 SecurityMiddleware 重名）"""

    # 可疑路径模式
    SUSPICIOUS_PATTERNS = [
        '/etc/passwd',
        '/etc/shadow',
        '/windows/system32',
        '/proc/self',
        '../',
        '..\\',
        '.env',
        'settings.py',
        'config.py',
        'secret',
        '.git',
        '.htaccess',
        'web.config',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """处理异常"""
        return None


def security_logger(get_response):
    """安全日志中间件"""

    def middleware(request):
        path = request.path.lower()

        # 检查是否是可疑路径
        is_suspicious = any(pattern in path for pattern in [
            '/etc/', '/windows/', '/proc/', '../', '..\\',
            '.env', 'settings.py', 'config.py', 'web.config'
        ])

        if is_suspicious:
            logger.warning(
                f"[安全警告] 可疑请求: {request.method} {request.path} "
                f"来自: {request.META.get('REMOTE_ADDR', 'unknown')} "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}"
            )

        response = get_response(request)
        return response

    return middleware


def custom_404_view(request, exception=None):
    """自定义404视图"""
    path = request.path.lower()

    # 检查是否是路径遍历尝试
    is_traversal_attempt = any(pattern in path for pattern in [
        '/etc/', '/windows/', '/proc/', '../', '..\\',
        '.env', 'settings.py'
    ])

    if is_traversal_attempt:
        logger.warning(f"[安全] 路径遍历尝试被阻止: {request.path}")
        # 对可疑请求返回简单的404，不暴露任何信息
        return HttpResponseNotFound(
            '<h1>404 Not Found</h1>',
            content_type='text/html',
            status=404
        )

    # 正常404请求，返回友好页面
    from django.shortcuts import render
    return render(request, '404.html', {'path': request.path}, status=404)


def custom_500_view(request):
    """自定义500视图"""
    from django.shortcuts import render
    return render(request, '500.html', status=500)
