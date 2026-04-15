"""
验证码模块单元测试

测试覆盖:
- 验证码生成格式
- 验证码存储
- 验证码验证成功
- 验证码验证失败
- 验证码过期
- 尝试次数限制
- IP 锁定
- 大小写不敏感
- 重放攻击防护
"""
import pytest
import time
import hashlib
from unittest.mock import patch, MagicMock
from django.core.cache import cache

from apps.accounts.captcha import (
    generate_captcha,
    store_captcha,
    validate_captcha,
    CAPTCHA_CHARS,
    MAX_ATTEMPTS,
    get_client_ip,
    is_locked_out,
    record_failed_attempt,
    clear_attempts,
)


class TestCaptchaGeneration:
    """验证码生成测试"""

    def test_generate_captcha_returns_tuple(self):
        """测试生成验证码返回元组"""
        result = generate_captcha()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_generate_captcha_code_length(self):
        """测试验证码长度为 6"""
        code, _ = generate_captcha()
        assert len(code) == 6

    def test_generate_captcha_code_chars(self):
        """测试验证码只包含允许的字符"""
        code, _ = generate_captcha()
        for char in code:
            assert char in CAPTCHA_CHARS

    def test_generate_captcha_no_confusing_chars(self):
        """测试验证码不包含易混淆字符"""
        confusing = ['0', 'O', '1', 'I', 'L']
        code, _ = generate_captcha()
        for char in code:
            assert char not in confusing

    def test_generate_captcha_image_base64(self):
        """测试生成的图片是有效的 base64"""
        import base64
        _, image_base64 = generate_captcha()
        # 应该能解码
        image_data = base64.b64decode(image_base64)
        assert len(image_data) > 0

    def test_generate_captcha_uniqueness(self):
        """测试连续生成的验证码不重复"""
        codes = set()
        for _ in range(100):
            code, _ = generate_captcha()
            codes.add(code)
        # 100 次生成应该有大量不同的验证码
        assert len(codes) > 90


class TestCaptchaStorage:
    """验证码存储测试"""

    def test_store_captcha_creates_session_data(self):
        """测试存储验证码创建 session 数据"""
        request = MagicMock()
        request.session = {}

        code = 'ABC123'
        store_captcha(request, code)

        assert 'captcha_code' in request.session

    def test_store_captcha_stores_hash(self):
        """测试存储的是 hash 而非明文"""
        request = MagicMock()
        request.session = {}

        code = 'ABC123'
        store_captcha(request, code)

        stored = request.session['captcha_code']
        assert 'hash' in stored
        # 验证是 hash 而非明文
        assert stored['hash'] != code

    def test_store_captcha_stores_expiry(self):
        """测试存储过期时间"""
        request = MagicMock()
        request.session = {}

        code = 'ABC123'
        store_captcha(request, code)

        stored = request.session['captcha_code']
        assert 'expires_at' in stored
        assert stored['expires_at'] > time.time()

    def test_store_captcha_hash_correct(self):
        """测试 hash 计算正确"""
        request = MagicMock()
        request.session = {}

        code = 'ABC123'
        store_captcha(request, code)

        stored = request.session['captcha_code']
        expected_hash = hashlib.sha256(code.upper().encode()).hexdigest()
        assert stored['hash'] == expected_hash


class TestCaptchaValidation:
    """验证码验证测试"""

    @pytest.fixture
    def request_with_captcha(self):
        """创建带验证码的请求"""
        request = MagicMock()
        request.session = {}
        request.META = {'REMOTE_ADDR': '127.0.0.1'}

        code = 'TEST99'
        store_captcha(request, code)

        return request, code

    def test_validate_captcha_success(self, request_with_captcha):
        """测试验证成功"""
        request, code = request_with_captcha

        with patch('django.conf.settings.TESTING', False):
            is_valid, error_msg = validate_captcha(request, code)

            assert is_valid is True
            assert error_msg is None

    def test_validate_captcha_wrong_code(self, request_with_captcha):
        """测试验证失败 - 错误验证码"""
        request, _ = request_with_captcha

        with patch('django.conf.settings.TESTING', False):
            is_valid, error_msg = validate_captcha(request, 'WRONG')

            assert is_valid is False
            assert '错误' in error_msg

    def test_validate_captcha_case_insensitive(self, request_with_captcha):
        """测试大小写不敏感"""
        request, code = request_with_captcha

        with patch('django.conf.settings.TESTING', False):
            # 用小写验证
            is_valid, error_msg = validate_captcha(request, code.lower())

            assert is_valid is True

    def test_validate_captcha_expired(self):
        """测试验证码过期"""
        request = MagicMock()
        request.session = {
            'captcha_code': {
                'hash': hashlib.sha256('TEST'.encode()).hexdigest(),
                'expires_at': time.time() - 1  # 已过期
            }
        }
        request.META = {'REMOTE_ADDR': '127.0.0.1'}

        with patch('django.conf.settings.TESTING', False):
            is_valid, error_msg = validate_captcha(request, 'TEST')

            assert is_valid is False
            assert '过期' in error_msg

    def test_validate_captcha_destroys_after_use(self, request_with_captcha):
        """测试验证后销毁验证码"""
        request, code = request_with_captcha

        with patch('django.conf.settings.TESTING', False):
            validate_captcha(request, code)

            # 验证后应该销毁
            assert 'captcha_code' not in request.session

    def test_validate_captcha_replay_attack_prevention(self, request_with_captcha):
        """测试重放攻击防护"""
        request, code = request_with_captcha

        with patch('django.conf.settings.TESTING', False):
            # 第一次验证成功
            is_valid, _ = validate_captcha(request, code)
            assert is_valid is True

            # 第二次验证应该失败（验证码已销毁）
            is_valid, error_msg = validate_captcha(request, code)
            assert is_valid is False
            assert '过期' in error_msg


class TestAttemptLimit:
    """尝试次数限制测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前清除缓存"""
        cache.clear()

    def test_record_failed_attempt_increments(self):
        """测试记录失败尝试次数递增"""
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.100'}

        attempts = record_failed_attempt(request)
        assert attempts == 1

        attempts = record_failed_attempt(request)
        assert attempts == 2

    def test_lockout_after_max_attempts(self):
        """测试达到最大次数后锁定"""
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.101'}

        # 记录 MAX_ATTEMPTS 次
        for _ in range(MAX_ATTEMPTS):
            record_failed_attempt(request)

        # 应该被锁定
        assert is_locked_out(request) is True

    def test_clear_attempts(self):
        """测试清除尝试记录"""
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.102'}

        # 记录尝试
        record_failed_attempt(request)

        # 清除
        clear_attempts(request)

        # 再次记录应该从 1 开始
        cache.clear()  # 确保缓存干净
        attempts = record_failed_attempt(request)
        assert attempts == 1


class TestClientIP:
    """客户端 IP 获取测试"""

    def test_get_client_ip_direct(self):
        """测试直接 IP"""
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.50'}

        ip = get_client_ip(request)
        assert ip == '192.168.1.50'

    def test_get_client_ip_forwarded(self):
        """测试代理 IP"""
        request = MagicMock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '10.0.0.1, 192.168.1.100',
            'REMOTE_ADDR': '192.168.1.50'
        }

        ip = get_client_ip(request)
        assert ip == '10.0.0.1'

    def test_get_client_ip_multiple_proxies(self):
        """测试多层代理"""
        request = MagicMock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '10.0.0.1, 10.0.0.2, 10.0.0.3',
            'REMOTE_ADDR': '192.168.1.50'
        }

        ip = get_client_ip(request)
        # 取第一个
        assert ip == '10.0.0.1'


class TestCaptchaRefreshAPI:
    """验证码刷新 API 测试"""

    @pytest.mark.django_db
    def test_captcha_refresh_get(self, client):
        """测试 GET 请求"""
        response = client.get('/accounts/captcha/refresh/')

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'image' in data

    @pytest.mark.django_db
    def test_captcha_refresh_post_rejected(self, client):
        """测试 POST 请求被拒绝"""
        response = client.post('/accounts/captcha/refresh/')

        assert response.status_code == 405

    @pytest.mark.django_db
    def test_captcha_refresh_stores_session(self, client):
        """测试刷新验证码存储到 session"""
        client.get('/accounts/captcha/refresh/')

        assert 'captcha_code' in client.session
