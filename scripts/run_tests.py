#!/usr/bin/env python
"""
测试运行脚本

使用方法:
    python scripts/run_tests.py              # 运行所有测试
    python scripts/run_tests.py --cov        # 运行测试并生成覆盖率报告
    python scripts/run_tests.py --quick      # 快速测试（跳过慢测试）
    python scripts/run_tests.py --security   # 只运行安全测试
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"运行: {' '.join(cmd)}")
    print("=" * 60)

    result = subprocess.run(
        cmd,
        cwd=cwd or Path(__file__).parent.parent,
    )
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="DjangoBlog 测试运行器")
    parser.add_argument("--cov", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--quick", action="store_true", help="快速测试（跳过慢测试）")
    parser.add_argument("--security", action="store_true", help="只运行安全测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--api", action="store_true", help="只运行 API 测试")
    parser.add_argument("--smoke", action="store_true", help="只运行冒烟测试")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("path", nargs="?", default="apps/", help="测试路径")

    args = parser.parse_args()

    # 基础命令
    cmd = ["pytest"]

    # 测试路径
    if args.security:
        cmd.extend(["-m", "security", "apps/core/tests/test_security.py"])
    elif args.integration:
        cmd.extend(["-m", "integration", "tests/"])
    elif args.api:
        cmd.extend(["-m", "api", "apps/api/tests/"])
    elif args.smoke:
        cmd.extend(["-m", "smoke"])
    elif args.quick:
        cmd.extend(["-m", "not slow", args.path])
    else:
        cmd.append(args.path)

    # 覆盖率
    if args.cov:
        cmd.extend(
            [
                "--cov=apps",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-fail-under=50",
            ]
        )

    # 详细输出
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # 运行测试
    returncode = run_command(cmd)

    if args.cov:
        print("\n" + "=" * 60)
        print("覆盖率报告已生成: htmlcov/index.html")
        print("=" * 60)

    return returncode


if __name__ == "__main__":
    sys.exit(main())
