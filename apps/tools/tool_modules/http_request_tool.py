"""
HTTP请求模拟器工具 - 优化版
"""

from ..categories import ToolCategory
from django import forms
from django.core.cache import cache
from apps.tools.base_tool import BaseTool
from http.cookies import SimpleCookie
import json
import socket
import struct
import time
from urllib.parse import urljoin, urlparse, urlunparse

import urllib3


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


def _resolve_public_ipv4_addresses(hostname):
    """Resolve a hostname to stable public IPv4 addresses only."""
    if _ip_to_int(hostname) is not None:
        if _is_private_or_internal(hostname):
            return None, "禁止访问内网地址"
        return [hostname], None

    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
    except socket.gaierror:
        return None, f"无法解析域名: {hostname}"

    addresses = []
    for info in infos:
        ip_address = info[4][0]
        if ip_address not in addresses:
            addresses.append(ip_address)

    if not addresses:
        return None, f"无法解析域名: {hostname}"

    for ip_address in addresses:
        if _is_private_or_internal(ip_address):
            return None, f"域名 {hostname} 解析到内网地址 {ip_address}，禁止访问"

    return addresses, None


def _prepare_pinned_request_target(url_str):
    """Resolve and pin an HTTP request target to a validated public IP."""
    parsed = urlparse(url_str)

    if parsed.scheme not in {"http", "https"}:
        return None, None, None, None, "只支持 HTTP 和 HTTPS 请求"

    if parsed.username or parsed.password:
        return None, None, None, None, "URL 中不支持内嵌账号密码，请使用请求头"

    hostname = parsed.hostname
    if not hostname:
        return None, None, None, None, "无法解析 URL 主机名"

    addresses, error_msg = _resolve_public_ipv4_addresses(hostname)
    if error_msg is not None:
        return None, None, None, None, error_msg

    resolved_ip = addresses[0]
    default_port = 443 if parsed.scheme == "https" else 80
    port = parsed.port or default_port
    host_header = hostname if port == default_port else f"{hostname}:{port}"
    pinned_netloc = resolved_ip if port == default_port else f"{resolved_ip}:{port}"
    request_path = parsed.path or "/"
    pinned_url = urlunparse((parsed.scheme, pinned_netloc, request_path, parsed.params, parsed.query, parsed.fragment))

    return parsed, pinned_url, host_header, resolved_ip, None


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

        _, _, _, _, error_msg = _prepare_pinned_request_target(url)
        if error_msg is not None:
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
            response_meta = self._send_request(
                method, url, headers_dict, data, content_type, timeout, follow_redirects
            )
        except Exception as e:
            return self._handle_request_error(e)

        # 解析响应
        return self._parse_response(response_meta)

    def _parse_headers(self, headers, content_type, method, data):
        """解析请求头"""
        headers_dict = {}
        if headers:
            try:
                headers_dict = json.loads(headers)
            except json.JSONDecodeError as e:
                return None, f"请求头JSON解析错误: {str(e)}"
            if not isinstance(headers_dict, dict):
                return None, "请求头必须是 JSON 对象"

        # 保留这些头由工具自身控制，避免绕过固定解析结果
        headers_dict.pop("Host", None)
        headers_dict.pop("host", None)
        headers_dict.pop("Content-Length", None)
        headers_dict.pop("content-length", None)

        # 添加Content-Type
        if method in ["POST", "PUT", "PATCH"] and data:
            headers_dict["Content-Type"] = content_type

        return headers_dict, None

    def _send_request(self, method, url, headers_dict, data, content_type, timeout, follow_redirects):
        """发送 HTTP 请求，并将域名固定到已校验的公网 IP。"""
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
            raise ValueError(f"不支持的 HTTP 方法: {method}")

        current_method = method
        current_url = url
        request_body = self._build_request_body(current_method, data, content_type)
        request_headers = dict(headers_dict)
        redirect_count = 0
        last_resolved_ip = None
        start_time = time.perf_counter()

        while True:
            parsed, pinned_url, host_header, resolved_ip, error_msg = _prepare_pinned_request_target(current_url)
            if error_msg is not None:
                raise ValueError(error_msg)

            last_resolved_ip = resolved_ip
            response = self._perform_request(
                current_method,
                pinned_url,
                request_headers,
                request_body,
                timeout,
                parsed.hostname,
                host_header,
            )

            location = response.headers.get("Location")
            if not (follow_redirects and location and response.status in {301, 302, 303, 307, 308}):
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return {
                    "response": response,
                    "method": current_method,
                    "url": current_url,
                    "elapsed_ms": elapsed_ms,
                    "resolved_ip": last_resolved_ip,
                }

            redirect_count += 1
            if redirect_count > 3:
                raise ValueError("重定向次数过多")

            current_url = urljoin(current_url, location)
            if response.status in {301, 302, 303} and current_method not in {"GET", "HEAD"}:
                current_method = "GET"
                request_body = None
                request_headers = {
                    key: value
                    for key, value in request_headers.items()
                    if key.lower() not in {"content-type", "content-length"}
                }

    def _perform_request(self, method, pinned_url, headers, body, timeout, original_host, host_header):
        """Execute a pinned outbound HTTP request."""
        request_headers = dict(headers)
        request_headers["Host"] = host_header

        manager_kwargs = {}
        if original_host:
            manager_kwargs["assert_hostname"] = original_host
            manager_kwargs["server_hostname"] = original_host

        timeout_config = urllib3.Timeout(connect=timeout, read=timeout)
        http = urllib3.PoolManager(**manager_kwargs)
        return http.request(
            method,
            pinned_url,
            body=body,
            headers=request_headers,
            timeout=timeout_config,
            redirect=False,
            retries=False,
            preload_content=True,
            assert_same_host=False,
        )

    def _build_request_body(self, method, data, content_type):
        """Prepare the outbound request body."""
        if method not in {"POST", "PUT", "PATCH"} or not data:
            return None

        if content_type == "application/json":
            parsed = json.loads(data)
            return json.dumps(parsed).encode("utf-8")

        if isinstance(data, bytes):
            return data

        return str(data).encode("utf-8")

    def _extract_response_encoding(self, headers):
        """Best-effort charset detection from response headers."""
        content_type = headers.get("Content-Type", "")
        for chunk in content_type.split(";")[1:]:
            name, _, value = chunk.strip().partition("=")
            if name.lower() == "charset" and value:
                return value.strip()
        return "utf-8"

    def _extract_response_cookies(self, headers):
        """Parse response cookies into a simple dict."""
        cookies = {}
        raw_values = headers.getlist("Set-Cookie") if hasattr(headers, "getlist") else []
        for raw_value in raw_values:
            parsed = SimpleCookie()
            parsed.load(raw_value)
            for key, morsel in parsed.items():
                cookies[key] = morsel.value
        return cookies

    def _parse_response(self, response_meta):
        """解析响应"""
        response = response_meta["response"]
        method = response_meta["method"]
        encoding = self._extract_response_encoding(response.headers)
        response_text = response.data.decode(encoding, errors="replace") if response.data else ""
        result = {
            "url": response_meta["url"],
            "method": method,
            "status_code": response.status,
            "status_text": response.reason,
            "headers": dict(response.headers),
            "resolved_ip": response_meta["resolved_ip"],
        }

        # 响应时间
        result["response_time"] = f"{response_meta['elapsed_ms']:.2f}ms"

        # 响应内容
        if method != "HEAD":
            try:
                # 尝试解析为JSON
                result["content"] = json.loads(response_text)
                result["content_type"] = "json"
            except Exception:
                # 返回文本
                result["content"] = response_text[:5000] if len(response_text) > 5000 else response_text
                result["content_type"] = "text"

            # 内容编码
            result["encoding"] = encoding

        # Cookies
        cookies = self._extract_response_cookies(response.headers)
        if cookies:
            result["cookies"] = cookies

        return result

    def _handle_request_error(self, e):
        """处理请求错误"""
        if isinstance(e, (urllib3.exceptions.ConnectTimeoutError, urllib3.exceptions.ReadTimeoutError, TimeoutError)):
            return {"error": "请求超时"}
        elif isinstance(e, (urllib3.exceptions.NewConnectionError, urllib3.exceptions.ProtocolError)):
            return {"error": f"连接错误: {str(e)}"}
        elif isinstance(e, urllib3.exceptions.SSLError):
            return {"error": f"TLS 连接错误: {str(e)}"}
        elif isinstance(e, json.JSONDecodeError):
            return {"error": f"请求体JSON解析错误: {str(e)}"}
        else:
            return {"error": str(e)}
