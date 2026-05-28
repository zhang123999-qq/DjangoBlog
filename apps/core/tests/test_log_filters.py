"""
日志敏感信息过滤器测试
"""

import logging

import pytest

from apps.core.log_filters import SanitizeLogFilter, SensitiveDataFilter


class TestSensitiveDataFilter:
    """敏感信息过滤器测试"""

    @pytest.fixture
    def filter_instance(self):
        return SensitiveDataFilter()

    def test_filter_password(self, filter_instance):
        """测试密码脱敏"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg='User login with password="mySecretPass123"',
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "mySecretPass123" not in record.msg

    def test_filter_secret_key(self, filter_instance):
        """测试密钥脱敏"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Config: secret_key=abc123def456",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "abc123def456" not in record.msg

    def test_filter_token(self, filter_instance):
        """测试 Token 脱敏"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg='API call with token="abc123xyz"',
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "abc123xyz" not in record.msg

    def test_filter_api_key(self, filter_instance):
        """测试 API Key 脱敏"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Request headers: api_key: sk_live_test_key",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "sk_live_test_key" not in record.msg

    def test_preserve_non_sensitive(self, filter_instance):
        """测试保留非敏感信息"""
        original_msg = "User logged in successfully"
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=original_msg,
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert record.msg == original_msg

    def test_preserve_django_server_access_log_args(self, filter_instance):
        """测试保留 Django 开发服务器访问日志参数"""
        original_args = ("GET /blog/ HTTP/1.1", "200", "1234")
        record = logging.LogRecord(
            name="django.server",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg='"%s" %s %s',
            args=original_args,
            exc_info=None,
        )

        filter_instance.filter(record)

        assert record.args == original_args
        assert record.getMessage() == '"GET /blog/ HTTP/1.1" 200 1234'

    def test_preserve_non_sensitive_string_args(self, filter_instance):
        """测试保留非敏感字符串参数"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Loaded tool %s from %s",
            args=("json_formatter", "/tools/json/"),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert record.getMessage() == "Loaded tool json_formatter from /tools/json/"

    def test_filter_sensitive_value_in_string_args(self, filter_instance):
        """测试格式化参数中的敏感值仍会脱敏"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="User login with password=%s",
            args=("mySecretPass123",),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "mySecretPass123" not in record.getMessage()
        assert "password=" in record.getMessage()


class TestSanitizeLogFilter:
    """简化版过滤器测试"""

    @pytest.fixture
    def filter_instance(self):
        return SanitizeLogFilter()

    def test_sanitize_password(self, filter_instance):
        """测试密码脱敏"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="password=secret123",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "secret123" not in record.msg

    def test_sanitize_token(self, filter_instance):
        """测试 Token 脱敏"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="token: abc123xyz",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "abc123xyz" not in record.msg
