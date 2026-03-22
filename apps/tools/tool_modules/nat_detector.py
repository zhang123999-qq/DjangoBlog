"""
NAT 检测工具 - 检测网络地址转换状态
"""
from ..categories import ToolCategory
from django import forms
from ..base_tool import BaseTool


class NATDetectorForm(forms.Form):
    """NAT 检测表单 - 空表单"""
    pass


class NATDetectorTool(BaseTool):
    """NAT 检测工具"""
    name = "NAT 检测"
    slug = "nat-detector"
    description = "检测您的网络地址转换(NAT)状态，了解您的网络连接类型"
    icon = "bi bi-diagram-3"
    category = ToolCategory.NETWORK
    form_class = NATDetectorForm
    template_name = "tools/nat_detector.html"

    def handle(self, request, form):
        # NAT检测主要在前端通过WebRTC完成
        # 这里返回服务器端信息
        import socket
        
        # 获取服务器信息
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            hostname = "未知"
            local_ip = "未知"
        
        # 尝试获取公网IP（作为备用）
        public_ip = None
        try:
            import requests
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            if response.status_code == 200:
                public_ip = response.json().get('ip')
        except:
            pass
        
        return {
            'server_info': {
                'hostname': hostname,
                'local_ip': local_ip,
            },
            'server_public_ip': public_ip,
        }
