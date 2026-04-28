"""
工具模块视图测试

测试覆盖:
- tool_list: 工具列表视图
- tool_detail: 工具详情视图
- my_ip_json: IP查询视图
- 权限控制: 登录保护
- 表单验证: 错误处理
"""

import pytest
import socket
from unittest.mock import patch
from django.test import Client, SimpleTestCase
from django.urls import reverse
from apps.accounts.models import User
from apps.tools.models import ToolConfig
from apps.tools.tool_modules.http_request_tool import HTTPRequestTool, _prepare_pinned_request_target
from apps.tools.tool_modules.port_scan_tool import _resolve_public_target


@pytest.mark.django_db
class TestToolListView:
    """工具列表视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.tool_list_url = reverse('tools:tool_list')

    def test_tool_list_view_loads(self):
        """测试工具列表加载"""
        response = self.client.get(self.tool_list_url)
        assert response.status_code == 200
        assert 'categories' in response.context
        assert 'tools' in response.context

    def test_tool_list_view_caching(self):
        """测试工具列表缓存"""
        # 第一次访问
        response1 = self.client.get(self.tool_list_url)
        assert response1.status_code == 200

        # 第二次访问（应该命中缓存）
        response2 = self.client.get(self.tool_list_url)
        assert response2.status_code == 200

    def test_tool_list_view_context(self):
        """测试工具列表上下文"""
        response = self.client.get(self.tool_list_url)
        assert response.status_code == 200

        # 检查上下文数据
        context = response.context
        assert 'categories' in context
        assert 'tools' in context
        assert 'total_tools' in context
        assert 'enabled_tools_count' in context


@pytest.mark.django_db
class TestToolDetailView:
    """工具详情视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_tool_detail_view_requires_login(self):
        """测试工具详情需要登录"""
        # 尝试访问一个存在的工具
        url = reverse('tools:tool_detail', args=['hash'])
        response = self.client.get(url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_tool_detail_view_loads_when_logged_in(self):
        """测试登录后可以访问工具详情"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tools:tool_detail', args=['hash'])
        response = self.client.get(url)
        # 应该成功加载
        assert response.status_code == 200
        assert 'tool' in response.context
        assert 'form' in response.context

    def test_tool_detail_view_nonexistent_tool(self):
        """测试不存在的工具"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tools:tool_detail', args=['nonexistent-tool'])
        response = self.client.get(url)
        # 应该显示错误信息
        assert response.status_code == 200
        assert 'error' in response.context

    def test_tool_detail_view_disabled_tool(self):
        """测试被禁用的工具"""
        # 创建工具配置并禁用
        ToolConfig.objects.create(
            slug='hash',
            name='哈希计算',
            is_enabled=False
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('tools:tool_detail', args=['hash'])
        response = self.client.get(url)
        # 应该显示工具被禁用
        assert response.status_code == 200
        assert 'error' in response.context
        assert '已被禁用' in response.context['error']


@pytest.mark.django_db
class TestMyIPJsonView:
    """IP查询视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_my_ip_json_requires_login(self):
        """测试IP查询需要登录"""
        url = reverse('tools:my_ip_json')
        response = self.client.get(url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_my_ip_json_loads_when_logged_in(self):
        """测试登录后可以查询IP"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tools:my_ip_json')
        response = self.client.get(url)
        # 应该返回JSON响应
        assert response.status_code == 200
        assert response['content-type'] == 'application/json'

        # 解析JSON响应
        data = response.json()
        assert 'ok' in data
        assert 'ip' in data


@pytest.mark.django_db
class TestToolFormValidation:
    """工具表单验证测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_tool_form_validation_error(self):
        """测试工具表单验证错误"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tools:tool_detail', args=['hash'])

        # 提交空表单（应该验证失败）
        response = self.client.post(url, {})

        # 应该返回表单页面（带错误信息）
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'error_message' in response.context
        assert response.context['error_message'] is not None

    def test_tool_form_validation_success(self):
        """测试工具表单验证成功"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tools:tool_detail', args=['hash'])

        # 提交有效表单
        response = self.client.post(url, {
            'text': 'hello',
            'algorithm': 'md5'
        })

        # 应该返回结果
        assert response.status_code == 200
        assert 'result' in response.context
        # 结果应该包含哈希值
        if response.context['result']:
            assert 'hash' in response.context['result'] or 'result' in response.context['result']


@pytest.mark.django_db
class TestToolPermissionControl:
    """工具权限控制测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_anonymous_cannot_access_tools(self):
        """测试匿名用户不能访问工具"""
        url = reverse('tools:tool_detail', args=['hash'])
        response = self.client.get(url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_anonymous_can_view_tool_list(self):
        """测试匿名用户可以查看工具列表"""
        url = reverse('tools:tool_list')
        response = self.client.get(url)
        # 应该可以查看列表
        assert response.status_code == 200

    def test_anonymous_cannot_use_my_ip_json(self):
        """测试匿名用户不能使用IP查询"""
        url = reverse('tools:my_ip_json')
        response = self.client.get(url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_logged_in_user_can_access_tools(self):
        """测试登录用户可以访问工具"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tools:tool_detail', args=['hash'])
        response = self.client.get(url)
        # 应该可以访问
        assert response.status_code == 200


class _FakeResponse:
    def __init__(self, status=200, headers=None, reason="OK", data=b"{}"):
        self.status = status
        self.headers = headers or {}
        self.reason = reason
        self.data = data


class TestNetworkToolSecurity(SimpleTestCase):
    @patch(
        "apps.tools.tool_modules.http_request_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )
    def test_prepare_pinned_request_target_rewrites_public_domain(self, _mock_getaddrinfo):
        parsed, pinned_url, host_header, resolved_ip, error = _prepare_pinned_request_target(
            "https://example.com/api?q=1"
        )

        assert error is None
        assert parsed.hostname == "example.com"
        assert pinned_url == "https://93.184.216.34/api?q=1"
        assert host_header == "example.com"
        assert resolved_ip == "93.184.216.34"

    @patch(
        "apps.tools.tool_modules.http_request_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))],
    )
    def test_prepare_pinned_request_target_rejects_internal_resolution(self, _mock_getaddrinfo):
        _parsed, _pinned_url, _host_header, _resolved_ip, error = _prepare_pinned_request_target(
            "https://example.com/"
        )

        assert error is not None
        assert "内网地址" in error

    def test_prepare_pinned_request_target_rejects_internal_literal_ip(self):
        _parsed, _pinned_url, _host_header, _resolved_ip, error = _prepare_pinned_request_target(
            "http://127.0.0.1/admin"
        )

        assert error is not None
        assert "内网地址" in error

    @patch(
        "apps.tools.tool_modules.http_request_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )
    def test_send_request_uses_pinned_public_ip(self, _mock_getaddrinfo):
        tool = HTTPRequestTool()

        with patch.object(tool, "_perform_request", return_value=_FakeResponse()) as mock_perform_request:
            response_meta = tool._send_request("GET", "https://example.com/path", {}, "", "application/json", 5, False)

        assert response_meta["resolved_ip"] == "93.184.216.34"
        assert mock_perform_request.call_args.args[1] == "https://93.184.216.34/path"
        assert mock_perform_request.call_args.args[5] == "example.com"
        assert mock_perform_request.call_args.args[6] == "example.com"

    @patch(
        "apps.tools.tool_modules.http_request_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )
    def test_send_request_revalidates_redirect_targets(self, _mock_getaddrinfo):
        tool = HTTPRequestTool()
        first_response = _FakeResponse(status=302, headers={"Location": "http://127.0.0.1/admin"})

        with patch.object(tool, "_perform_request", return_value=first_response):
            with self.assertRaises(ValueError):
                tool._send_request("GET", "https://example.com/path", {}, "", "application/json", 5, True)

    @patch(
        "apps.tools.tool_modules.port_scan_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )
    def test_resolve_public_target_returns_pinned_ip(self, _mock_getaddrinfo):
        resolved_ip, error = _resolve_public_target("example.com")

        assert error is None
        assert resolved_ip == "93.184.216.34"

    @patch(
        "apps.tools.tool_modules.port_scan_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))],
    )
    def test_resolve_public_target_rejects_internal_resolution(self, _mock_getaddrinfo):
        resolved_ip, error = _resolve_public_target("example.com")

        assert resolved_ip is None
        assert "禁止扫描" in error
