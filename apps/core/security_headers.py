"""
安全头中间件

功能：
- Content Security Policy (CSP) with nonce support
- HSTS
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
"""

import secrets
from django.conf import settings


class CSPMiddleware:
    """
    Content Security Policy 中间件

    轻量级实现，无需 django-csp 依赖。
    支持 per-request nonce 以替换 unsafe-inline。
    """

    NONCE_LENGTH = 16  # 16 bytes = 32 hex chars

    def __init__(self, get_response):
        self.get_response = get_response

        # 从 settings 加载 CSP 配置
        self.csp_enabled = getattr(settings, "CSP_ENABLED", False)
        self.nonce_enabled = getattr(settings, "CSP_NONCE_ENABLED", False)

    def __call__(self, request):
        # 生成 per-request nonce（无论 CSP 是否启用，模板可能需要）
        nonce = secrets.token_hex(self.NONCE_LENGTH)
        request.csp_nonce = nonce

        response = self.get_response(request)

        if self.csp_enabled:
            directives = self._build_directives(nonce if self.nonce_enabled else None)
            response["Content-Security-Policy"] = directives

        return response

    def _build_directives(self, nonce=None):
        """构建 CSP 指令字符串"""
        directives = []

        # 读取配置，使用默认值
        script_src = list(getattr(settings, "CSP_SCRIPT_SRC", ["'self'"]))
        style_src = list(getattr(settings, "CSP_STYLE_SRC", ["'self'"]))

        # 如果启用了 nonce，替换 unsafe-inline
        if nonce:
            nonce_str = f"'nonce-{nonce}'"
            if nonce_str not in script_src:
                script_src.append(nonce_str)
            if "'unsafe-inline'" in script_src:
                script_src.remove("'unsafe-inline'")
            if nonce_str not in style_src:
                style_src.append(nonce_str)
            if "'unsafe-inline'" in style_src:
                style_src.remove("'unsafe-inline'")

        configs = {
            "default-src": getattr(settings, "CSP_DEFAULT_SRC", ["'self'"]),
            "script-src": script_src,
            "style-src": style_src,
            "img-src": getattr(settings, "CSP_IMG_SRC", ["'self'"]),
            "font-src": getattr(settings, "CSP_FONT_SRC", ["'self'"]),
            "connect-src": getattr(settings, "CSP_CONNECT_SRC", ["'self'"]),
            "frame-ancestors": getattr(settings, "CSP_FRAME_ANCESTORS", ["'self'"]),
            "base-uri": getattr(settings, "CSP_BASE_URI", ["'self'"]),
            "form-action": getattr(settings, "CSP_FORM_ACTION", ["'self'"]),
        }

        for directive, sources in configs.items():
            if sources:
                sources_str = " ".join(sources)
                directives.append(f"{directive} {sources_str}")

        return "; ".join(directives)


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

        # ========================================
        # 基础安全头
        # ========================================

        # X-Content-Type-Options: 防止 MIME 类型嗅探
        response["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: XSS 过滤（已弃用但仍有效，旧浏览器兼容）
        response["X-XSS-Protection"] = "1; mode=block"

        # X-Frame-Options: 防止点击劫持
        if hasattr(settings, "X_FRAME_OPTIONS"):
            response["X-Frame-Options"] = settings.X_FRAME_OPTIONS
        else:
            response["X-Frame-Options"] = "DENY"

        # Referrer-Policy: 控制 Referer 头
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # ========================================
        # 方案A：基础增强（无兼容性风险）
        # ========================================

        # X-Permitted-Cross-Domain-Policies: 禁止 Flash/PDF 跨域访问
        response["X-Permitted-Cross-Domain-Policies"] = "none"

        # X-Download-Options: 防止 IE 直接打开下载文件
        response["X-Download-Options"] = "noopen"

        # Cross-Origin-Opener-Policy: 隔离浏览上下文（允许弹窗，兼容 OAuth）
        response["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"

        # Cross-Origin-Resource-Policy: 防止跨域资源加载
        response["Cross-Origin-Resource-Policy"] = "same-site"

        # Permissions-Policy: 限制浏览器功能（扩展版）
        response["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "display-capture=(), "
            "encrypted-media=(), "
            "fullscreen=(self), "  # 允许自己全屏
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "midi=(), "
            "payment=(), "
            "usb=()"
        )

        # ========================================
        # 敏感页面缓存控制
        # ========================================
        sensitive_paths = ["/accounts/", "/admin/", "/api/auth/"]
        if any(request.path.startswith(path) for path in sensitive_paths):
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        # ========================================
        # HSTS: 仅在生产环境
        # ========================================
        if not self.debug and hasattr(settings, "SECURE_HSTS_SECONDS"):
            max_age = settings.SECURE_HSTS_SECONDS
            if max_age > 0:
                hsts_value = f"max-age={max_age}"
                if getattr(settings, "SECURE_HSTS_INCLUDE_SUBDOMAINS", False):
                    hsts_value += "; includeSubDomains"
                if getattr(settings, "SECURE_HSTS_PRELOAD", False):
                    hsts_value += "; preload"
                response["Strict-Transport-Security"] = hsts_value

        return response
