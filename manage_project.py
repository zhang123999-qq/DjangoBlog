#!/usr/bin/env python
"""
Django Blog 项目管理脚本
用法: python manage_project.py [命令]
"""
import os
import sys
import subprocess
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent


def run_command(cmd, cwd=None):
    """运行命令"""
    if cwd is None:
        cwd = BASE_DIR
    print(f"\n🔧 执行: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode


def install_dev():
    """安装开发依赖"""
    print("📦 安装开发依赖...")
    return run_command("uv pip install -r requirements/development.txt")


def install_prod():
    """安装生产依赖"""
    print("📦 安装生产依赖...")
    return run_command("uv pip install -r requirements/production.txt")


def clean():
    """清理缓存和临时文件"""
    print("🧹 清理缓存和临时文件...")
    
    # 清理 __pycache__
    for pycache in BASE_DIR.rglob("__pycache__"):
        print(f"  删除: {pycache}")
        import shutil
        shutil.rmtree(pycache, ignore_errors=True)
    
    # 清理 .pyc 文件
    for pyc in BASE_DIR.rglob("*.pyc"):
        pyc.unlink(missing_ok=True)
    
    # 清理 .pytest_cache
    pytest_cache = BASE_DIR / ".pytest_cache"
    if pytest_cache.exists():
        import shutil
        shutil.rmtree(pytest_cache, ignore_errors=True)
        print(f"  删除: {pytest_cache}")
    
    # 清理 tmp 目录
    tmp_dir = BASE_DIR / "tmp"
    if tmp_dir.exists():
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print(f"  删除: {tmp_dir}")
    
    print("✅ 清理完成!")
    return 0


def test():
    """运行测试"""
    print("🧪 运行测试...")
    return run_command("pytest tests/ -v --html=tests/report.html --self-contained-html")


def test_security():
    """运行安全测试"""
    print("🔒 运行安全测试...")
    return run_command("pytest tests/test_security.py -v")


def lint():
    """代码检查"""
    print("🔍 代码检查...")
    run_command("flake8 apps/ config/ --max-line-length=120 --exclude=__pycache__,migrations")
    run_command("black --check apps/ config/ --line-length=120")
    return 0


def format_code():
    """格式化代码"""
    print("✨ 格式化代码...")
    run_command("black apps/ config/ --line-length=120")
    run_command("isort apps/ config/ --profile black")
    return 0


def migrate():
    """数据库迁移"""
    print("🗃️ 执行数据库迁移...")
    run_command("python manage.py makemigrations")
    run_command("python manage.py migrate")
    return 0


def run_server():
    """启动开发服务器"""
    print("🚀 启动开发服务器 (http://127.0.0.1:18789)...")
    return run_command("python manage.py runserver 0.0.0.0:18789")


def run_lan():
    """局域网运行"""
    print("🌐 启动局域网服务器...")
    return run_command("run_lan.bat")


def collectstatic():
    """收集静态文件"""
    print("📁 收集静态文件...")
    return run_command("python manage.py collectstatic --noinput")


def help():
    """显示帮助"""
    print("""
Django Blog 项目管理脚本
用法: python manage_project.py [命令]

可用命令:
  install-dev    安装开发依赖
  install-prod   安装生产依赖
  clean          清理缓存和临时文件
  test           运行测试
  test-security  运行安全测试
  lint           代码检查
  format         格式化代码
  migrate        数据库迁移
  run            启动开发服务器
  run-lan        启动局域网服务器
  collectstatic  收集静态文件
  help           显示帮助
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        help()
        sys.exit(0)
    
    command = sys.argv[1]
    commands = {
        "install-dev": install_dev,
        "install-prod": install_prod,
        "clean": clean,
        "test": test,
        "test-security": test_security,
        "lint": lint,
        "format": format_code,
        "migrate": migrate,
        "run": run_server,
        "run-lan": run_lan,
        "collectstatic": collectstatic,
        "help": help,
    }
    
    if command in commands:
        sys.exit(commands[command]())
    else:
        print(f"❌ 未知命令: {command}")
        help()
        sys.exit(1)
