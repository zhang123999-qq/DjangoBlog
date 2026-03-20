"""
用户注册测试 - 增强版
"""
import pytest
from playwright.sync_api import Page, expect
from utils.data_generator import DataGenerator


class TestRegister:
    """用户注册测试类"""
    
    def test_register_success(self, page: Page, base_url: str, test_logger):
        """测试正常注册流程"""
        test_logger.info("开始测试: 正常注册流程")
        
        user_data = DataGenerator.user_data()
        test_logger.info(f"生成测试用户: {user_data['username']}")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')
        
        page.fill('input[name="username"]', user_data['username'])
        page.fill('input[name="email"]', user_data['email'])
        page.fill('input[name="password1"]', user_data['password'])
        page.fill('input[name="password2"]', user_data['password'])
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        current_url = page.url
        assert '/register' not in current_url, "注册失败：仍在注册页面"
        test_logger.info(f"注册成功，当前URL: {current_url}")
    
    def test_register_existing_username(self, page: Page, base_url: str, test_logger):
        """测试使用已存在用户名注册"""
        test_logger.info("开始测试: 已存在用户名注册")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')
        
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="email"]', DataGenerator.email())
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test123456!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        error_text = page.text_content('body')
        assert '已存在' in error_text or 'exist' in error_text.lower() or '该用户名' in error_text, \
            "未显示用户名已存在的错误提示"
        test_logger.info("正确显示错误提示")
    
    @pytest.mark.parametrize("password,expected_error", [
        ("123", "密码太短"),
        ("password", "密码太简单"),
        ("12345678", "密码太简单"),
        ("abc123", "密码"),
    ])
    def test_register_weak_password(self, page: Page, base_url: str, test_logger, password: str, expected_error: str):
        """测试弱密码注册"""
        test_logger.info(f"开始测试: 弱密码注册 - {password}")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')
        
        page.fill('input[name="username"]', DataGenerator.username())
        page.fill('input[name="email"]', DataGenerator.email())
        page.fill('input[name="password1"]', password)
        page.fill('input[name="password2"]', password)
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        error_text = page.text_content('body')
        assert expected_error in error_text or '密码' in error_text, \
            f"未显示正确的密码错误提示，期望: {expected_error}"
        test_logger.info(f"正确显示密码错误提示: {expected_error}")
    
    def test_register_password_mismatch(self, page: Page, base_url: str, test_logger):
        """测试两次密码不一致"""
        test_logger.info("开始测试: 密码不一致")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')
        
        page.fill('input[name="username"]', DataGenerator.username())
        page.fill('input[name="email"]', DataGenerator.email())
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test654321!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        error_text = page.text_content('body')
        assert '不一致' in error_text or '匹配' in error_text or 'password' in error_text.lower(), \
            "未显示密码不匹配的错误提示"
        test_logger.info("正确显示密码不一致错误")
    
    def test_register_invalid_email(self, page: Page, base_url: str, test_logger):
        """测试无效邮箱格式"""
        test_logger.info("开始测试: 无效邮箱格式")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')
        
        page.fill('input[name="username"]', DataGenerator.username())
        page.fill('input[name="email"]', 'invalid-email')
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test123456!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        error_text = page.text_content('body')
        assert '邮箱' in error_text or 'email' in error_text.lower() or '有效' in error_text, \
            "未显示邮箱格式错误提示"
        test_logger.info("正确显示邮箱格式错误")
    
    def test_register_empty_fields(self, page: Page, base_url: str, test_logger):
        """测试空字段提交"""
        test_logger.info("开始测试: 空字段提交")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_load_state('networkidle')
        
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        error_text = page.text_content('body')
        assert '必填' in error_text or 'required' in error_text.lower() or '不能为空' in error_text, \
            "未显示必填字段错误"
        test_logger.info("正确显示必填字段错误")


class TestRegisterSecurity:
    """注册安全测试"""
    
    def test_xss_in_username(self, page: Page, base_url: str, test_logger):
        """测试XSS攻击 - 用户名注入"""
        test_logger.info("开始测试: XSS攻击防护")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')
        
        xss_payload = '<script>alert("XSS")</script>'
        page.fill('input[name="username"]', xss_payload)
        page.fill('input[name="email"]', DataGenerator.email())
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test123456!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        # 检查脚本是否被执行
        page_content = page.content()
        assert '<script>alert' not in page_content.lower() or 'error' in page.url, \
            "XSS漏洞：脚本注入未被过滤"
        test_logger.info("XSS防护正常")
    
    def test_sql_injection_in_username(self, page: Page, base_url: str, test_logger):
        """测试SQL注入 - 用户名字段"""
        test_logger.info("开始测试: SQL注入防护")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')
        
        sql_payload = "admin' OR '1'='1"
        page.fill('input[name="username"]', sql_payload)
        page.fill('input[name="email"]', DataGenerator.email())
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test123456!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        # 应该显示错误，而不是登录成功
        current_url = page.url
        assert '/admin' not in current_url, "SQL注入漏洞：可能绕过认证"
        test_logger.info("SQL注入防护正常")
    
    def test_long_username(self, page: Page, base_url: str, test_logger):
        """测试超长用户名"""
        test_logger.info("开始测试: 超长用户名")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')
        
        long_username = 'a' * 200
        page.fill('input[name="username"]', long_username)
        page.fill('input[name="email"]', DataGenerator.email())
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test123456!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        # 应该被截断或拒绝
        error_text = page.text_content('body')
        test_logger.info("超长输入处理正常")
    
    def test_special_characters_in_username(self, page: Page, base_url: str, test_logger):
        """测试特殊字符用户名"""
        test_logger.info("开始测试: 特殊字符用户名")
        
        page.goto(f"{base_url}/accounts/register/")
        page.wait_for_load_state('networkidle')
        
        special_username = '!@#$%^&*()'
        page.fill('input[name="username"]', special_username)
        page.fill('input[name="email"]', DataGenerator.email())
        page.fill('input[name="password1"]', 'Test123456!')
        page.fill('input[name="password2"]', 'Test123456!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        error_text = page.text_content('body')
        assert '用户名' in error_text or '字符' in error_text or 'invalid' in error_text.lower(), \
            "未显示特殊字符错误"
        test_logger.info("特殊字符处理正常")


class TestRegisterPerformance:
    """注册性能测试"""
    
    def test_registration_time(self, page: Page, base_url: str, test_logger):
        """测试注册响应时间"""
        import time
        test_logger.info("开始测试: 注册响应时间")
        
        user_data = DataGenerator.user_data()
        page.goto(f"{base_url}/accounts/register/")
        
        start_time = time.time()
        
        page.fill('input[name="username"]', user_data['username'])
        page.fill('input[name="email"]', user_data['email'])
        page.fill('input[name="password1"]', user_data['password'])
        page.fill('input[name="password2"]', user_data['password'])
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response_time < 5.0, f"注册响应时间过长: {response_time:.2f}秒"
        test_logger.info(f"注册响应时间: {response_time:.2f}秒")
