"""
Pytest配置文件 - 优化版
提供测试fixtures、页面对象、验证码处理等
"""
import pytest
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from utils.helpers import CaptchaHandler, WaitHelper, ScreenshotHelper
from utils.page_objects import LoginPage, RegisterPage, HomePage, UserFlow

# ============================================
# 日志配置
# ============================================

def setup_logging():
    """配置日志记录器"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 配置根日志
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logging.getLogger(__name__)

logger = setup_logging()

# 截图目录
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


# ============================================
# 命令行参数
# ============================================

def pytest_addoption(parser):
    """添加命令行参数"""
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run tests in headless mode"
    )
    parser.addoption(
        "--test-url",
        action="store",
        default="http://localhost:8000",
        help="Base URL for testing"
    )
    parser.addoption(
        "--slow-mo",
        action="store",
        default=0,
        type=int,
        help="Slow down operations by ms"
    )
    parser.addoption(
        "--timeout",
        action="store",
        default=30000,
        type=int,
        help="Default timeout in ms"
    )
    parser.addoption(
        "--retries",
        action="store",
        default=2,
        type=int,
        help="Number of retries for failed tests"
    )
    parser.addoption(
        "--test-captcha",
        action="store",
        default="test",
        type=str,
        help="Test captcha value to use"
    )
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run Playwright E2E tests that require a live server"
    )


# ============================================
# Fixtures
# ============================================

@pytest.fixture(scope="session")
def base_url(request):
    """获取基础URL"""
    return request.config.getoption("--test-url")


@pytest.fixture(scope="session")
def headless(request):
    """获取是否无头模式"""
    return request.config.getoption("--headless")


@pytest.fixture(scope="session")
def slow_mo(request):
    """获取慢速操作延迟"""
    return request.config.getoption("--slow-mo")


@pytest.fixture(scope="session")
def default_timeout(request):
    """获取默认超时"""
    return request.config.getoption("--timeout")


@pytest.fixture(scope="session")
def test_captcha(request):
    """获取测试验证码"""
    return request.config.getoption("--test-captcha")


@pytest.fixture(scope="session")
def browser(headless, slow_mo):
    """创建浏览器实例"""
    logger.info(f"启动浏览器，headless={headless}, slow_mo={slow_mo}ms")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=[
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        yield browser
        browser.close()
        logger.info("浏览器已关闭")


@pytest.fixture(scope="function")
def context(browser):
    """创建浏览器上下文"""
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        locale='zh-CN',
        timezone_id='Asia/Shanghai',
        ignore_https_errors=True,
        # 录制视频（可选）
        # record_video_dir=str(SCREENSHOT_DIR / "videos"),
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context, default_timeout):
    """创建页面实例"""
    page = context.new_page()
    page.set_default_timeout(default_timeout)
    yield page
    page.close()


# ============================================
# 页面对象 Fixtures
# ============================================

@pytest.fixture
def login_page(page, base_url) -> LoginPage:
    """登录页面对象"""
    return LoginPage(page, base_url)


@pytest.fixture
def register_page(page, base_url) -> RegisterPage:
    """注册页面对象"""
    return RegisterPage(page, base_url)


@pytest.fixture
def home_page(page, base_url) -> HomePage:
    """首页页面对象"""
    return HomePage(page, base_url)


@pytest.fixture
def user_flow(page, base_url) -> UserFlow:
    """用户流程封装"""
    return UserFlow(page, base_url)


# ============================================
# 辅助工具 Fixtures
# ============================================

@pytest.fixture
def test_logger():
    """测试日志记录器"""
    return logging.getLogger(__name__)


@pytest.fixture
def captcha_handler() -> CaptchaHandler:
    """验证码处理器"""
    return CaptchaHandler()


@pytest.fixture
def wait_helper(page, default_timeout) -> WaitHelper:
    """等待助手"""
    return WaitHelper(page, default_timeout)


@pytest.fixture
def screenshot_helper(page) -> ScreenshotHelper:
    """截图助手"""
    return ScreenshotHelper(page, SCREENSHOT_DIR)


# ============================================
# 已登录状态 Fixtures
# ============================================

@pytest.fixture
def logged_in_page(page, base_url, test_captcha):
    """已登录的页面实例"""
    logger.info("执行自动登录")

    login_page = LoginPage(page, base_url)
    login_page.login('admin', 'asd123456', test_captcha)

    # 等待登录结果
    if login_page.is_login_success():
        logger.info("登录成功")
    else:
        logger.warning(f"登录可能失败，当前URL: {page.url}")
        error_msg = login_page.get_error_message()
        if error_msg:
            logger.warning(f"错误信息: {error_msg}")

    yield page


@pytest.fixture
def admin_page(logged_in_page, base_url):
    """管理员页面（已登录且在管理后台）"""
    logged_in_page.goto(f"{base_url}/admin/")
    logged_in_page.wait_for_load_state('networkidle')
    yield logged_in_page


# ============================================
# 测试数据 Fixtures
# ============================================

@pytest.fixture
def test_user_data():
    """测试用户数据"""
    from utils.data_generator import DataGenerator
    return DataGenerator.user_data()


@pytest.fixture
def test_article_data():
    """测试文章数据"""
    return {
        'title': f'测试文章_{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'content': '这是一篇测试文章的内容，用于自动化测试。',
        'category': '测试分类',
        'tags': ['测试', '自动化'],
    }


# ============================================
# 钩子函数
# ============================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图和记录"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        try:
            if "page" in item.funcargs:
                page = item.funcargs["page"]
                screenshot_name = f"{item.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                screenshot_path = SCREENSHOT_DIR / screenshot_name
                page.screenshot(path=str(screenshot_path))
                logger.error(f"测试失败，截图已保存: {screenshot_path}")

                # 附加到报告
                report.extra = getattr(report, 'extra', [])
                report.extra.append({
                    'name': 'Screenshot',
                    'content': str(screenshot_path),
                    'type': 'image'
                })

                # 保存页面内容
                html_path = SCREENSHOT_DIR / f"{item.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                html_path.write_text(page.content(), encoding='utf-8')
                logger.info(f"页面HTML已保存: {html_path}")

        except Exception as e:
            logger.error(f"截图失败: {e}")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(request):
    """设置测试环境"""
    logger.info("=" * 60)
    logger.info("开始测试会话")
    logger.info(f"测试URL: {request.config.getoption('--test-url')}")
    logger.info(f"无头模式: {request.config.getoption('--headless')}")
    logger.info(f"超时时间: {request.config.getoption('--timeout')}ms")
    logger.info(f"重试次数: {request.config.getoption('--retries')}")
    logger.info("=" * 60)

    yield

    logger.info("=" * 60)
    logger.info("测试会话结束")
    logger.info("=" * 60)


# ============================================
# 标记定义
# ============================================

def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line("markers", "security: 安全测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "auth: 认证相关测试")
    config.addinivalue_line("markers", "blog: 博客功能测试")
    config.addinivalue_line("markers", "forum: 论坛功能测试")
    config.addinivalue_line("markers", "tools: 工具栏测试")
    config.addinivalue_line("markers", "e2e: 需要 live server 的端到端测试")


def pytest_collection_modifyitems(config, items):
    """默认跳过依赖 live server 的 E2E 测试，避免本地无服务时误失败。"""
    if config.getoption("--run-e2e"):
        return

    skip_e2e = pytest.mark.skip(reason="requires live server; use --run-e2e to enable")

    for item in items:
        fixturenames = set(getattr(item, 'fixturenames', []) or [])
        # 仅对真正依赖 Playwright 运行时的用例打 e2e 跳过
        if {'page', 'context', 'browser', 'playwright'} & fixturenames:
            item.add_marker(skip_e2e)
            item.add_marker('e2e')


# ============================================
# 重试机制
# ============================================

def pytest_runtest_protocol(item, nextitem):
    """测试重试机制"""
    retries = item.config.getoption("--retries")
    if retries <= 0:
        return

    # 使用 pytest-rerunfailures 插件实现重试
    # 或者手动实现
    pass
