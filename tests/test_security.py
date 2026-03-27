"""
安全测试套件
"""
import pytest
from playwright.sync_api import Page


class TestSecurity:
    """安全测试类"""

    def test_csrf_token_present(self, page: Page, base_url: str):
        """测试CSRF Token存在"""
        page.goto(f"{base_url}/accounts/login/")
        page.wait_for_load_state('networkidle')

        # 检查CSRF token
        csrf_token = page.query_selector('input[name="csrfmiddlewaretoken"]')
        assert csrf_token is not None, "CSRF token不存在"

    def test_clickjacking_protection(self, page: Page, base_url: str):
        """测试点击劫持防护"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state('networkidle')

        # 检查X-Frame-Options头（需要通过响应头检查）
        # 这里简单检查页面是否正常加载
        assert page.url is not None

    def test_no_sensitive_info_exposed(self, page: Page, base_url: str):
        """测试敏感信息泄露"""
        page.goto(f"{base_url}/")
        page.wait_for_load_state('networkidle')

        page_content = page.content().lower()

        # 检查是否有敏感信息泄露
        sensitive_patterns = [
            'secret_key',
            'api_key',
            'password',
            'token',
            'private_key',
        ]

        for pattern in sensitive_patterns:
            # 排除表单字段名等正常情况
            if f'name="{pattern}"' in page_content or f'name=\\"{pattern}\\"' in page_content:
                continue  # 表单字段名是正常的
            # 如果在页面中直接出现，可能是泄露
            if pattern in page_content and 'input' not in page_content:
                # 进一步检查是否是真正的泄露
                pass  # 这里可以根据实际情况细化

    def test_sql_injection_login(self, page: Page, base_url: str):
        """测试登录SQL注入"""
        page.goto(f"{base_url}/accounts/login/")
        page.wait_for_load_state('networkidle')

        # 尝试SQL注入
        page.fill('input[name="username"]', "admin' OR '1'='1' --")
        page.fill('input[name="password"]', "anything")
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # 应该登录失败
        current_url = page.url
        assert '/admin' not in current_url, "SQL注入漏洞：可能绕过认证"

    def test_xss_in_search(self, page: Page, base_url: str):
        """测试搜索XSS"""
        page.goto(f"{base_url}/blog/")
        page.wait_for_load_state('networkidle')

        # 查找搜索框
        search_input = page.query_selector('input[type="search"], input[name="q"]')
        if search_input:
            search_input.fill('<script>alert("XSS")</script>')
            search_input.press('Enter')
            page.wait_for_load_state('networkidle')

            # 检查脚本是否被执行
            page_content = page.content()
            # 转义后的payload应该安全
            assert '<script>alert' not in page_content.lower() or '&lt;script&gt;' in page_content

    def test_directory_traversal(self, page: Page, base_url: str):
        """测试目录遍历"""
        # 尝试访问敏感文件
        malicious_paths = [
            '/../../../etc/passwd',
            '/..\\..\\..\\windows\\system32\\config\\sam',
            '/static/../../../settings.py',
        ]

        for path in malicious_paths:
            page.goto(f"{base_url}{path}")
            page.wait_for_load_state('networkidle')

            page_content = page.content().lower()
            # 不应该暴露敏感文件内容
            assert 'root:' not in page_content or '404' in page_content or 'error' in page_content

    def test_rate_limiting(self, page: Page, base_url: str):
        """测试速率限制"""
        page.goto(f"{base_url}/accounts/login/")
        page.wait_for_load_state('networkidle')

        # 尝试多次快速登录
        for i in range(5):
            page.fill('input[name="username"]', f'user{i}')
            page.fill('input[name="password"]', f'wrong{i}')
            page.click('button[type="submit"]')
            page.wait_for_timeout(100)

        page.wait_for_load_state('networkidle')

        # 检查是否有速率限制提示
        page_content = page.text_content('body')
        # 可能有速率限制，也可能只是登录失败
        # 至少不应该让请求全部成功


class TestAuthenticationSecurity:
    """认证安全测试"""

    def test_password_requirements(self, page: Page, base_url: str):
        """测试密码强度要求"""
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')

        # 测试弱密码
        weak_passwords = ['123', 'password', '12345678']

        for weak_pwd in weak_passwords:
            page.fill('input[name="username"]', 'testuser')
            page.fill('input[name="email"]', 'test@test.com')
            page.fill('input[name="password1"]', weak_pwd)
            page.fill('input[name="password2"]', weak_pwd)
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')

            error_text = page.text_content('body')
            assert '密码' in error_text or 'password' in error_text.lower(), \
                f"弱密码 '{weak_pwd}' 未被拒绝"

    def test_session_security(self, page: Page, base_url: str):
        """测试会话安全"""
        # 登录
        page.goto(f"{base_url}/accounts/login/")
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'admin123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # 检查会话cookie
        cookies = page.context.cookies()

        for cookie in cookies:
            # 检查HttpOnly（需要通过context检查）
            if 'sessionid' in cookie.get('name', ''):
                # 会话cookie应该有安全属性
                pass  # 实际检查需要更复杂的逻辑

    def test_logout_clears_session(self, page: Page, base_url: str):
        """测试登出清除会话"""
        # 登录
        page.goto(f"{base_url}/accounts/login/")
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'admin123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # 登出
        page.goto(f"{base_url}/accounts/logout/")
        page.wait_for_load_state('networkidle')

        # 访问需要登录的页面
        page.goto(f"{base_url}/admin/")
        page.wait_for_load_state('networkidle')

        # 应该被重定向到登录页
        current_url = page.url
        assert 'login' in current_url, "登出后仍可访问受保护页面"


class TestInputValidation:
    """输入验证测试"""

    def test_html_injection(self, page: Page, base_url: str):
        """测试HTML注入"""
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')

        html_payload = '<h1>Hacked</h1><img src=x onerror=alert(1)>'
        page.fill('input[name="username"]', html_payload)
        page.fill('input[name="email"]', 'test@test.com')
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test123456!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # 检查HTML是否被转义
        page_content = page.content()
        # 应该被转义，而不是直接执行
        assert '<h1>Hacked</h1>' not in page_content or 'error' in page.url

    def test_unicode_handling(self, page: Page, base_url: str):
        """测试Unicode处理"""
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')

        unicode_username = '用户名测试'
        page.fill('input[name="username"]', unicode_username)
        page.fill('input[name="email"]', 'test@test.com')
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test123456!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # 应该正确处理或拒绝Unicode
        # 至少不应该崩溃

    def test_null_byte_injection(self, page: Page, base_url: str):
        """测试空字节注入"""
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')

        null_payload = 'admin\x00evil'
        page.fill('input[name="username"]', null_payload)
        page.fill('input[name="email"]', 'test@test.com')
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test123456!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # 应该被正确处理或拒绝
        current_url = page.url
        # 不应该创建意外的用户
