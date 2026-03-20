"""
Pytest配置文件 - 提供测试fixtures和钩子函数
"""
import pytest
import logging
import os
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# 配置日志
def setup_logging():
    """配置日志记录器"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
                '--disable-web-security',  # 测试环境禁用安全策略
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
        ignore_https_errors=True,  # 测试环境忽略HTTPS错误
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


@pytest.fixture(scope="function")
def logged_in_page(page, base_url):
    """已登录的页面实例"""
    logger.info("执行登录操作")
    page.goto(f"{base_url}/accounts/login/")
    page.wait_for_load_state('networkidle')
    
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    
    logger.info("登录成功")
    yield page


@pytest.fixture
def test_logger():
    """返回测试日志记录器"""
    return logger


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动截图"""
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
                
                report.extra = getattr(report, 'extra', [])
                report.extra.append({
                    'name': 'Screenshot',
                    'content': str(screenshot_path),
                    'type': 'image'
                })
        except Exception as e:
            logger.error(f"截图失败: {e}")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(request):
    """设置测试环境"""
    logger.info("=" * 60)
    logger.info("开始测试会话")
    logger.info(f"测试URL: {request.config.getoption('--test-url')}")
    logger.info(f"无头模式: {request.config.getoption('--headless')}")
    logger.info("=" * 60)
    
    yield
    
    logger.info("=" * 60)
    logger.info("测试会话结束")
    logger.info("=" * 60)


# 标记定义
def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
