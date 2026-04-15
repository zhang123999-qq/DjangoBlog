#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Django Blog 项目管理脚本
用法: python manage_project.py [命令]
"""

import sys
import subprocess
import shutil
import shlex
from pathlib import Path

# 项目根目录（scripts 的父目录）
BASE_DIR = Path(__file__).resolve().parent.parent


def safe_print(text):
    """安全打印，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 移除 emoji
        text = text.encode("ascii", "ignore").decode("ascii")
        print(text)


def run_command(cmd, cwd=None):
    """运行命令（默认禁用 shell=True，降低命令注入风险）"""
    if cwd is None:
        cwd = BASE_DIR

    if isinstance(cmd, str):
        cmd_args = shlex.split(cmd)
        display_cmd = cmd
    else:
        cmd_args = cmd
        display_cmd = " ".join(cmd)

    safe_print(f"\n[执行] {display_cmd}")
    result = subprocess.run(cmd_args, shell=False, cwd=cwd)
    return result.returncode


def install_dev():
    """安装开发依赖"""
    safe_print("[安装] 开发依赖...")
    return run_command("uv pip install -r requirements/development.txt")


def install_prod():
    """安装生产依赖"""
    safe_print("[安装] 生产依赖...")
    return run_command("uv pip install -r requirements/production.txt")


def clean():
    """清理缓存和临时文件"""
    safe_print("[清理] 缓存和临时文件...")

    count = 0

    # 排除目录（不清理虚拟环境和版本控制目录）
    EXCLUDE_DIRS = {".venv", ".git", "node_modules"}

    # 清理 __pycache__（排除 .venv）
    for pycache in BASE_DIR.rglob("__pycache__"):
        if any(excluded in pycache.parts for excluded in EXCLUDE_DIRS):
            continue
        try:
            shutil.rmtree(pycache, ignore_errors=True)
            count += 1
        except Exception:
            pass

    # 清理 .pyc 文件（排除 .venv）
    for pyc in BASE_DIR.rglob("*.pyc"):
        if any(excluded in pyc.parts for excluded in EXCLUDE_DIRS):
            continue
        try:
            pyc.unlink(missing_ok=True)
            count += 1
        except Exception:
            pass

    # 清理 .pytest_cache
    pytest_cache = BASE_DIR / ".pytest_cache"
    if pytest_cache.exists():
        shutil.rmtree(pytest_cache, ignore_errors=True)
        count += 1

    # 清理 htmlcov（测试覆盖率报告）
    htmlcov_dir = BASE_DIR / "htmlcov"
    if htmlcov_dir.exists():
        shutil.rmtree(htmlcov_dir, ignore_errors=True)
        count += 1

    # 清理 tmp 目录
    tmp_dir = BASE_DIR / "tmp"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
        count += 1

    # 清理 allure 报告
    allure_dir = BASE_DIR / "allure-results"
    if allure_dir.exists():
        shutil.rmtree(allure_dir, ignore_errors=True)
        count += 1

    safe_print(f"[完成] 已清理 {count} 项")
    return 0


def test():
    """运行测试"""
    safe_print("[测试] 运行测试套件 (pytest)...")
    return run_command("uv run pytest")


def test_security():
    """运行安全测试"""
    safe_print("[安全] 运行安全测试...")
    return run_command("uv run python manage.py check --deploy")


def lint():
    """代码检查"""
    safe_print("[检查] 代码质量...")
    run_command("uv run flake8 apps/ config/ --max-line-length=120 --exclude=__pycache__,migrations,.venv")
    return 0


def format_code():
    """格式化代码"""
    safe_print("[格式化] 代码...")
    run_command("uv run black apps/ config/ --line-length=120")
    run_command("uv run isort apps/ config/ --profile black")
    return 0


def migrate():
    """数据库迁移"""
    safe_print("[迁移] 数据库...")
    run_command("uv run python manage.py makemigrations")
    run_command("uv run python manage.py migrate")
    return 0


def run_server():
    """启动开发服务器"""
    safe_print("[启动] 开发服务器 (http://127.0.0.1:8000)...")
    return run_command("uv run python manage.py runserver 0.0.0.0:8000")


def run_lan():
    """局域网运行"""
    safe_print("[启动] 局域网服务器...")
    return run_command("uv run python manage.py runserver 0.0.0.0:8000")


def collectstatic():
    """收集静态文件"""
    safe_print("[收集] 静态文件...")
    return run_command("uv run python manage.py collectstatic --noinput")


def show_help():
    """显示帮助"""
    print("""
Django Blog 项目管理脚本
用法: python scripts/manage_project.py [命令]

可用命令:
  install-dev    安装开发依赖
  install-prod   安装生产依赖
  clean          清理缓存和临时文件
  test           运行测试
  test-security  运行安全检查
  lint           代码检查
  format         格式化代码
  migrate        数据库迁移
  run            启动开发服务器
  run-lan        启动局域网服务器
  collectstatic  收集静态文件
  help           显示帮助

示例:
  python scripts/manage_project.py clean
  python scripts/manage_project.py test
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
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
        "help": show_help,
    }

    if command in commands:
        sys.exit(commands[command]())
    else:
        print(f"[错误] 未知命令: {command}")
        show_help()
        sys.exit(1)
