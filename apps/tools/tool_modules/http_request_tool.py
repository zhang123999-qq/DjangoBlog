"""
HTTP请求模拟器工具 - 优化版
"""

from ..categories import ToolCategory
from django import forms
from django.core.cache import cache
from apps.tools.base_tool import BaseTool
import json
import socket
import struct
import time
from urllib.parse import urlparse


def _ip_to_int(ip_str):
    """将 IP 转为整数，便于范围比较"""
    try:
        return struct.unpack("!I", socket.inet_aton(ip_str))[0]
    except (socket.error, OSError):
        return None


def _is_private_or_internal(ip_str):
    """检查 IP 是否为内网/私有地址"""
    ip_int = _ip_to_int(ip_str)
    if ip_int is None:
        return True  # 无法解析则拒绝

    # 内网/私有地址范围
    private_ranges = [
        (0x00000000, 0x00FFFFFF),  # 0.0.0.0/8
        (0x0A000000, 0x0AFFFFFF),  # 10.0.0.0/8
        (0x64400000, 0x647FFFFF),  # 100.64.0.0/10 (CGNAT)
        (0x7F000000, 0x7FFFFFFF),  # 127.0.0.0/8 (localhost)
        (0xAC100000, 0xAC1FFFFF),  # 172.16.0.0/12
        (0xC0A80000, 0xC0AFFFFF),  # 192.168.0.0/16
        (0xC00000A8, 0xC00000A8),  # 192.0.0.8/32 (DS-Lite)
        (0xC0000200, 0xC00002FF),  # 192.0.2.0/24 (TEST-NET-1)
        (0xC6120000, 0xC613FFFF),  # 198.18.0.0/15 (基准测试)
        (0xC6336400, 0xC63364FF),  # 198.51.100.0/24 (TEST-NET-2)
        (0xCB007100, 0xCB0071FF),  # 203.0.113.0/24 (TEST-NET-3)
        (0xA9FE0000, 0xA9FEFFFF),  # 169.254.0.0/16 (链路本地/元数据)
        (0xF0000000, 0xFFFFFFFF),  # 240.0.0.0/4 (保留/组播)
    ]

    for start, end in private_ranges:
        if start <= ip_int <= end:
            return True
    return False


def _validate_url_for_ssrf(url_str):
    """验证 URL 目标地址，防止 SSRF"""
    parsed = urlparse(url_str)
    hostname = parsed.hostname

    if not hostname:
        return False, "无法解析 URL 主机名"

    # 先检查是否是 IP 直连
    ip_int = _ip_to_int(hostname)
    if ip_int is not None:
        if _is_private_or_internal(hostname):
            return False, "禁止访问内网地址"
    else:
        # 域名解析并检查
        try:
            resolved_ip = socket.gethostbyname(hostname)
            if _is_private_or_internal(resolved_ip):
                return False, f"域名 {hostname} 解析到内网地址 {resolved_ip}，禁止访问"
        except socket.gaierror:
            return False, f"无法解析域名: {hostname}"

    return True, None


# 用户级请求频率限制
def _check_http_request_rate_limit(request):
    """每用户每分钟最多 20 次 HTTP 请求"""
    user_id = getattr(request.user, "id", None) or "anon"
    bucket = str(int(time.time()) // 60)
    key = f"tools:http_req:{user_id}:{bucket}"

    count = cache.get(key, 0)
    if count >= 20:
        return False
    cache.set(key, count + 1, 120)
    return True


class HTTPRequestForm(forms.Form):
    """HTTP请求模拟器表单"""

    url = forms.CharField(
        label="URL",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "https://api.example.com/endpoint"}),
        required=True,
        help_text="输入完整的URL地址",
    )
    method = forms.ChoiceField(
        label="请求方法",
        choices=[
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
            ("PATCH", "PATCH"),
            ("HEAD", "HEAD"),
            ("OPTIONS", "OPTIONS"),
        ],
        initial="GET",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    headers = forms.CharField(
        label="请求头（JSON格式）",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "form-control",
                "placeholder": '{"Content-Type": "application/json", "Authorization": "Bearer token"}',
            }
        ),
        required=False,
        help_text="可选的请求头，JSON格式",
    )
    data = forms.CharField(
        label="请求体（POST/PUT/PATCH）",
        widget=forms.Textarea(attrs={"rows": 5, "class": "form-control", "placeholder": '{"key": "value"}'}),
        required=False,
        help_text="请求体内容，JSON或表单格式",
    )
    content_type = forms.ChoiceField(
        label="Content-Type",
        choices=[
            ("application/json", "JSON"),
            ("application/x-www-form-urlencoded", "表单"),
            ("text/plain", "纯文本"),
            ("multipart/form-data", "multipart"),
        ],
        initial="application/json",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    timeout = forms.IntegerField(
        label="超时时间（秒）",
        min_value=1,
        max_value=60,
        initial=30,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    follow_redirects = forms.BooleanField(
        label="跟随重定向", initial=True, required=False, help_text="是否自动跟随301/302重定向"
    )


class HTTPRequestTool(BaseTool):
    """HTTP请求模拟器工具"""

    name = "HTTP请求模拟器"
    slug = "http-request"
    description = "发送HTTP/HTTPS请求，支持多种方法、自定义头部和请求体"
    icon = "fa fa-paper-plane"
    category = ToolCategory.NETWORK
    form_class = HTTPRequestForm

    def handle(self, request, form):
        """处理 HTTP 请求"""
        # 提取表单数据
        url = form.cleaned_data["url"]
        method = form.cleaned_data["method"]
        headers = form.cleaned_data["headers"]
        data = form.cleaned_data["data"]
        content_type = form.cleaned_data["content_type"]
        timeout = form.cleaned_data["timeout"]
        follow_redirects = form.cleaned_data["follow_redirects"]

        # SSRF 保护：验证目标地址不是内网
        is_valid, error_msg = _validate_url_for_ssrf(url)
        if not is_valid:
            return {"error": f"安全限制: {error_msg}"}

        # 速率限制
        if not _check_http_request_rate_limit(request):
            return {"error": "请求过于频繁，请稍后再试（每分钟最多 20 次）"}

        # 解析请求头
        headers_dict, error = self._parse_headers(headers, content_type, method, data)
        if error:
            return {"error": error}

        # 发送请求
        try:
            response = self._send_request(
                method, url, headers_dict, data, content_type, timeout, follow_redirects
            )
        except Exception as e:
            return self._handle_request_error(e)

        # 解析响应
        return self._parse_response(response, method)

    def _parse_headers(self, headers, content_type, method, data):
        """解析请求头"""
        headers_dict = {}
        if headers:
            try:
                headers_dict = json.loads(headers)
            except json.JSONDecodeError as e:
                return None, f"请求头JSON解析错误: {str(e)}"

        # 添加Content-Type
        if method in ["POST", "PUT", "PATCH"] and data:
            headers_dict["Content-Type"] = content_type

        return headers_dict, None

    def _send_request(self, method, url, headers_dict, data, content_type, timeout, follow_redirects):
        """发送 HTTP 请求"""
        try:
            import requests
        except ImportError:
            raise ImportError("请安装 requests: pip install requests")

        session = requests.Session()

        # 准备请求数据
        if method in ["POST", "PUT", "PATCH"] and data and content_type == "application/json":
            try:
                data = json.loads(data)
            except Exception:
                pass

        # 发送请求
        if method == "GET":
            return session.get(url, headers=headers_dict, timeout=timeout, allow_redirects=follow_redirects)
        elif method == "POST":
            return session.post(url, data=data, headers=headers_dict, timeout=timeout, allow_redirects=follow_redirects)
        elif method == "PUT":
            return session.put(url, data=data, headers=headers_dict, timeout=timeout, allow_redirects=follow_redirects)
        elif method == "DELETE":
            return session.delete(url, headers=headers_dict, timeout=timeout, allow_redirects=follow_redirects)
        elif method == "PATCH":
            return session.patch(url, data=data, headers=headers_dict, timeout=timeout, allow_redirects=follow_redirects)
        elif method == "HEAD":
            return session.head(url, headers=headers_dict, timeout=timeout, allow_redirects=follow_redirects)
        elif method == "OPTIONS":
            return session.options(url, headers=headers_dict, timeout=timeout, allow_redirects=follow_redirects)
        else:
            raise ValueError(f"不支持的 HTTP 方法: {method}")

    def _parse_response(self, response, method):
        """解析响应"""
        result = {
            "url": response.url,
            "method": method,
            "status_code": response.status_code,
            "status_text": response.reason,
            "headers": dict(response.headers),
        }

        # 响应时间
        result["response_time"] = f"{response.elapsed.total_seconds() * 1000:.2f}ms"

        # 响应内容
        if method != "HEAD":
            try:
                # 尝试解析为JSON
                result["content"] = response.json()
                result["content_type"] = "json"
            except Exception:
                # 返回文本
                result["content"] = response.text[:5000] if len(response.text) > 5000 else response.text
                result["content_type"] = "text"

            # 内容编码
            result["encoding"] = response.encoding

        # Cookies
        if response.cookies:
            result["cookies"] = dict(response.cookies)

        return result

    def _handle_request_error(self, e):
        """处理请求错误"""
        import requests
        
        if isinstance(e, requests.Timeout):
            return {"error": "请求超时"}
        elif isinstance(e, requests.ConnectionError):
            return {"error": f"连接错误: {str(e)}"}
        elif isinstance(e, requests.RequestException):
            return {"error": f"请求错误: {str(e)}"}
        elif isinstance(e, json.JSONDecodeError):
            return {"error": f"请求体JSON解析错误: {str(e)}"}
        elif isinstance(e, ImportError):
            return {"error": str(e)}
        else:
            return {"error": str(e)}
