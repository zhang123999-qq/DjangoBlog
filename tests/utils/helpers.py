"""
测试工具类 - 验证码识别、页面对象、通用操作
"""
import re
import time
import logging
import base64
from io import BytesIO
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


class CaptchaHandler:
    """验证码处理器"""
    
    def __init__(self, test_mode: bool = True):
        """
        初始化验证码处理器
        
        Args:
            test_mode: 测试模式，使用测试验证码或跳过
        """
        self.test_mode = test_mode
        self.ocr_available = False
        
        # 尝试加载OCR库
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.ocr_available = True
            logger.info("Tesseract OCR 可用")
        except ImportError:
            logger.warning("Tesseract OCR 不可用，将使用测试模式验证码")
    
    def solve_captcha(self, page, captcha_selector: str = 'img.captcha-img', input_selector: str = 'input[name="captcha"]') -> Tuple[bool, str]:
        """
        解决验证码
        
        Args:
            page: Playwright页面对象
            captcha_selector: 验证码图片选择器
            input_selector: 验证码输入框选择器
            
        Returns:
            (成功与否, 验证码文本)
        """
        # 1. 检查是否有验证码
        captcha_img = page.query_selector(captcha_selector)
        captcha_input = page.query_selector(input_selector)
        
        if not captcha_input:
            logger.info("未发现验证码输入框")
            return True, ""
        
        if not captcha_img:
            # 没有验证码图片，尝试测试验证码
            return self._try_test_captchas(page, input_selector)
        
        # 2. 测试模式：尝试测试验证码
        if self.test_mode:
            return self._try_test_captchas(page, input_selector)
        
        # 3. OCR模式：识别验证码
        if self.ocr_available:
            return self._ocr_captcha(page, captcha_img, input_selector)
        
        # 4. 降级：尝试测试验证码
        return self._try_test_captchas(page, input_selector)
    
    def _try_test_captchas(self, page, input_selector: str) -> Tuple[bool, str]:
        """尝试测试环境常用验证码"""
        test_captchas = ['', 'test', '1234', '0000', '123456', 'abc', 'TEST']
        
        for captcha in test_captchas:
            try:
                page.fill(input_selector, captcha)
                logger.debug(f"尝试验证码: '{captcha}'")
                return True, captcha
            except Exception as e:
                logger.debug(f"验证码 '{captcha}' 失败: {e}")
                continue
        
        return False, ""
    
    def _ocr_captcha(self, page, captcha_img, input_selector: str) -> Tuple[bool, str]:
        """使用OCR识别验证码"""
        try:
            # 获取验证码图片
            screenshot = captcha_img.screenshot()
            image = Image.open(BytesIO(screenshot))
            
            # 图像预处理
            image = image.convert('L')  # 灰度化
            image = image.point(lambda x: 0 if x < 128 else 255)  # 二值化
            
            # OCR识别
            text = self.pytesseract.image_to_string(
                image,
                config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            ).strip()
            
            # 清理识别结果
            text = re.sub(r'[^a-zA-Z0-9]', '', text)
            
            if text:
                page.fill(input_selector, text)
                logger.info(f"OCR识别验证码: '{text}'")
                return True, text
            
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
        
        return False, ""
    
    def get_audio_captcha_text(self, page, audio_selector: str) -> Optional[str]:
        """处理语音验证码（预留接口）"""
        # TODO: 集成语音识别
        pass


class WaitHelper:
    """智能等待助手"""
    
    def __init__(self, page, default_timeout: int = 30000):
        self.page = page
        self.default_timeout = default_timeout
    
    def wait_for_element(self, selector: str, timeout: int = None, state: str = 'visible') -> bool:
        """等待元素出现"""
        timeout = timeout or self.default_timeout
        try:
            self.page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
        except Exception:
            return False
    
    def wait_for_navigation(self, timeout: int = None):
        """等待页面导航完成"""
        timeout = timeout or self.default_timeout
        self.page.wait_for_load_state('networkidle', timeout=timeout)
    
    def wait_for_url_contains(self, text: str, timeout: int = None) -> bool:
        """等待URL包含指定文本"""
        timeout = timeout or self.default_timeout
        try:
            self.page.wait_for_url(f"*{text}*", timeout=timeout)
            return True
        except Exception:
            return False
    
    def wait_for_text(self, text: str, timeout: int = None) -> bool:
        """等待页面出现指定文本"""
        timeout = timeout or self.default_timeout
        try:
            self.page.wait_for_function(
                f'document.body.textContent.includes("{text}")',
                timeout=timeout
            )
            return True
        except Exception:
            return False
    
    def wait_for_any_element(self, selectors: list, timeout: int = None) -> Optional[str]:
        """等待任意一个元素出现"""
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout / 1000:
            for selector in selectors:
                element = self.page.query_selector(selector)
                if element:
                    return selector
            time.sleep(0.1)
        
        return None
    
    def smart_wait(self, condition_check, timeout: int = None, interval: float = 0.5) -> bool:
        """智能等待条件满足"""
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout / 1000:
            try:
                if condition_check():
                    return True
            except Exception:
                pass
            time.sleep(interval)
        
        return False


class RetryHelper:
    """重试助手"""
    
    @staticmethod
    def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
        """
        失败时重试
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            delay: 重试间隔（秒）
            exceptions: 触发重试的异常类型
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return func()
            except exceptions as e:
                last_error = e
                logger.warning(f"第 {attempt + 1} 次尝试失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
        
        raise last_error
    
    @staticmethod
    def retry_with_backoff(func, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
        """带退避的重试"""
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                logger.warning(f"第 {attempt + 1} 次尝试失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    raise


class ScreenshotHelper:
    """截图助手"""
    
    def __init__(self, page, screenshot_dir: Path):
        self.page = page
        self.screenshot_dir = screenshot_dir
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    def take_screenshot(self, name: str) -> Path:
        """截图"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}.png"
        path = self.screenshot_dir / filename
        self.page.screenshot(path=str(path))
        logger.info(f"截图已保存: {path}")
        return path
    
    def take_full_screenshot(self, name: str) -> Path:
        """全页截图"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_full_{timestamp}.png"
        path = self.screenshot_dir / filename
        self.page.screenshot(path=str(path), full_page=True)
        return path


class AssertionHelper:
    """断言助手"""
    
    @staticmethod
    def assert_url_contains(page, text: str, error_msg: str = None):
        """断言URL包含指定文本"""
        current_url = page.url
        assert text in current_url, error_msg or f"URL '{current_url}' 不包含 '{text}'"
    
    @staticmethod
    def assert_text_visible(page, text: str, error_msg: str = None):
        """断言页面包含指定文本"""
        page_content = page.text_content('body')
        assert text in page_content, error_msg or f"页面不包含文本 '{text}'"
    
    @staticmethod
    def assert_element_visible(page, selector: str, error_msg: str = None):
        """断言元素可见"""
        element = page.query_selector(selector)
        assert element is not None and element.is_visible(), error_msg or f"元素 '{selector}' 不可见"
    
    @staticmethod
    def assert_no_errors(page, error_selectors: list = None):
        """断言页面无错误"""
        error_selectors = error_selectors or [
            '.alert-danger', '.error-message', '.errorlist',
            '[class*="error"]', '[class*="alert-danger"]'
        ]
        
        for selector in error_selectors:
            element = page.query_selector(selector)
            if element and element.is_visible():
                error_text = element.text_content()
                raise AssertionError(f"发现错误提示: {error_text}")
    
    @staticmethod
    def assert_response_time(func, max_seconds: float, error_msg: str = None):
        """断言响应时间"""
        start_time = time.time()
        result = func()
        elapsed = time.time() - start_time
        
        assert elapsed <= max_seconds, error_msg or f"响应时间 {elapsed:.2f}s 超过限制 {max_seconds}s"
        return result
