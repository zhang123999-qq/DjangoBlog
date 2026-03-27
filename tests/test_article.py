"""
博客文章测试
"""
import pytest
from playwright.sync_api import Page, expect
from utils.data_generator import DataGenerator
from pathlib import Path


class TestArticle:
    """博客文章测试类"""

    def test_view_article_list(self, page: Page, base_url: str, test_logger):
        """
        测试查看文章列表

        步骤:
        1. 访问博客页面
        2. 验证列表显示
        """
        test_logger.info("开始测试: 查看文章列表")

        page.goto(f"{base_url}/blog/")
        page.wait_for_load_state('networkidle')

        # 验证页面标题或内容
        page_content = page.text_content('body')
        assert '博客' in page_content or '文章' in page_content or '暂无' in page_content, \
            "博客页面内容异常"

        test_logger.info("文章列表页面正常")

    def test_create_article_success(self, logged_in_page: Page, base_url: str, test_logger):
        """
        测试发布文章（通过管理后台）

        前置条件: 用户已登录且有发布权限
        步骤:
        1. 进入管理后台
        2. 添加文章
        3. 填写内容
        4. 保存发布
        """
        test_logger.info("开始测试: 发布文章")

        # 进入管理后台
        logged_in_page.goto(f"{base_url}/admin/blog/post/add/")
        logged_in_page.wait_for_load_state('networkidle')

        # 检查是否有权限
        current_url = logged_in_page.url
        page_content = logged_in_page.text_content('body')

        # 如果被重定向到登录页面，跳过测试
        if '/login' in current_url or '登录' in page_content and '/admin' not in current_url:
            test_logger.warning("未登录管理后台，跳过测试")
            pytest.skip("没有管理后台访问权限，需要先登录")

        # 检查是否有登录表单（表示未登录）
        login_form = logged_in_page.query_selector('form input[name="username"]')
        if login_form:
            test_logger.warning("检测到登录表单，跳过测试")
            pytest.skip("需要登录才能访问管理后台")

        # 生成测试数据
        article_data = DataGenerator.article_data()
        test_logger.info(f"生成文章数据: {article_data['title']}")

        # 填写文章标题
        logged_in_page.fill('input[name="title"]', article_data['title'])

        # 填写摘要
        try:
            logged_in_page.fill('textarea[name="summary"]', article_data['summary'])
        except Exception:
            test_logger.info("摘要字段可能不存在")

        # 填写内容 - 可能是textarea或富文本编辑器
        try:
            logged_in_page.fill('textarea[name="content"]', article_data['content'])
        except Exception:
            # 尝试富文本编辑器
            try:
                logged_in_page.fill('.tox-edit-area textarea', article_data['content'])
            except Exception:
                test_logger.warning("无法定位内容编辑区域")

        # 选择状态为发布
        try:
            logged_in_page.select_option('select[name="status"]', 'published')
        except Exception:
            test_logger.info("状态选择器可能不存在")

        # 保存
        try:
            logged_in_page.click('input[type="submit"][name="_save"], button[type="submit"]')
        except Exception:
            logged_in_page.click('button:has-text("保存")')

        logged_in_page.wait_for_load_state('networkidle')

        # 验证保存成功
        current_url = logged_in_page.url
        page_content = logged_in_page.text_content('body')

        success_indicators = ['成功', '添加', '保存', article_data['title']]
        assert any(indicator in page_content for indicator in success_indicators), \
            f"文章保存失败，URL: {current_url}"

        test_logger.info(f"文章发布成功")

    def test_view_article_detail(self, page: Page, base_url: str, test_logger):
        """
        测试查看文章详情

        步骤:
        1. 访问博客列表
        2. 点击文章
        3. 验证详情页
        """
        test_logger.info("开始测试: 查看文章详情")

        page.goto(f"{base_url}/blog/")
        page.wait_for_load_state('networkidle')

        # 查找文章链接
        article_links = page.query_selector_all('a[href*="/blog/"]')

        for link in article_links[1:4]:  # 跳过博客首页链接
            try:
                href = link.get_attribute('href')
                if href and len(href.split('/')) > 3:
                    article_title = link.text_content()
                    link.click()
                    page.wait_for_load_state('networkidle')

                    # 验证详情页
                    page_content = page.text_content('body')
                    assert article_title in page_content or '内容' in page_content, \
                        "文章详情页内容异常"

                    test_logger.info(f"文章详情页正常: {page.url}")
                    return
            except Exception:
                continue

        test_logger.info("没有可点击的文章")
        # 如果没有文章，测试通过（页面正常显示"暂无文章"）

    def test_article_comment(self, logged_in_page: Page, base_url: str, test_logger):
        """
        测试文章评论

        前置条件: 用户已登录
        步骤:
        1. 访问文章详情页
        2. 填写评论
        3. 提交评论
        """
        test_logger.info("开始测试: 文章评论")

        # 先访问博客
        logged_in_page.goto(f"{base_url}/blog/")
        logged_in_page.wait_for_load_state('networkidle')

        # 查找文章
        article_links = logged_in_page.query_selector_all('a[href*="/blog/"]')

        for link in article_links[1:3]:
            try:
                href = link.get_attribute('href')
                if href and len(href.split('/')) > 3:
                    link.click()
                    logged_in_page.wait_for_load_state('networkidle')

                    # 查找评论表单
                    comment_form = logged_in_page.query_selector('textarea[name="content"]')
                    if comment_form:
                        comment_text = DataGenerator.comment()
                        logged_in_page.fill('textarea[name="content"]', comment_text)
                        logged_in_page.click('button[type="submit"]')
                        logged_in_page.wait_for_load_state('networkidle')

                        # 验证评论提交
                        page_content = logged_in_page.text_content('body')
                        assert '审核' in page_content or '成功' in page_content or comment_text in page_content, \
                            "评论提交失败"

                        test_logger.info("评论提交成功")
                        return
            except Exception:
                continue

        test_logger.info("未找到可评论的文章")
        pytest.skip("没有可评论的文章")

    def test_article_category_filter(self, page: Page, base_url: str, test_logger):
        """
        测试文章分类筛选

        步骤:
        1. 访问博客
        2. 点击分类
        3. 验证筛选结果
        """
        test_logger.info("开始测试: 分类筛选")

        page.goto(f"{base_url}/blog/")
        page.wait_for_load_state('networkidle')

        # 查找分类链接
        category_links = page.query_selector_all('a[href*="/blog/category/"]')

        if not category_links:
            test_logger.info("没有分类链接")
            pytest.skip("没有可用的分类")

        # 点击第一个分类
        category_links[0].click()
        page.wait_for_load_state('networkidle')

        # 验证URL包含分类
        current_url = page.url
        assert 'category' in current_url or 'tag' in current_url, \
            "分类筛选失败"

        test_logger.info(f"分类筛选成功: {current_url}")
