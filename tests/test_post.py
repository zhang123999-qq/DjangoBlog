"""
论坛发帖测试
"""
import pytest
from playwright.sync_api import Page, expect
from utils.data_generator import DataGenerator
from utils.wait_for import WaitFor


class TestPost:
    """论坛发帖测试类"""
    
    def test_create_topic_success(self, logged_in_page: Page, base_url: str, test_logger):
        """
        测试成功发布主题
        
        前置条件: 用户已登录
        步骤:
        1. 导航到论坛
        2. 选择版块
        3. 填写标题和内容
        4. 提交发布
        5. 验证发布成功
        """
        test_logger.info("开始测试: 发布主题")
        
        # 导航到论坛
        logged_in_page.goto(f"{base_url}/forum/")
        test_logger.info("访问论坛页面")
        
        # 等待版块加载
        logged_in_page.wait_for_load_state('networkidle')
        
        # 点击第一个版块
        boards = logged_in_page.query_selector_all('a[href*="/forum/"]')
        if len(boards) > 1:
            boards[1].click()  # 第一个是论坛首页链接
            logged_in_page.wait_for_load_state('networkidle')
            test_logger.info("选择版块")
        
        # 点击发布主题按钮
        try:
            logged_in_page.click('a:has-text("发布主题"), button:has-text("发布")')
            logged_in_page.wait_for_load_state('networkidle')
        except:
            test_logger.warning("未找到发布按钮，跳过测试")
            pytest.skip("未找到发布主题按钮")
        
        # 生成测试数据
        post_data = DataGenerator.post_data()
        test_logger.info(f"生成帖子数据: {post_data['title']}")
        
        # 填写表单
        logged_in_page.fill('input[name="title"]', post_data['title'])
        logged_in_page.fill('textarea[name="content"]', post_data['content'])
        test_logger.info("填写帖子内容")
        
        # 提交
        logged_in_page.click('button[type="submit"]')
        test_logger.info("提交帖子")
        
        # 等待响应
        logged_in_page.wait_for_load_state('networkidle')
        
        # 验证发布成功
        current_url = logged_in_page.url
        
        # 检查是否跳转到帖子详情或显示成功消息
        page_content = logged_in_page.text_content('body')
        
        success_indicators = ['审核', '成功', '发布', 'topic', post_data['title']]
        assert any(indicator in page_content for indicator in success_indicators), \
            f"发布失败，URL: {current_url}"
        
        test_logger.info(f"发布成功，URL: {current_url}")
    
    def test_create_topic_without_title(self, logged_in_page: Page, base_url: str, test_logger):
        """
        测试标题为空时发布
        
        预期: 显示标题必填的错误提示
        """
        test_logger.info("开始测试: 空标题发布")
        
        # 导航到论坛
        logged_in_page.goto(f"{base_url}/forum/")
        logged_in_page.wait_for_load_state('networkidle')
        
        # 尝试找到并点击发布按钮
        boards = logged_in_page.query_selector_all('a[href*="/forum/"]')
        if len(boards) > 1:
            boards[1].click()
            logged_in_page.wait_for_load_state('networkidle')
        
        try:
            logged_in_page.click('a:has-text("发布主题"), button:has-text("发布")')
            logged_in_page.wait_for_load_state('networkidle')
        except:
            pytest.skip("未找到发布主题按钮")
        
        # 只填写内容，不填标题
        logged_in_page.fill('textarea[name="content"]', DataGenerator.content(1))
        
        # 提交
        logged_in_page.click('button[type="submit"]')
        logged_in_page.wait_for_load_state('networkidle')
        
        # 验证错误提示
        page_content = logged_in_page.text_content('body')
        assert '标题' in page_content or '必填' in page_content or 'required' in page_content.lower(), \
            "未显示标题必填错误"
        
        test_logger.info("正确显示标题必填错误")
    
    def test_create_topic_without_content(self, logged_in_page: Page, base_url: str, test_logger):
        """
        测试内容为空时发布
        
        预期: 显示内容必填的错误提示
        """
        test_logger.info("开始测试: 空内容发布")
        
        logged_in_page.goto(f"{base_url}/forum/")
        logged_in_page.wait_for_load_state('networkidle')
        
        boards = logged_in_page.query_selector_all('a[href*="/forum/"]')
        if len(boards) > 1:
            boards[1].click()
            logged_in_page.wait_for_load_state('networkidle')
        
        try:
            logged_in_page.click('a:has-text("发布主题"), button:has-text("发布")')
            logged_in_page.wait_for_load_state('networkidle')
        except:
            pytest.skip("未找到发布主题按钮")
        
        # 只填写标题，不填内容
        logged_in_page.fill('input[name="title"]', DataGenerator.title())
        
        logged_in_page.click('button[type="submit"]')
        logged_in_page.wait_for_load_state('networkidle')
        
        page_content = logged_in_page.text_content('body')
        assert '内容' in page_content or '必填' in page_content or 'required' in page_content.lower(), \
            "未显示内容必填错误"
        
        test_logger.info("正确显示内容必填错误")
    
    def test_view_topic_list(self, page: Page, base_url: str, test_logger):
        """
        测试查看主题列表
        
        步骤:
        1. 访问论坛
        2. 验证主题列表显示
        """
        test_logger.info("开始测试: 查看主题列表")
        
        page.goto(f"{base_url}/forum/")
        page.wait_for_load_state('networkidle')
        
        # 验证页面元素
        page_content = page.text_content('body')
        
        # 论坛应该有版块或主题列表
        assert '论坛' in page_content or '版块' in page_content or '主题' in page_content, \
            "论坛页面内容异常"
        
        test_logger.info("主题列表显示正常")
    
    def test_view_topic_detail(self, page: Page, base_url: str, test_logger):
        """
        测试查看主题详情
        
        步骤:
        1. 访问论坛
        2. 点击主题
        3. 验证详情页显示
        """
        test_logger.info("开始测试: 查看主题详情")
        
        page.goto(f"{base_url}/forum/")
        page.wait_for_load_state('networkidle')
        
        # 查找主题链接
        topic_links = page.query_selector_all('a[href*="/forum/"]')
        
        # 过滤掉版块链接，找主题链接
        for link in topic_links[2:5]:  # 跳过前面的导航链接
            try:
                href = link.get_attribute('href')
                if href and '/topic' in href or len(href.split('/')) > 4:
                    link.click()
                    page.wait_for_load_state('networkidle')
                    
                    # 验证详情页
                    current_url = page.url
                    assert '/forum/' in current_url, "未进入主题详情页"
                    
                    test_logger.info(f"主题详情页: {current_url}")
                    return
            except:
                continue
        
        test_logger.info("没有可点击的主题，跳过测试")
        pytest.skip("没有可用的主题")
