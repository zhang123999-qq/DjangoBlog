"""
测试工具包
"""
from .data_generator import DataGenerator
from .wait_for import WaitFor, wait_for_navigation, wait_for_ajax_complete

__all__ = ['DataGenerator', 'WaitFor', 'wait_for_navigation', 'wait_for_ajax_complete']
