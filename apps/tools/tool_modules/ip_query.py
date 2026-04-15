"""
IP 查询工具 - 整合版（自动检测 + 手动查询）
"""

from ..categories import ToolCategory
from django import forms
import requests
import socket
from ..base_tool import BaseTool


class IPQueryForm(forms.Form):
    """IP 查询表单"""

    ip = forms.CharField(
        label="IP地址或域名",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "留空自动检测我的IP，或输入 8.8.8.8 / google.com"}
        ),
        required=False,
        help_text="留空将自动检测您当前的 IP 地址并查询",
    )


class IPQueryTool(BaseTool):
    """IP 查询工具（整合版）"""

    name = "IP 查询"
    slug = "ip-query"
    description = "查询当前或指定的 IP 地址信息，包括地理位置、运营商、AS 号等"
    icon = "fa fa-globe"
    category = ToolCategory.NETWORK
    form_class = IPQueryForm
    template_name = "tools/ip_query.html"

    def handle(self, request, form):
        query_ip = form.cleaned_data.get("ip", "").strip()

        # 未输入 → 自动检测当前 IP
        if not query_ip:
            detected_ip = self._get_client_ip(request)
            if not detected_ip:
                return {"error": "无法获取您的 IP 地址"}
            query_ip = detected_ip
            is_detected = True
        else:
            is_detected = False
            # 域名解析
            if not self._is_ip(query_ip):
                resolved = self._resolve_domain(query_ip)
                if resolved:
                    query_ip = resolved
                else:
                    return {"error": f'无法解析域名: {form.cleaned_data.get("ip", "")}'}

        # 查询 IP 信息
        result = {
            "input": form.cleaned_data.get("ip", ""),
            "query_ip": query_ip,
            "is_detected": is_detected,
        }

        # 1. ipinfo.io
        ipinfo = self._query_ipinfo(query_ip)
        if ipinfo:
            result["ipinfo"] = ipinfo

        # 2. ip-api.com（支持中文）
        ipapi = self._query_ipapi(query_ip)
        if ipapi:
            result["ipapi"] = ipapi

        # 如果两个 API 都失败
        if not ipinfo and not ipapi:
            result["error"] = "所有 IP 查询 API 均失败，请稍后重试"

        return result

    def _is_ip(self, ip_str):
        """检查是否为 IP 地址"""
        try:
            parts = ip_str.split(".")
            return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)
        except Exception:
            return False

    def _resolve_domain(self, domain):
        """解析域名到 IP"""
        try:
            return socket.gethostbyname(domain)
        except Exception:
            return None

    def _get_client_ip(self, request):
        """获取客户端真实 IP"""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ip = xff.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        return ip

    def _query_ipinfo(self, ip):
        try:
            resp = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def _query_ipapi(self, ip):
        try:
            resp = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    return {
                        "country": data.get("country"),
                        "countryCode": data.get("countryCode"),
                        "regionName": data.get("regionName"),
                        "city": data.get("city"),
                        "isp": data.get("isp"),
                        "org": data.get("org"),
                        "as": data.get("as"),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "timezone": data.get("timezone"),
                    }
        except Exception:
            pass
        return None
