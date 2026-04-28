"""
端口扫描工具 - 优化版
"""

from ..categories import ToolCategory
from django import forms
from django.core.cache import cache
from apps.tools.base_tool import BaseTool
import socket
import struct
import time


# 复用 IP 检查逻辑
def _ip_to_int(ip_str):
    try:
        return struct.unpack("!I", socket.inet_aton(ip_str))[0]
    except (socket.error, OSError):
        return None


def _is_private_or_internal(ip_str):
    ip_int = _ip_to_int(ip_str)
    if ip_int is None:
        return True
    private_ranges = [
        (0x00000000, 0x00FFFFFF),  # 0.0.0.0/8
        (0x0A000000, 0x0AFFFFFF),  # 10.0.0.0/8
        (0x64400000, 0x647FFFFF),  # 100.64.0.0/10
        (0x7F000000, 0x7FFFFFFF),  # 127.0.0.0/8
        (0xAC100000, 0xAC1FFFFF),  # 172.16.0.0/12
        (0xC0A80000, 0xC0AFFFFF),  # 192.168.0.0/16
        (0xA9FE0000, 0xA9FEFFFF),  # 169.254.0.0/16
        (0xF0000000, 0xFFFFFFFF),  # 240.0.0.0/4
    ]
    for start, end in private_ranges:
        if start <= ip_int <= end:
            return True
    return False


def _check_port_scan_rate_limit(request):
    """每用户每 5 分钟最多 3 次端口扫描"""
    user_id = getattr(request.user, "id", None) or "anon"
    bucket = str(int(time.time()) // 300)
    key = f"tools:port_scan:{user_id}:{bucket}"

    count = cache.get(key, 0)
    if count >= 3:
        return False
    cache.set(key, count + 1, 600)
    return True


def _resolve_public_target(host):
    """Resolve a hostname once and return a pinned public IPv4 target."""
    ip_int = _ip_to_int(host)
    if ip_int is not None:
        if _is_private_or_internal(host):
            return None, "安全限制：禁止扫描内网地址"
        return host, None

    try:
        infos = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
    except socket.gaierror:
        return None, f"无法解析域名: {host}"

    addresses = []
    for info in infos:
        ip_address = info[4][0]
        if ip_address not in addresses:
            addresses.append(ip_address)

    if not addresses:
        return None, f"无法解析域名: {host}"

    for ip_address in addresses:
        if _is_private_or_internal(ip_address):
            return None, f"安全限制：域名 {host} 解析到内网地址，禁止扫描"

    return addresses[0], None


# 常用端口列表
COMMON_PORTS = {
    "Web服务": [80, 443, 8080, 8443],
    "数据库": [3306, 5432, 27017, 6379, 1433],
    "远程访问": [22, 23, 3389, 5900],
    "邮件": [25, 110, 143, 465, 587, 993, 995],
    "文件传输": [20, 21, 69, 115],
    "DNS": [53],
    "代理": [3128, 8080, 8888],
}


class PortScanForm(forms.Form):
    """端口扫描表单"""

    host = forms.CharField(
        label="主机名/IP",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "example.com 或 192.168.1.1"}),
        required=True,
        help_text="输入域名或IP地址",
    )
    scan_type = forms.ChoiceField(
        label="扫描类型",
        choices=[
            ("single", "单端口扫描"),
            ("common", "常用端口扫描"),
            ("range", "端口范围扫描"),
            ("custom", "自定义端口"),
        ],
        initial="single",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    port = forms.IntegerField(
        label="端口号",
        min_value=1,
        max_value=65535,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "80"}),
        required=False,
    )
    common_port_group = forms.ChoiceField(
        label="常用端口组",
        choices=[(k, k) for k in COMMON_PORTS.keys()],
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    port_range = forms.CharField(
        label="端口范围",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "1-1000 或 80,443,8080"}),
        required=False,
        help_text="格式: 1-1000 或 80,443,8080",
    )
    timeout = forms.IntegerField(
        label="超时时间（秒）",
        min_value=1,
        max_value=30,
        initial=3,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class PortScanTool(BaseTool):
    """端口扫描工具"""

    name = "端口扫描"
    slug = "port-scan"
    description = "检查指定IP或域名的端口开放情况，支持单端口、常用端口和端口范围扫描"
    icon = "fa fa-network-wired"
    category = ToolCategory.NETWORK
    form_class = PortScanForm

    def handle(self, request, form):
        host = form.cleaned_data["host"]
        scan_type = form.cleaned_data["scan_type"]
        timeout = form.cleaned_data["timeout"]

        target_host, error_message = _resolve_public_target(host)
        if error_message is not None:
            return {"error": error_message}

        # 速率限制
        if not _check_port_scan_rate_limit(request):
            return {"error": "扫描过于频繁，请稍后再试（每 5 分钟最多 3 次）"}

        # 解析端口
        ports = []
        if scan_type == "single":
            port = form.cleaned_data.get("port")
            if not port:
                return {"error": "请输入端口号"}
            ports = [port]
        elif scan_type == "common":
            group = form.cleaned_data.get("common_port_group")
            if group in COMMON_PORTS:
                ports = COMMON_PORTS[group]
        elif scan_type == "range":
            port_range = form.cleaned_data.get("port_range", "").strip()
            if not port_range:
                return {"error": "请输入端口范围"}
            ports = self._parse_port_range(port_range)
        elif scan_type == "custom":
            port_range = form.cleaned_data.get("port_range", "").strip()
            if not port_range:
                return {"error": "请输入端口"}
            # 支持逗号分隔的端口列表
            ports = [int(p.strip()) for p in port_range.split(",") if p.strip().isdigit()]

        if not ports:
            return {"error": "没有要扫描的端口"}

        # 限制端口数量，防止滥用（降为 100，降低被滥用风险）
        if len(ports) > 100:
            return {"error": f"端口数量过多 ({len(ports)})，最多支持 100 个端口"}

        # 开始扫描
        results = []
        open_ports = []
        closed_count = 0

        for port in ports:
            status, message = self._scan_port(target_host, port, timeout)
            result = {"port": port, "status": status, "message": message, "service": self._get_service_name(port)}
            results.append(result)
            if status == "开放":
                open_ports.append(port)
            else:
                closed_count += 1

        return {
            "host": host,
            "resolved_ip": target_host,
            "total_ports": len(ports),
            "open_count": len(open_ports),
            "open_ports": open_ports,
            "closed_count": closed_count,
            "results": results[:50],  # 只返回前50个结果详情
        }

    def _parse_port_range(self, port_range):
        """解析端口范围"""
        ports = []
        # 处理范围格式 "1-1000"
        if "-" in port_range and "," not in port_range:
            parts = port_range.split("-")
            if len(parts) == 2:
                try:
                    start = int(parts[0])
                    end = int(parts[1])
                    ports = list(range(start, end + 1))
                except ValueError:
                    pass
        # 处理逗号分隔 "80,443,8080"
        elif "," in port_range:
            ports = [int(p.strip()) for p in port_range.split(",") if p.strip().isdigit()]
        return ports

    def _scan_port(self, host, port, timeout):
        """扫描单个端口"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return ("开放", f"端口 {port} 是开放的")
            else:
                return ("关闭", f"端口 {port} 是关闭的")
        except socket.timeout:
            return ("超时", f"端口 {port} 扫描超时")
        except socket.gaierror:
            return ("错误", "无法解析主机名")
        except Exception as e:
            return ("错误", str(e))

    def _get_service_name(self, port):
        """获取常见服务名称"""
        services = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            445: "SMB",
            993: "IMAPS",
            995: "POP3S",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            6379: "Redis",
            8080: "HTTP-Alt",
            8443: "HTTPS-Alt",
            27017: "MongoDB",
        }
        return services.get(port, "")
