"""
日志敏感信息过滤器

自动脱敏日志中的敏感信息：
- 密码
- Secret Key
- Token
- API Key
- 邮箱（部分脱敏）
- 手机号（部分脱敏）
- 身份证号（部分脱敏）
"""

import logging
import re
from typing import Any, Dict, List, Optional, Pattern, Tuple


class SensitiveDataFilter(logging.Filter):
    """
    敏感信息过滤器

    使用方法:
        # settings.py
        LOGGING = {
            'filters': {
                'sensitive_data': {
                    '()': 'apps.core.log_filters.SensitiveDataFilter',
                    'mask_char': '*',
                    'sensitive_keys': ['password', 'secret', 'token'],
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'filters': ['sensitive_data'],
                }
            }
        }
    """

    # 默认敏感字段名
    DEFAULT_SENSITIVE_KEYS = [
        'password',
        'passwd',
        'pwd',
        'secret',
        'secret_key',
        'secretkey',
        'api_key',
        'apikey',
        'api_secret',
        'apisecret',
        'token',
        'access_token',
        'accesstoken',
        'refresh_token',
        'refreshtoken',
        'auth',
        'authorization',
        'credential',
        'private_key',
        'privatekey',
        'session_key',
        'sessionkey',
        'csrf',
        'csrf_token',
        'csrftoken',
    ]

    # 部分脱敏的字段（保留部分信息）
    PARTIAL_MASK_KEYS = [
        'email',
        'phone',
        'mobile',
        'id_card',
        'idcard',
        'credit_card',
        'creditcard',
    ]

    # 正则匹配模式
    PATTERNS: List[Tuple[Pattern, str]] = [
        # JWT Token
        (re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'), '***JWT***'),
        # UUID Token
        (re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', re.I), '***UUID***'),
        # AWS Key
        (re.compile(r'AKIA[0-9A-Z]{16}'), '***AWS_KEY***'),
        # Generic API Key (32-64 hex chars)
        (re.compile(r'\b[a-f0-9]{32,64}\b', re.I), '***API_KEY***'),
    ]

    def __init__(
        self,
        name: str = '',
        mask_char: str = '*',
        sensitive_keys: Optional[List[str]] = None,
        partial_mask_keys: Optional[List[str]] = None,
    ):
        """
        初始化过滤器

        Args:
            name: 过滤器名称
            mask_char: 脱敏字符
            sensitive_keys: 自定义敏感字段名列表
            partial_mask_keys: 自定义部分脱敏字段名列表
        """
        super().__init__(name)
        self.mask_char = mask_char
        self.sensitive_keys = sensitive_keys or self.DEFAULT_SENSITIVE_KEYS
        self.partial_mask_keys = partial_mask_keys or self.PARTIAL_MASK_KEYS

        # 编译字段匹配正则
        key_pattern = '|'.join(re.escape(k) for k in self.sensitive_keys)
        self.sensitive_pattern = re.compile(
            rf'({key_pattern})["\s:=]+(["\']?)([^\s"\',\]]+)',
            re.I
        )

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录

        Args:
            record: 日志记录对象

        Returns:
            bool: 总是返回 True（允许记录通过，但会修改内容）
        """
        # 处理消息
        if record.msg and isinstance(record.msg, str):
            record.msg = self._mask_sensitive_data(record.msg)

        # 处理参数
        if record.args:
            if isinstance(record.args, dict):
                record.args = self._mask_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._mask_value(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True

    def _mask_sensitive_data(self, message: str) -> str:
        """
        脱敏消息中的敏感数据

        Args:
            message: 原始消息

        Returns:
            str: 脱敏后的消息
        """
        # 1. 正则模式替换
        for pattern, replacement in self.PATTERNS:
            message = pattern.sub(replacement, message)

        # 2. 键值对替换
        message = self.sensitive_pattern.sub(
            lambda m: f'{m.group(1)}{m.group(2)}{self._mask_value(m.group(3))}',
            message
        )

        return message

    def _mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        脱敏字典中的敏感值

        Args:
            data: 原始字典

        Returns:
            Dict: 脱敏后的字典
        """
        result = {}
        for key, value in data.items():
            lower_key = key.lower().replace('-', '_')

            if lower_key in self.sensitive_keys:
                result[key] = self._mask_value(str(value))
            elif lower_key in self.partial_mask_keys:
                result[key] = self._partial_mask(str(value), lower_key)
            elif isinstance(value, dict):
                result[key] = self._mask_dict(value)
            elif isinstance(value, str):
                result[key] = self._mask_sensitive_data(value)
            else:
                result[key] = value

        return result

    def _mask_value(self, value: str) -> str:
        """
        完全脱敏值

        Args:
            value: 原始值

        Returns:
            str: 脱敏后的值
        """
        if not value:
            return value

        # 保留前后各 2 个字符（如果够长）
        if len(value) > 6:
            return value[:2] + self.mask_char * (len(value) - 4) + value[-2:]
        return self.mask_char * len(value)

    def _partial_mask(self, value: str, key: str) -> str:
        """
        部分脱敏（保留部分可识别信息）

        Args:
            value: 原始值
            key: 字段名

        Returns:
            str: 脱敏后的值
        """
        if not value:
            return value

        key_lower = key.lower()

        # 邮箱脱敏：t***@example.com
        if 'email' in key_lower and '@' in value:
            parts = value.split('@')
            if len(parts[0]) > 1:
                parts[0] = parts[0][0] + self.mask_char * (len(parts[0]) - 1)
            return '@'.join(parts)

        # 手机号脱敏：138****8888
        if 'phone' in key_lower or 'mobile' in key_lower:
            if len(value) >= 7:
                return value[:3] + self.mask_char * 4 + value[-4:]
            return self._mask_value(value)

        # 身份证脱敏：110***********1234
        if 'id_card' in key_lower or 'idcard' in key_lower:
            if len(value) >= 8:
                return value[:3] + self.mask_char * (len(value) - 7) + value[-4:]
            return self._mask_value(value)

        # 默认部分脱敏
        if len(value) > 4:
            return value[:2] + self.mask_char * (len(value) - 4) + value[-2:]
        return self.mask_char * len(value)


class SanitizeLogFilter(logging.Filter):
    """
    简化版日志过滤器

    只处理消息字符串，不处理参数
    """

    SENSITIVE_PATTERNS = [
        # Password patterns
        (re.compile(r'(password["\']?\s*[:=]\s*["\']?)([^"\',\s]+)', re.I), r'\1***'),
        (re.compile(r'(passwd["\']?\s*[:=]\s*["\']?)([^"\',\s]+)', re.I), r'\1***'),
        (re.compile(r'(pwd["\']?\s*[:=]\s*["\']?)([^"\',\s]+)', re.I), r'\1***'),
        # Secret patterns
        (re.compile(r'(secret[_-]?key["\']?\s*[:=]\s*["\']?)([^"\',\s]+)', re.I), r'\1***'),
        (re.compile(r'(secret["\']?\s*[:=]\s*["\']?)([^"\',\s]+)', re.I), r'\1***'),
        # Token patterns
        (re.compile(r'(token["\']?\s*[:=]\s*["\']?)([^"\',\s]+)', re.I), r'\1***'),
        (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\',\s]+)', re.I), r'\1***'),
        (re.compile(r'(authorization["\']?\s*[:=]\s*["\']?)([^"\',\s]+)', re.I), r'\1***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录"""
        if isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)

        return True


def setup_logging_filters():
    """
    为所有处理器添加敏感信息过滤器

    使用方法:
        # 在 settings.py 或启动时调用
        from apps.core.log_filters import setup_logging_filters
        setup_logging_filters()
    """
    root_logger = logging.getLogger()

    sensitive_filter = SensitiveDataFilter()

    for handler in root_logger.handlers:
        handler.addFilter(sensitive_filter)

    # 也添加到 Django 请求日志
    django_request_logger = logging.getLogger('django.request')
    for handler in django_request_logger.handlers:
        handler.addFilter(sensitive_filter)
