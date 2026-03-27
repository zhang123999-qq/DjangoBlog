"""
安全头中间件

功能：
- Content Security Policy (CSP)
- HSTS
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
"""

from django.conf import settings


class CSPMiddleware:
    """
    Content Security Policy 中间件

    轻量级实现，无需 django-csp 依赖
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # 从 settings 加载 CSP 配置
        self.csp_enabled = getattr(settings, 'CSP_ENABLED', False)

        if self.csp_enabled:
            self.directives = self._build_directives()

    def __call__(self, request):
        response = self.get_response(request)

        if self.csp_enabled:
            # 添加 CSP 头
            response['Content-Security-Policy'] = self.directives

        return response

    def _build_directives(self):
        """构建 CSP 指令字符串"""
        directives = []

        # 读取配置，使用默认值
        configs = {
            'default-src': getattr(settings, 'CSP_DEFAULT_SRC', ["'self'"]),
            'script-src': getattr(settings, 'CSP_SCRIPT_SRC', ["'self'"]),
            'style-src': getattr(settings, 'CSP_STYLE_SRC', ["'self'"]),
            'img-src': getattr(settings, 'CSP_IMG_SRC', ["'self'"]),
            'font-src': getattr(settings, 'CSP_FONT_SRC', ["'self'"]),
            'connect-src': getattr(settings, 'CSP_CONNECT_SRC', ["'self'"]),
            'frame-ancestors': getattr(settings, 'CSP_FRAME_ANCESTORS', ["'self'"]),
            'base-uri': getattr(settings, 'CSP_BASE_URI', ["'self'"]),
            'form-action': getattr(settings, 'CSP_FORM_ACTION', ["'self'"]),
        }

        for directive, sources in configs.items():
            if sources:
                sources_str = ' '.join(sources)
                directives.append(f"{directive} {sources_str}")

        return '; '.join(directives)


class SecurityHeadersMiddleware:
    """
    综合安全头中间件

    添加多种安全相关的 HTTP 头
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.debug = settings.DEBUG

    def __call__(self, request):
        response = self.get_response(request)

        # X-Content-Type-Options: 防止 MIME 类型嗅探
        response['X-Content-Type-Options'] = 'nosniff'

        # X-XSS-Protection: XSS 过滤（已弃用但仍有效）
        response['X-XSS-Protection'] = '1; mode=block'

        # X-Frame-Options: 防止点击劫持
        if hasattr(settings, 'X_FRAME_OPTIONS'):
            response['X-Frame-Options'] = settings.X_FRAME_OPTIONS
        else:
            response['X-Frame-Options'] = 'DENY'

        # Referrer-Policy: 控制 Referer 头
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions-Policy: 限制浏览器功能
        response['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=()'
        )

        # HSTS: 仅在生产环境
        if not self.debug and hasattr(settings, 'SECURE_HSTS_SECONDS'):
            max_age = settings.SECURE_HSTS_SECONDS
            if max_age > 0:
                hsts_value = f'max-age={max_age}'
                if getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False):
                    hsts_value += '; includeSubDomains'
                if getattr(settings, 'SECURE_HSTS_PRELOAD', False):
                    hsts_value += '; preload'
                response['Strict-Transport-Security'] = hsts_value

        return response
