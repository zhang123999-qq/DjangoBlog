"""
Pytest 配置文件
提供测试 fixtures 和通用配置
"""

import pytest
from django.test import Client


# ============================================================
# 标记注册
# ============================================================
def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line("markers", "slow: 标记慢测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "api: API 测试")
    config.addinivalue_line("markers", "security: 安全测试")


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def client():
    """测试客户端"""
    return Client()


@pytest.fixture
def user_data():
    """用户测试数据"""
    return {"username": "testuser", "email": "test@example.com", "password": "TestPassword123!", "nickname": "测试用户"}


@pytest.fixture
def admin_data():
    """管理员测试数据"""
    return {"username": "admin", "email": "admin@example.com", "password": "AdminPassword123!"}


@pytest.fixture
def category_data():
    """分类测试数据"""
    return {
        "name": "测试分类",
    }


@pytest.fixture
def tag_data():
    """标签测试数据"""
    return {
        "name": "测试标签",
    }


@pytest.fixture
def post_data():
    """文章测试数据"""
    return {
        "title": "测试文章标题",
        "content": "这是测试文章的内容，包含足够长的文本。",
        "summary": "这是文章摘要",
        "status": "published",
    }


@pytest.fixture
def board_data():
    """版块测试数据"""
    return {"name": "测试版块", "description": "这是一个测试版块的描述"}


@pytest.fixture
def topic_data():
    """主题测试数据"""
    return {"title": "测试主题标题", "content": "这是测试主题的内容"}
