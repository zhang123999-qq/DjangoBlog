"""
CSP Nonce 中间件

功能：
- 为每个请求生成唯一的 nonce 值
- 允许内联脚本和样式安全执行
- 移除 unsafe-inline 和 unsafe-eval

用法：
1. 在 settings.py 中添加中间件：
   MIDDLEWARE = [
       ...
       'apps.core.csp_nonce.CSPNonceMiddleware',
       ...
   ]

2. 在模板中使用：
   <script nonce="{{ request.csp_nonce }}">
       // 内联脚本
   </script>
   <style nonce="{{ request.csp_nonce }}">
       /* 内联样式 */
   </style>
"""

import secrets
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class CSPNonceMiddleware:
    """
    CSP Nonce 中间件

    为每个请求生成唯一的 nonce 值，用于内联脚本和样式。
    这比使用 'unsafe-inline' 更安全。
    """

    # 16 字节 = 32 个十六进制字符
    NONCE_LENGTH = 16

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp_enabled = getattr(settings, "CSP_NONCE_ENABLED", False)
        self.report_only = getattr(settings, "CSP_REPORT_ONLY", False)

    def __call__(self, request):
        # 为每个请求生成唯一 nonce
        request.csp_nonce = secrets.token_hex(self.NONCE_LENGTH)

        response = self.get_response(request)

        if self.csp_enabled:
            nonce = request.csp_nonce
            csp_policy = self._build_csp_with_nonce(nonce)

            if self.report_only:
                # 报告模式：只报告不阻止（用于测试）
                response["Content-Security-Policy-Report-Only"] = csp_policy
            else:
                # 强制模式：阻止违规
                response["Content-Security-Policy"] = csp_policy

        return response

    def _build_csp_with_nonce(self, nonce):
        """构建带 nonce 的 CSP 策略"""
        directives = [
            # 默认策略
            "default-src 'self'",
            # 脚本：允许 self 和 nonce
            f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net",
            # 样式：允许 self、nonce 和内联样式（兼容性）
            f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            # 图片：允许 self、data: 和 https
            "img-src 'self' data: https: blob:",
            # 字体：允许 self、data: 和 Google Fonts
            "font-src 'self' data: https://fonts.gstatic.com",
            # 连接：允许 self
            "connect-src 'self'",
            # 框架祖先：防止被嵌入
            "frame-ancestors 'none'",
            # 表单提交目标
            "form-action 'self'",
            # 基础 URL
            "base-uri 'self'",
        ]

        # 添加报告 URI（可选）
        report_uri = getattr(settings, "CSP_REPORT_URI", None)
        if report_uri:
            directives.append(f"report-uri {report_uri}")

        return "; ".join(directives)


def get_csp_nonce(request):
    """
    获取请求的 CSP nonce

    用于上下文处理器或模板标签
    """
    return getattr(request, "csp_nonce", "")


# 上下文处理器
def csp_nonce_context(request):
    """
    将 CSP nonce 注入模板上下文

    在 settings.py 中添加：
    'apps.core.csp_nonce.csp_nonce_context'
    到 TEMPLATES['OPTIONS']['context_processors']
    """
    return {
        "csp_nonce": getattr(request, "csp_nonce", ""),
    }
