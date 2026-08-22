"""
性能基准测试配置

使用 pytest-benchmark 进行性能回归检测
"""

import pytest

# 基准测试配置
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "benchmark: marks tests as performance benchmarks"
    )