"""
自定义等待条件
"""
from playwright.sync_api import Page, Locator
from typing import Callable, Any
import re


class WaitFor:
    """自定义等待条件"""
    
    @staticmethod
    def url_contains(page: Page, pattern: str, timeout: int = 10000) -> bool:
        """
        等待URL包含指定模式
        
        Args:
            page: Playwright页面对象
            pattern: URL模式（支持正则）
            timeout: 超时时间（毫秒）
        
        Returns:
            bool: 是否匹配成功
        """
        try:
            page.wait_for_url(re.compile(pattern), timeout=timeout)
            return True
        except Exception:
            return False
    
    @staticmethod
    def element_text_change(locator: Locator, original_text: str, timeout: int = 10000) -> bool:
        """
        等待元素文本变化
        
        Args:
            locator: 元素定位器
            original_text: 原始文本
            timeout: 超时时间
        
        Returns:
            bool: 文本是否变化
        """
        try:
            locator.wait_for(timeout=timeout)
            current_text = locator.text_content()
            return current_text != original_text
        except Exception:
            return False
    
    @staticmethod
    def element_count(page: Page, selector: str, expected_count: int, timeout: int = 10000) -> bool:
        """
        等待元素数量达到期望值
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            expected_count: 期望数量
            timeout: 超时时间
        
        Returns:
            bool: 数量是否匹配
        """
        try:
            page.wait_for_selector(selector, timeout=timeout)
            elements = page.query_selector_all(selector)
            return len(elements) == expected_count
        except Exception:
            return False
    
    @staticmethod
    def element_visible(page: Page, selector: str, timeout: int = 10000) -> bool:
        """
        等待元素可见
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间
        
        Returns:
            bool: 元素是否可见
        """
        try:
            page.wait_for_selector(selector, state='visible', timeout=timeout)
            return True
        except Exception:
            return False
    
    @staticmethod
    def element_hidden(page: Page, selector: str, timeout: int = 10000) -> bool:
        """
        等待元素隐藏或消失
        
        Args:
            page: Playwright页面对象
            selector: CSS选择器
            timeout: 超时时间
        
        Returns:
            bool: 元素是否隐藏
        """
        try:
            page.wait_for_selector(selector, state='hidden', timeout=timeout)
            return True
        except Exception:
            return False
    
    @staticmethod
    def text_present(page: Page, text: str, timeout: int = 10000) -> bool:
        """
        等待页面出现指定文本
        
        Args:
            page: Playwright页面对象
            text: 期望出现的文本
            timeout: 超时时间
        
        Returns:
            bool: 文本是否出现
        """
        try:
            page.wait_for_function(
                f'document.body.innerText.includes("{text}")',
                timeout=timeout
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    def element_enabled(locator: Locator, timeout: int = 10000) -> bool:
        """
        等待元素可启用（非禁用状态）
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
        
        Returns:
            bool: 元素是否可用
        """
        try:
            locator.wait_for(timeout=timeout)
            return locator.is_enabled()
        except Exception:
            return False


def wait_for_navigation(page: Page, expected_url: str, timeout: int = 30000):
    """
    等待页面导航完成
    
    Args:
        page: Playwright页面对象
        expected_url: 期望URL（可以是部分匹配）
        timeout: 超时时间
    """
    page.wait_for_url(f"**/{expected_url}**", timeout=timeout, wait_until='networkidle')


def wait_for_ajax_complete(page: Page, timeout: int = 10000):
    """
    等待AJAX请求完成
    
    Args:
        page: Playwright页面对象
        timeout: 超时时间
    """
    page.wait_for_load_state('networkidle', timeout=timeout)
