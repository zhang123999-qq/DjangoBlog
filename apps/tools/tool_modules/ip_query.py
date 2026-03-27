"""
IP查询工具 - 优化版
"""
from ..categories import ToolCategory
from django import forms
import requests
from ..base_tool import BaseTool


class IPQueryForm(forms.Form):
    """IP 查询表单"""
    ip = forms.CharField(
        label='IP地址或域名',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '8.8.8.8 或 google.com'
        }),
        required=True,
        help_text='输入IP地址或域名，系统会自动提取IP进行查询'
    )


class IPQueryTool(BaseTool):
    """IP 查询工具"""
    name = "IP 查询"
    slug = "ip-query"
    description = "查询IP地址或域名的详细信息，包括地理位置、运营商、AS号等"
    icon = "fa fa-globe"
    category = ToolCategory.NETWORK
    form_class = IPQueryForm

    def handle(self, request, form):
        ip = form.cleaned_data['ip']

        # 如果输入的是域名，先解析IP
        original_input = ip
        if not self._is_ip(ip):
            resolved_ip = self._resolve_domain(ip)
            if resolved_ip:
                ip = resolved_ip
            else:
                return {'error': f'无法解析域名: {original_input}'}

        # 使用多个API获取更全面的信息
        result = {
            'input': original_input,
            'query_ip': ip,
        }

        # 1. ipinfo.io API
        ipinfo = self._query_ipinfo(ip)
        if ipinfo:
            result['ipinfo'] = ipinfo

        # 2. ip-api.com (免费，支持中文)
        ipapi = self._query_ipapi(ip)
        if ipapi:
            result['ipapi'] = ipapi

        return result

    def _is_ip(self, ip_str):
        """检查是否为IP地址"""
        try:
            parts = ip_str.split('.')
            return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)
        except Exception:
            return False

    def _resolve_domain(self, domain):
        """解析域名到IP"""
        import socket
        try:
            return socket.gethostbyname(domain)
        except Exception:
            return None

    def _query_ipinfo(self, ip):
        """查询 ipinfo.io"""
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            return {'error': str(e)}
        return None

    def _query_ipapi(self, ip):
        """查询 ip-api.com"""
        try:
            # 支持中文返回
            response = requests.get(
                f"http://ip-api.com/json/{ip}?lang=zh-CN",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country'),
                        'countryCode': data.get('countryCode'),
                        'region': data.get('regionName'),
                        'city': data.get('city'),
                        'isp': data.get('isp'),
                        'org': data.get('org'),
                        'as': data.get('as'),
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'timezone': data.get('timezone'),
                    }
        except Exception as e:
            return {'error': str(e)}
        return None
