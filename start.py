#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DjangoBlog 快速启动脚本
支持 Windows/Linux/macOS

用法:
    python start.py          # 启动开发服务器
    python start.py --lan    # 允许局域网访问
    python start.py --port 8080  # 指定端口
"""

import os
import sys
import subprocess
import platform
import socket
from pathlib import Path


# ============================================
# 终端编码处理
# ============================================

def setup_terminal():
    """设置终端编码"""
    if platform.system() == 'Windows':
        try:
            os.system('chcp 65001 > nul 2>&1')
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'


# ============================================
# 颜色输出
# ============================================

class Colors:
    SUPPORTS_COLOR = (
        (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty())
        or os.environ.get('FORCE_COLOR', '') == '1'
    )
    
    OKGREEN = '\033[92m' if SUPPORTS_COLOR else ''
    OKCYAN = '\033[96m' if SUPPORTS_COLOR else ''
    WARNING = '\033[93m' if SUPPORTS_COLOR else ''
    BOLD = '\033[1m' if SUPPORTS_COLOR else ''
    ENDC = '\033[0m' if SUPPORTS_COLOR else ''


def safe_print(text: str):
    """安全打印"""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))


def print_success(text: str):
    safe_print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")


def print_info(text: str):
    safe_print(f"{Colors.OKCYAN}[INFO] {text}{Colors.ENDC}")


def print_warning(text: str):
    safe_print(f"{Colors.WARNING}[WARN] {text}{Colors.ENDC}")


# ============================================
# 辅助函数
# ============================================

def get_venv_python() -> str:
    """获取虚拟环境中的 Python 路径"""
    project_root = Path(__file__).parent.resolve()
    is_windows = platform.system() == 'Windows'
    
    if is_windows:
        venv_python = project_root / '.venv' / 'Scripts' / 'python.exe'
    else:
        venv_python = project_root / '.venv' / 'bin' / 'python'
    
    if not venv_python.exists():
        return sys.executable
    
    return str(venv_python)


def get_local_ip() -> str:
    """获取本机 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def check_server_running(port: int) -> bool:
    """检查端口是否被占用"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()
        return result == 0
    except:
        return False


def print_banner():
    """打印启动横幅"""
    safe_print("")
    safe_print(f"{Colors.OKCYAN}{Colors.BOLD}{'='*55}{Colors.ENDC}")
    safe_print(f"{Colors.OKCYAN}{Colors.BOLD}{'DjangoBlog 开发服务器':^55}{Colors.ENDC}")
    safe_print(f"{Colors.OKCYAN}{Colors.BOLD}{'='*55}{Colors.ENDC}")
    safe_print("")


# ============================================
# 主函数
# ============================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='DjangoBlog 快速启动脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python start.py           # 启动服务器
  python start.py --lan     # 局域网访问
  python start.py --port 8080  # 自定义端口
        '''
    )
    
    parser.add_argument('--lan', action='store_true', help='允许局域网访问')
    parser.add_argument('--port', type=int, default=8000, help='端口 (默认: 8000)')
    parser.add_argument('--no-browser', action='store_true', help='不打开浏览器')
    
    args = parser.parse_args()
    
    # 设置终端
    setup_terminal()
    
    # 获取参数
    python = get_venv_python()
    project_root = Path(__file__).parent.resolve()
    manage_py = project_root / 'manage.py'
    
    host = '0.0.0.0' if args.lan else '127.0.0.1'
    port = args.port
    
    # 打印横幅
    print_banner()
    
    # 检查端口
    if check_server_running(port):
        print_warning(f"端口 {port} 已被占用!")
        print_info("请使用 --port 指定其他端口")
        return 1
    
    # 打印信息
    print_info(f"Python: {python}")
    print_info(f"地址: http://{host}:{port}/")
    print_info(f"管理后台: http://{host}:{port}/admin/")
    print_info(f"安装向导: http://{host}:{port}/install/")
    
    if args.lan:
        print_warning("局域网访问已启用")
        local_ip = get_local_ip()
        print_info(f"本机IP: http://{local_ip}:{port}/")
    
    safe_print("")
    print_success("按 Ctrl+C 停止服务器")
    safe_print("")
    
    # 构建命令
    cmd = [python, str(manage_py), 'runserver', f'{host}:{port}']
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 启动服务器
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        safe_print("")
        print_warning("服务器已停止")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
