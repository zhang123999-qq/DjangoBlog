"""
IP 检测工具 - 自动检测访问者IP地址
"""
from django import forms
import requests
from ..base_tool import BaseTool


class IPDetectorForm(forms.Form):
    """IP 检测表单 - 空表单，不需要用户输入"""
    pass


class IPDetectorTool(BaseTool):
    """IP 检测工具 - 自动显示访问者的IP地址"""
    name = "我的IP"
    slug = "my-ip"
    description = "自动检测您的IP地址，显示位置、运营商等信息"
    icon = "bi bi-geo-alt"
    form_class = IPDetectorForm
    template_name = "tools/ip_detector.html"

    def handle(self, request, form):
        # 获取访问者真实IP
        ip = self._get_client_ip(request)
        
        if not ip:
            return {'error': '无法获取IP地址'}
        
        # 查询IP信息
        ip_info = self._query_ip_info(ip)
        
        return {
            'ip': ip,
            'ip_info': ip_info,
        }
    
    def _get_client_ip(self, request):
        """获取客户端真实IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # 如果有代理，取第一个IP
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        # 处理本地开发环境
        if ip in ['127.0.0.1', '::1', 'localhost']:
            # 尝试获取公网IP
            try:
                response = requests.get('https://api.ipify.org?format=json', timeout=5)
                if response.status_code == 200:
                    return response.json().get('ip', ip)
            except:
                pass
        
        return ip
    
    def _query_ip_info(self, ip):
        """查询IP详细信息"""
        result = {}
        
        # 使用 ip-api.com (免费，支持中文)
        try:
            response = requests.get(
                f"http://ip-api.com/json/{ip}?lang=zh-CN&fields=status,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,query",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    result = {
                        'country': data.get('country', '-'),
                        'country_code': data.get('countryCode', '-'),
                        'region': data.get('regionName', '-'),
                        'city': data.get('city', '-'),
                        'zipcode': data.get('zip', '-'),
                        'lat': data.get('lat', '-'),
                        'lon': data.get('lon', '-'),
                        'timezone': data.get('timezone', '-'),
                        'isp': data.get('isp', '-'),
                        'org': data.get('org', '-'),
                        'as': data.get('as', '-'),
                        'asname': data.get('asname', '-'),
                    }
        except Exception as e:
            result['error'] = str(e)
        
        # 补充 ipinfo.io 信息
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not result.get('timezone'):
                    result['timezone'] = data.get('timezone', '-')
                # 添加hostname
                result['hostname'] = data.get('hostname', '-')
        except:
            pass
        
        return result
