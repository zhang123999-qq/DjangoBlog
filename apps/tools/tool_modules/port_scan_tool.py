"""
端口扫描工具 - 优化版
"""
from ..categories import ToolCategory
from django import forms
from apps.tools.base_tool import BaseTool
import socket


# 常用端口列表
COMMON_PORTS = {
    'Web服务': [80, 443, 8080, 8443],
    '数据库': [3306, 5432, 27017, 6379, 1433],
    '远程访问': [22, 23, 3389, 5900],
    '邮件': [25, 110, 143, 465, 587, 993, 995],
    '文件传输': [20, 21, 69, 115],
    'DNS': [53],
    '代理': [3128, 8080, 8888],
}


class PortScanForm(forms.Form):
    """端口扫描表单"""
    host = forms.CharField(
        label='主机名/IP',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'example.com 或 192.168.1.1'
        }),
        required=True,
        help_text='输入域名或IP地址'
    )
    scan_type = forms.ChoiceField(
        label='扫描类型',
        choices=[
            ('single', '单端口扫描'),
            ('common', '常用端口扫描'),
            ('range', '端口范围扫描'),
            ('custom', '自定义端口'),
        ],
        initial='single',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    port = forms.IntegerField(
        label='端口号',
        min_value=1,
        max_value=65535,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '80'
        }),
        required=False
    )
    common_port_group = forms.ChoiceField(
        label='常用端口组',
        choices=[(k, k) for k in COMMON_PORTS.keys()],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    port_range = forms.CharField(
        label='端口范围',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1-1000 或 80,443,8080'
        }),
        required=False,
        help_text='格式: 1-1000 或 80,443,8080'
    )
    timeout = forms.IntegerField(
        label='超时时间（秒）',
        min_value=1,
        max_value=30,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
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
        host = form.cleaned_data['host']
        scan_type = form.cleaned_data['scan_type']
        timeout = form.cleaned_data['timeout']

        # 解析端口
        ports = []
        if scan_type == 'single':
            port = form.cleaned_data.get('port')
            if not port:
                return {'error': '请输入端口号'}
            ports = [port]
        elif scan_type == 'common':
            group = form.cleaned_data.get('common_port_group')
            if group in COMMON_PORTS:
                ports = COMMON_PORTS[group]
        elif scan_type == 'range':
            port_range = form.cleaned_data.get('port_range', '').strip()
            if not port_range:
                return {'error': '请输入端口范围'}
            ports = self._parse_port_range(port_range)
        elif scan_type == 'custom':
            port_range = form.cleaned_data.get('port_range', '').strip()
            if not port_range:
                return {'error': '请输入端口'}
            # 支持逗号分隔的端口列表
            ports = [int(p.strip()) for p in port_range.split(',') if p.strip().isdigit()]

        if not ports:
            return {'error': '没有要扫描的端口'}

        # 限制端口数量，防止滥用
        if len(ports) > 1000:
            return {'error': f'端口数量过多 ({len(ports)})，最多支持1000个端口'}

        # 开始扫描
        results = []
        open_ports = []
        closed_count = 0

        for port in ports:
            status, message = self._scan_port(host, port, timeout)
            result = {
                'port': port,
                'status': status,
                'message': message,
                'service': self._get_service_name(port)
            }
            results.append(result)
            if status == '开放':
                open_ports.append(port)
            else:
                closed_count += 1

        return {
            'host': host,
            'total_ports': len(ports),
            'open_count': len(open_ports),
            'open_ports': open_ports,
            'closed_count': closed_count,
            'results': results[:50]  # 只返回前50个结果详情
        }

    def _parse_port_range(self, port_range):
        """解析端口范围"""
        ports = []
        # 处理范围格式 "1-1000"
        if '-' in port_range and ',' not in port_range:
            parts = port_range.split('-')
            if len(parts) == 2:
                try:
                    start = int(parts[0])
                    end = int(parts[1])
                    ports = list(range(start, end + 1))
                except ValueError:
                    pass
        # 处理逗号分隔 "80,443,8080"
        elif ',' in port_range:
            ports = [int(p.strip()) for p in port_range.split(',') if p.strip().isdigit()]
        return ports

    def _scan_port(self, host, port, timeout):
        """扫描单个端口"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return ('开放', f'端口 {port} 是开放的')
            else:
                return ('关闭', f'端口 {port} 是关闭的')
        except socket.timeout:
            return ('超时', f'端口 {port} 扫描超时')
        except socket.gaierror:
            return ('错误', '无法解析主机名')
        except Exception as e:
            return ('错误', str(e))

    def _get_service_name(self, port):
        """获取常见服务名称"""
        services = {
            21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP',
            53: 'DNS', 80: 'HTTP', 110: 'POP3', 143: 'IMAP',
            443: 'HTTPS', 445: 'SMB', 993: 'IMAPS', 995: 'POP3S',
            3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL',
            5900: 'VNC', 6379: 'Redis', 8080: 'HTTP-Alt',
            8443: 'HTTPS-Alt', 27017: 'MongoDB',
        }
        return services.get(port, '')
