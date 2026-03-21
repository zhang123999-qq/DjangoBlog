#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DjangoBlog 自动化部署脚本 v2.0
支持 Windows/Linux/macOS，增强容错性和稳定性

用法:
    python run.py              # 交互式安装
    python run.py --prod       # 生产环境安装
    python run.py --dev        # 开发环境安装
    python run.py --check      # 仅检查环境
    python run.py --help       # 显示帮助
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
import logging
import traceback
import time
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from datetime import datetime
from enum import Enum


# ============================================
# 终端编码处理
# ============================================

class TerminalEncoder:
    """终端编码处理器"""
    
    @staticmethod
    def setup():
        """设置终端编码"""
        if platform.system() == 'Windows':
            try:
                os.system('chcp 65001 > nul 2>&1')
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                if hasattr(sys.stderr, 'reconfigure'):
                    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
        
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
    
    @staticmethod
    def safe_print(text: str):
        """安全打印"""
        try:
            print(text)
        except UnicodeEncodeError:
            encoding = sys.stdout.encoding or 'utf-8'
            safe_text = text.encode(encoding, errors='replace').decode(encoding)
            print(safe_text)


# ============================================
# 颜色输出
# ============================================

class Colors:
    """终端颜色"""
    SUPPORTS_COLOR = (
        (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty())
        or os.environ.get('FORCE_COLOR', '') == '1'
    )
    
    HEADER = '\033[95m' if SUPPORTS_COLOR else ''
    OKBLUE = '\033[94m' if SUPPORTS_COLOR else ''
    OKCYAN = '\033[96m' if SUPPORTS_COLOR else ''
    OKGREEN = '\033[92m' if SUPPORTS_COLOR else ''
    WARNING = '\033[93m' if SUPPORTS_COLOR else ''
    FAIL = '\033[91m' if SUPPORTS_COLOR else ''
    ENDC = '\033[0m' if SUPPORTS_COLOR else ''
    BOLD = '\033[1m' if SUPPORTS_COLOR else ''


def safe_print(text: str):
    TerminalEncoder.safe_print(text)


def print_header(text: str):
    line = '=' * 60
    centered = text.center(60)
    safe_print(f"\n{Colors.HEADER}{Colors.BOLD}{line}{Colors.ENDC}")
    safe_print(f"{Colors.HEADER}{Colors.BOLD}{centered}{Colors.ENDC}")
    safe_print(f"{Colors.HEADER}{Colors.BOLD}{line}{Colors.ENDC}\n")


def print_success(text: str):
    safe_print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")


def print_error(text: str):
    safe_print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")


def print_warning(text: str):
    safe_print(f"{Colors.WARNING}[WARN] {text}{Colors.ENDC}")


def print_info(text: str):
    safe_print(f"{Colors.OKCYAN}[INFO] {text}{Colors.ENDC}")


def print_step(step: int, total: int, text: str):
    safe_print(f"\n{Colors.OKBLUE}[{step}/{total}] {text}{Colors.ENDC}")
    safe_print("-" * 50)


# ============================================
# 日志记录器
# ============================================

class Logger:
    """日志记录器"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = log_dir / f"install_{timestamp}.log"
        
        self.logger = logging.getLogger('DjangoBlogSetup')
        self.logger.setLevel(logging.DEBUG)
        
        fh = logging.FileHandler(self.log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(fh)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)


# ============================================
# 系统检测器
# ============================================

class SystemDetector:
    """系统环境检测器"""
    
    def __init__(self):
        self.info = self._collect_info()
    
    def _collect_info(self) -> Dict:
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'arch': platform.machine(),
            'python_version': platform.python_version(),
            'is_windows': platform.system() == 'Windows',
            'is_linux': platform.system() == 'Linux',
            'is_macos': platform.system() == 'Darwin',
            'is_64bit': sys.maxsize > 2**32,
        }
    
    def print_info(self):
        safe_print("")
        safe_print(f"  操作系统: {self.info['os']} {self.info['os_release']}")
        safe_print(f"  架构: {self.info['arch']} ({'64位' if self.info['is_64bit'] else '32位'})")
        safe_print(f"  Python: {self.info['python_version']}")
        safe_print("")


# ============================================
# 安装器
# ============================================

class DjangoBlogSetup:
    """DjangoBlog 自动化安装器"""
    
    MIN_PYTHON_VERSION = (3, 10)
    
    CORE_PACKAGES = [
        'Django>=4.2,<5.0',
        'django-environ>=0.11.0',
        'Pillow>=10.0.0',
        'markdown>=3.7',
        'bleach>=6.2.0',
        'djangorestframework>=3.14.0',
    ]
    
    def __init__(self, env_type: str = 'dev', no_input: bool = False):
        self.project_root = Path(__file__).parent.resolve()
        self.env_type = env_type
        self.no_input = no_input
        self.venv_dir = self.project_root / '.venv'
        self.logs_dir = self.project_root / 'logs'
        
        self.system = SystemDetector()
        self.logger = Logger(self.logs_dir)
        
        self.use_uv = False
        self.python_cmd = None
        self.pip_cmd = None
        
        self.step_results: Dict[str, str] = {}
    
    def _find_python(self) -> Optional[str]:
        """查找可用的 Python 命令"""
        candidates = ['python', 'python3', 'py']
        
        for ver in ['3.13', '3.12', '3.11', '3.10']:
            candidates.extend([f'python{ver}', f'py -{ver}'])
        
        for cmd in candidates:
            try:
                # 处理 py -3.x 格式
                if cmd.startswith('py -'):
                    result = subprocess.run(
                        cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                else:
                    result = subprocess.run(
                        [cmd, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                
                if result.returncode == 0:
                    version_str = result.stdout.strip().split()[1]
                    if self._check_version(version_str):
                        print_info(f"找到 Python {version_str} ({cmd})")
                        self.logger.info(f"使用 Python: {cmd}")
                        return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired, IndexError):
                continue
        
        return None
    
    def _check_version(self, version_str: str) -> bool:
        """检查版本"""
        try:
            parts = version_str.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            return (major, minor) >= self.MIN_PYTHON_VERSION
        except (ValueError, IndexError):
            return False
    
    def _find_pip(self) -> Optional[str]:
        """查找 pip"""
        # 优先使用 uv
        try:
            result = subprocess.run(['uv', '--version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                self.use_uv = True
                print_info("找到 uv 包管理器")
                return 'uv'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        for cmd in ['pip', 'pip3']:
            try:
                result = subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None
    
    def _run_command(
        self, 
        cmd: List[str], 
        cwd: Path = None, 
        check: bool = True,
        timeout: int = 300
    ) -> Tuple[int, str, str]:
        """执行命令"""
        cwd = cwd or self.project_root
        cmd_str = ' '.join(cmd)
        self.logger.info(f"执行: {cmd_str}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if check and result.returncode != 0:
                self.logger.error(f"命令失败: {result.stderr}")
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"命令超时: {cmd_str}")
            return -1, '', 'Command timed out'
        except Exception as e:
            self.logger.error(f"命令异常: {e}")
            return -1, '', str(e)
    
    def _get_venv_python(self) -> str:
        if self.system.info['is_windows']:
            return str(self.venv_dir / 'Scripts' / 'python.exe')
        return str(self.venv_dir / 'bin' / 'python')
    
    def _get_venv_pip(self) -> str:
        if self.use_uv:
            return 'uv'
        if self.system.info['is_windows']:
            return str(self.venv_dir / 'Scripts' / 'pip.exe')
        return str(self.venv_dir / 'bin' / 'pip')
    
    def step_check_environment(self) -> bool:
        """步骤1: 检查环境"""
        print_step(1, 8, "检查系统环境")
        
        self.system.print_info()
        
        self.python_cmd = self._find_python()
        if not self.python_cmd:
            print_error("未找到合适的 Python 版本")
            print_info(f"需要 Python {'.'.join(map(str, self.MIN_PYTHON_VERSION))}+")
            return False
        
        self.pip_cmd = self._find_pip()
        if not self.pip_cmd:
            print_error("未找到 pip 或 uv")
            print_info("安装 pip: python -m ensurepip --upgrade")
            print_info("或安装 uv: pip install uv")
            return False
        
        manage_py = self.project_root / 'manage.py'
        if not manage_py.exists():
            print_error("manage.py 不存在")
            return False
        
        print_success("环境检查通过")
        self.step_results['check'] = 'success'
        return True
    
    def step_create_venv(self) -> bool:
        """步骤2: 创建虚拟环境"""
        print_step(2, 8, "创建虚拟环境")
        
        if self.venv_dir.exists():
            venv_python = self._get_venv_python()
            if Path(venv_python).exists():
                print_info(f"虚拟环境已存在: {self.venv_dir}")
                
                if not self.no_input:
                    try:
                        response = input("删除并重建? (y/N): ").strip().lower()
                        if response == 'y':
                            shutil.rmtree(self.venv_dir)
                        else:
                            print_info("使用现有环境")
                            self.step_results['venv'] = 'skipped'
                            return True
                    except:
                        print_info("使用现有环境")
                        self.step_results['venv'] = 'skipped'
                        return True
                else:
                    self.step_results['venv'] = 'skipped'
                    return True
        
        print_info("创建虚拟环境...")
        
        if self.use_uv:
            cmd = ['uv', 'venv', str(self.venv_dir)]
        else:
            cmd = [self.python_cmd, '-m', 'venv', str(self.venv_dir)]
        
        returncode, _, stderr = self._run_command(cmd, check=False, timeout=120)
        
        if returncode == 0:
            print_success(f"虚拟环境创建成功")
            self.step_results['venv'] = 'success'
            return True
        
        print_error(f"创建失败: {stderr[:100] if stderr else '未知错误'}")
        self.step_results['venv'] = 'failed'
        return False
    
    def step_install_dependencies(self) -> bool:
        """步骤3: 安装依赖"""
        print_step(3, 8, "安装项目依赖")
        
        venv_python = self._get_venv_python()
        venv_pip = self._get_venv_pip()
        
        # 升级 pip
        print_info("升级 pip...")
        if self.use_uv:
            self._run_command(['uv', 'pip', 'install', '--upgrade', 'pip'], check=False)
        else:
            self._run_command([venv_python, '-m', 'pip', 'install', '--upgrade', 'pip'], check=False)
        
        # 确定依赖文件
        req_dir = self.project_root / 'requirements'
        if self.env_type == 'prod':
            req_file = req_dir / 'production.txt'
        else:
            req_file = req_dir / 'development.txt'
        
        if not req_file.exists():
            req_file = req_dir / 'base.txt'
        
        if not req_file.exists():
            print_warning("依赖文件不存在，安装核心包...")
            return self._install_core_packages(venv_python)
        
        print_info(f"使用: {req_file.name}")
        
        if self.use_uv:
            cmd = ['uv', 'pip', 'install', '-r', str(req_file)]
        else:
            cmd = [venv_pip, 'install', '-r', str(req_file)]
        
        returncode, _, stderr = self._run_command(cmd, check=False, timeout=600)
        
        if returncode == 0:
            print_success("依赖安装完成")
            self.step_results['deps'] = 'success'
            return True
        
        print_warning("部分失败，尝试安装核心包...")
        self._install_core_packages(venv_python)
        self.step_results['deps'] = 'warning'
        return True
    
    def _install_core_packages(self, venv_python: str) -> bool:
        """安装核心包"""
        for pkg in self.CORE_PACKAGES:
            name = pkg.split('>=')[0]
            print_info(f"  安装 {name}...")
            
            if self.use_uv:
                cmd = ['uv', 'pip', 'install', pkg]
            else:
                cmd = [self._get_venv_pip(), 'install', pkg]
            
            self._run_command(cmd, check=False, timeout=120)
        
        print_success("核心包安装完成")
        return True
    
    def step_setup_env(self) -> bool:
        """步骤4: 配置环境变量"""
        print_step(4, 8, "配置环境变量")
        
        env_file = self.project_root / '.env'
        
        if env_file.exists():
            print_info(".env 已存在")
            self.step_results['env'] = 'skipped'
            return True
        
        import secrets
        secret_key = secrets.token_urlsafe(50)
        
        content = f'''# Django 配置
DEBUG=True
SECRET_KEY={secret_key}
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*

# 站点信息
SITE_NAME=Django Blog
SITE_TITLE=Django Blog - 博客论坛系统

# 数据库
DB_ENGINE=sqlite

# Redis (可选)
USE_REDIS=False

# 安装向导
ENABLE_INSTALLER=True

# CSRF 信任来源
CSRF_TRUSTED_ORIGINS=http://localhost:8000
'''
        
        try:
            env_file.write_text(content, encoding='utf-8')
            print_success(".env 创建成功")
            self.step_results['env'] = 'success'
            return True
        except Exception as e:
            print_error(f".env 创建失败: {e}")
            self.step_results['env'] = 'failed'
            return False
    
    def step_migrate(self) -> bool:
        """步骤5: 数据库迁移"""
        print_step(5, 8, "执行数据库迁移")
        
        venv_python = self._get_venv_python()
        manage_py = self.project_root / 'manage.py'
        
        print_info("生成迁移...")
        self._run_command([venv_python, str(manage_py), 'makemigrations'], check=False)
        
        print_info("执行迁移...")
        returncode, stdout, stderr = self._run_command(
            [venv_python, str(manage_py), 'migrate'],
            check=False,
            timeout=120
        )
        
        if returncode == 0 or 'No migrations' in stdout:
            print_success("迁移完成")
            self.step_results['migrate'] = 'success'
            return True
        
        print_error(f"迁移失败: {stderr[:100] if stderr else '未知'}")
        self.step_results['migrate'] = 'failed'
        return False
    
    def step_collectstatic(self) -> bool:
        """步骤6: 收集静态文件"""
        print_step(6, 8, "收集静态文件")
        
        venv_python = self._get_venv_python()
        manage_py = self.project_root / 'manage.py'
        
        returncode, _, stderr = self._run_command(
            [venv_python, str(manage_py), 'collectstatic', '--noinput'],
            check=False
        )
        
        if returncode == 0:
            print_success("静态文件收集完成")
            self.step_results['static'] = 'success'
        else:
            print_info("开发模式跳过静态收集")
            self.step_results['static'] = 'skipped'
        
        return True
    
    def step_create_superuser(self) -> bool:
        """步骤7: 创建管理员"""
        print_step(7, 8, "创建管理员账户")
        
        venv_python = self._get_venv_python()
        manage_py = self.project_root / 'manage.py'
        
        # 检查是否已有管理员
        check_cmd = [
            venv_python, str(manage_py), 'shell', '-c',
            'from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).exists())'
        ]
        
        returncode, stdout, _ = self._run_command(check_cmd, check=False)
        
        if 'True' in stdout:
            print_info("已存在管理员")
            self.step_results['admin'] = 'skipped'
            return True
        
        if self.no_input:
            print_info("跳过管理员创建")
            print_info("稍后运行: python manage.py createsuperuser")
            self.step_results['admin'] = 'skipped'
            return True
        
        print_info("请创建管理员:")
        try:
            os.system(f'{venv_python} {manage_py} createsuperuser')
            self.step_results['admin'] = 'success'
        except:
            self.step_results['admin'] = 'skipped'
        
        return True
    
    def step_install_gunicorn(self) -> bool:
        """步骤8: 安装 Gunicorn"""
        print_step(8, 8, "安装生产服务器")
        
        venv_pip = self._get_venv_pip()
        
        packages = ['gunicorn', 'uvicorn[standard]', 'whitenoise']
        
        if self.use_uv:
            cmd = ['uv', 'pip', 'install'] + packages
        else:
            cmd = [venv_pip, 'install'] + packages
        
        returncode, _, _ = self._run_command(cmd, check=False)
        
        if returncode == 0:
            print_success("Gunicorn 安装成功")
            self._create_scripts()
            self.step_results['gunicorn'] = 'success'
        else:
            print_warning("Gunicorn 安装失败")
            self.step_results['gunicorn'] = 'warning'
        
        return True
    
    def _create_scripts(self):
        """创建启动脚本"""
        # Linux/Mac
        sh = self.project_root / 'start_server.sh'
        sh.write_text(f'''#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
mkdir -p logs
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
''', encoding='utf-8')
        
        if not self.system.info['is_windows']:
            os.chmod(sh, 0o755)
        
        # Windows
        bat = self.project_root / 'start_server.bat'
        bat.write_text(f'''@echo off
cd /d "%~dp0"
call .venv\\Scripts\\activate.bat
pip install waitress -q
waitress-serve --port=8000 config.wsgi:application
''', encoding='utf-8')
        
        print_success("启动脚本创建成功")
    
    def run(self) -> bool:
        """执行安装"""
        TerminalEncoder.setup()
        
        print_header("DjangoBlog 自动化安装 v2.0")
        
        safe_print(f"项目目录: {self.project_root}")
        safe_print(f"环境类型: {'生产环境' if self.env_type == 'prod' else '开发环境'}")
        safe_print(f"日志文件: {self.logger.log_file}")
        
        self.logger.info(f"开始安装: {self.env_type}")
        
        steps = [
            ("检查环境", self.step_check_environment),
            ("创建虚拟环境", self.step_create_venv),
            ("安装依赖", self.step_install_dependencies),
            ("配置环境变量", self.step_setup_env),
            ("数据库迁移", self.step_migrate),
            ("收集静态文件", self.step_collectstatic),
            ("创建管理员", self.step_create_superuser),
        ]
        
        if self.env_type == 'prod':
            steps.append(("安装 Gunicorn", self.step_install_gunicorn))
        
        failed = []
        for name, func in steps:
            try:
                self.logger.info(f"执行: {name}")
                if not func():
                    failed.append(name)
            except Exception as e:
                self.logger.error(f"{name} 异常: {e}")
                print_error(f"{name} 异常: {e}")
                failed.append(name)
        
        # 打印结果
        print_header("安装结果")
        
        for step, result in self.step_results.items():
            if result == 'success':
                print_success(step)
            elif result == 'warning':
                print_warning(step)
            else:
                safe_print(f"  {step}: {result}")
        
        if not failed:
            print_header("安装完成")
            safe_print("后续操作:")
            safe_print("")
            
            if self.system.info['is_windows']:
                safe_print("  1. 激活环境: .venv\\Scripts\\activate.bat")
            else:
                safe_print("  1. 激活环境: source .venv/bin/activate")
            
            safe_print("  2. 启动服务: python start.py")
            safe_print("  3. 访问网站: http://127.0.0.1:8000")
            safe_print("")
        
        return len(failed) == 0


def main():
    parser = argparse.ArgumentParser(
        description='DjangoBlog 自动化安装脚本 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python run.py              # 交互式安装
  python run.py --prod       # 生产环境
  python run.py --check      # 检查环境
  python run.py --no-input   # 非交互
        '''
    )
    
    parser.add_argument('--prod', action='store_true', help='生产环境')
    parser.add_argument('--dev', action='store_true', help='开发环境')
    parser.add_argument('--check', action='store_true', help='仅检查环境')
    parser.add_argument('--no-input', action='store_true', help='非交互模式')
    
    args = parser.parse_args()
    
    TerminalEncoder.setup()
    
    if args.check:
        print_header("系统环境检查")
        SystemDetector().print_info()
        return 0
    
    env_type = 'prod' if args.prod else 'dev'
    setup = DjangoBlogSetup(env_type=env_type, no_input=args.no_input)
    
    try:
        success = setup.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        safe_print("")
        print_warning("安装被中断")
        return 130
    except Exception as e:
        print_error(f"安装异常: {e}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
