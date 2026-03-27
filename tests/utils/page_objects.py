"""
页面对象模型 (Page Object Model)
将页面元素和操作封装成对象，提高测试可维护性和可扩展性
"""
import logging
from typing import Optional, List, Dict
from playwright.sync_api import Page, expect
from .helpers import CaptchaHandler, WaitHelper, RetryHelper, AssertionHelper

logger = logging.getLogger(__name__)


class BasePage:
    """基础页面对象"""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.wait = WaitHelper(page)
        self.captcha = CaptchaHandler()
        self.assertion = AssertionHelper

    def navigate(self, path: str = ""):
        """导航到页面"""
        url = f"{self.base_url}{path}"
        logger.info(f"导航到: {url}")
        self.page.goto(url)
        self.wait.wait_for_navigation()
        return self

    def get_current_url(self) -> str:
        """获取当前URL"""
        return self.page.url

    def get_page_title(self) -> str:
        """获取页面标题"""
        return self.page.title()

    def refresh(self):
        """刷新页面"""
        self.page.reload()
        self.wait.wait_for_navigation()
        return self

    def go_back(self):
        """后退"""
        self.page.go_back()
        self.wait.wait_for_navigation()
        return self

    def take_screenshot(self, name: str):
        """截图"""
        from pathlib import Path
        from datetime import datetime
        screenshot_dir = Path(__file__).parent.parent / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = screenshot_dir / f"{name}_{timestamp}.png"
        self.page.screenshot(path=str(path))
        logger.info(f"截图已保存: {path}")
        return self


class LoginPage(BasePage):
    """登录页面对象"""

    # 元素选择器
    USERNAME_INPUT = 'input[name="username"]'
    PASSWORD_INPUT = 'input[name="password"]'
    CAPTCHA_INPUT = 'input[name="captcha"]'
    CAPTCHA_IMG = 'img.captcha-img, img[id*="captcha"]'
    SUBMIT_BTN = 'button[type="submit"], input[type="submit"]'
    ERROR_MSG = '.alert-danger, .errorlist, .text-danger'
    SUCCESS_MSG = '.alert-success'

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.path = "/accounts/login/"

    def open(self) -> 'LoginPage':
        """打开登录页面"""
        self.navigate(self.path)
        return self

    def fill_username(self, username: str) -> 'LoginPage':
        """填写用户名"""
        self.page.fill(self.USERNAME_INPUT, username)
        return self

    def fill_password(self, password: str) -> 'LoginPage':
        """填写密码"""
        self.page.fill(self.PASSWORD_INPUT, password)
        return self

    def fill_captcha(self, captcha: str = None) -> 'LoginPage':
        """填写验证码"""
        captcha_input = self.page.query_selector(self.CAPTCHA_INPUT)
        if captcha_input:
            if captcha:
                self.page.fill(self.CAPTCHA_INPUT, captcha)
            else:
                # 自动处理验证码
                self.captcha.solve_captcha(self.page, self.CAPTCHA_IMG, self.CAPTCHA_INPUT)
        return self

    def click_submit(self) -> 'LoginPage':
        """点击登录按钮"""
        self.page.click(self.SUBMIT_BTN)
        self.wait.wait_for_navigation()
        return self

    def login(self, username: str, password: str, captcha: str = None) -> 'LoginPage':
        """完整的登录流程"""
        return (self.open()
                .fill_username(username)
                .fill_password(password)
                .fill_captcha(captcha)
                .click_submit())

    def is_login_success(self) -> bool:
        """判断是否登录成功"""
        current_url = self.get_current_url()
        # 登录成功后应该不在登录页面
        return '/login' not in current_url

    def is_login_failed(self) -> bool:
        """判断是否登录失败"""
        error_element = self.page.query_selector(self.ERROR_MSG)
        return error_element is not None and error_element.is_visible()

    def get_error_message(self) -> str:
        """获取错误信息"""
        error_element = self.page.query_selector(self.ERROR_MSG)
        if error_element:
            return error_element.text_content().strip()
        return ""

    def wait_for_login_success(self, timeout: int = 10000) -> bool:
        """等待登录成功"""
        def check_success():
            return '/login' not in self.get_current_url()

        return self.wait.smart_wait(check_success, timeout)


class RegisterPage(BasePage):
    """注册页面对象"""

    # 元素选择器
    USERNAME_INPUT = 'input[name="username"]'
    EMAIL_INPUT = 'input[name="email"]'
    PASSWORD1_INPUT = 'input[name="password1"]'
    PASSWORD2_INPUT = 'input[name="password2"]'
    CAPTCHA_INPUT = 'input[name="captcha"]'
    SUBMIT_BTN = 'button[type="submit"], input[type="submit"]'
    ERROR_MSG = '.alert-danger, .errorlist, .text-danger, .invalid-feedback'
    SUCCESS_MSG = '.alert-success'

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.path = "/accounts/register/"

    def open(self) -> 'RegisterPage':
        """打开注册页面"""
        self.navigate(self.path)
        return self

    def fill_username(self, username: str) -> 'RegisterPage':
        """填写用户名"""
        self.page.fill(self.USERNAME_INPUT, username)
        return self

    def fill_email(self, email: str) -> 'RegisterPage':
        """填写邮箱"""
        self.page.fill(self.EMAIL_INPUT, email)
        return self

    def fill_password1(self, password: str) -> 'RegisterPage':
        """填写密码"""
        self.page.fill(self.PASSWORD1_INPUT, password)
        return self

    def fill_password2(self, password: str) -> 'RegisterPage':
        """填写确认密码"""
        self.page.fill(self.PASSWORD2_INPUT, password)
        return self

    def fill_captcha(self, captcha: str = None) -> 'RegisterPage':
        """填写验证码"""
        captcha_input = self.page.query_selector(self.CAPTCHA_INPUT)
        if captcha_input:
            if captcha:
                self.page.fill(self.CAPTCHA_INPUT, captcha)
            else:
                self.captcha.solve_captcha(self.page, captcha_selector='img.captcha-img', input_selector=self.CAPTCHA_INPUT)
        return self

    def click_submit(self) -> 'RegisterPage':
        """点击注册按钮"""
        self.page.click(self.SUBMIT_BTN)
        self.wait.wait_for_navigation()
        return self

    def register(self, username: str, email: str, password: str, captcha: str = None) -> 'RegisterPage':
        """完整的注册流程"""
        return (self.open()
                .fill_username(username)
                .fill_email(email)
                .fill_password1(password)
                .fill_password2(password)
                .fill_captcha(captcha)
                .click_submit())

    def is_register_success(self) -> bool:
        """判断是否注册成功"""
        current_url = self.get_current_url()
        page_content = self.page.text_content('body')
        # 注册成功后应该不在注册页面，或者显示成功消息
        return '/register' not in current_url or '成功' in page_content or 'success' in page_content.lower()

    def get_error_messages(self) -> List[str]:
        """获取所有错误信息"""
        errors = []
        error_elements = self.page.query_selector_all(self.ERROR_MSG)
        for element in error_elements:
            text = element.text_content().strip()
            if text:
                errors.append(text)
        return errors


class HomePage(BasePage):
    """首页页面对象"""

    NAVBAR = 'nav.navbar'
    LOGIN_LINK = 'a[href*="login"]'
    REGISTER_LINK = 'a[href*="register"]'
    LOGOUT_LINK = 'a[href*="logout"]'
    USER_MENU = '.dropdown-toggle, .user-menu'

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.path = "/"

    def open(self) -> 'HomePage':
        """打开首页"""
        self.navigate(self.path)
        return self

    def is_logged_in(self) -> bool:
        """判断是否已登录"""
        # 检查是否有登录链接（未登录时显示）
        login_link = self.page.query_selector(self.LOGIN_LINK)
        return login_link is None or not login_link.is_visible()

    def go_to_login(self) -> LoginPage:
        """跳转到登录页"""
        self.page.click(self.LOGIN_LINK)
        self.wait.wait_for_navigation()
        return LoginPage(self.page, self.base_url)

    def go_to_register(self) -> RegisterPage:
        """跳转到注册页"""
        self.page.click(self.REGISTER_LINK)
        self.wait.wait_for_navigation()
        return RegisterPage(self.page, self.base_url)

    def logout(self) -> 'HomePage':
        """登出"""
        logout_link = self.page.query_selector(self.LOGOUT_LINK)
        if logout_link:
            logout_link.click()
            self.wait.wait_for_navigation()
        return self


class BlogPage(BasePage):
    """博客页面对象"""

    POST_LIST = '.post-list, .article-list'
    POST_ITEM = '.post-item, .article-item'
    POST_TITLE = '.post-title a, .article-title a'
    POST_CONTENT = '.post-content, .article-content'

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.path = "/blog/"

    def open(self) -> 'BlogPage':
        """打开博客页面"""
        self.navigate(self.path)
        return self

    def get_post_count(self) -> int:
        """获取文章数量"""
        posts = self.page.query_selector_all(self.POST_ITEM)
        return len(posts)

    def click_post_by_index(self, index: int) -> 'BlogPage':
        """点击指定索引的文章"""
        posts = self.page.query_selector_all(self.POST_TITLE)
        if 0 <= index < len(posts):
            posts[index].click()
            self.wait.wait_for_navigation()
        return self


class UserFlow:
    """用户流程封装"""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.login_page = LoginPage(page, base_url)
        self.register_page = RegisterPage(page, base_url)
        self.home_page = HomePage(page, base_url)

    def login_as(self, username: str, password: str, captcha: str = None) -> bool:
        """
        以指定用户登录

        Returns:
            是否登录成功
        """
        result = self.login_page.login(username, password, captcha)
        return result.is_login_success()

    def login_as_admin(self) -> bool:
        """以管理员登录"""
        return self.login_as('admin', 'asd123456')

    def register_new_user(self, user_data: dict) -> tuple:
        """
        注册新用户

        Returns:
            (是否成功, 错误信息列表)
        """
        result = self.register_page.register(
            username=user_data.get('username', 'testuser'),
            email=user_data.get('email', 'test@test.com'),
            password=user_data.get('password', 'Test123456!'),
            captcha=user_data.get('captcha')
        )

        success = result.is_register_success()
        errors = result.get_error_messages() if not success else []

        return success, errors

    def logout(self):
        """登出"""
        self.home_page.open().logout()

    def ensure_logged_out(self):
        """确保已登出"""
        self.home_page.open()
        if self.home_page.is_logged_in():
            self.logout()
