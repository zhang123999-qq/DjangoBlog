"""
NAT 检测工具 - 检测网络地址转换状态
"""

import socket
import requests
from requests.exceptions import RequestException

from ..categories import ToolCategory
from django import forms
from ..base_tool import BaseTool


class NATDetectorForm(forms.Form):
    """NAT 检测表单 - 空表单"""


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
        """
        返回服务器端信息，供前端 WebRTC 检测 NAT 类型时参考。
        """
        # 获取服务器本地信息（尽量获取 IPv4 地址）
        hostname = socket.gethostname()
        local_ip = self._get_local_ipv4()

        # 获取公网 IP（可选，用于辅助判断）
        public_ip = self._get_public_ip()

        return {
            "server_info": {
                "hostname": hostname,
                "local_ip": local_ip,
            },
            "server_public_ip": public_ip,
        }

    def _get_local_ipv4(self):
        """
        尝试获取本机 IPv4 地址，失败时返回 "未知"。
        """
        try:
            # 创建一个 UDP 套接字，连接到一个公共 DNS 服务器（不实际发送数据）
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "未知"

    def _get_public_ip(self):
        """
        获取服务器的公网 IP，失败时返回 None。
        """
        try:
            response = requests.get("https://api.ipify.org?format=json", timeout=5)
            response.raise_for_status()
            return response.json().get("ip")
        except (RequestException, ImportError, ValueError):
            return None
