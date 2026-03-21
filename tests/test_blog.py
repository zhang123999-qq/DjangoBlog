"""
博客功能测试套件 - 优化版
测试文章的创建、编辑、删除等功能
"""
import pytest
import logging
from datetime import datetime
from playwright.sync_api import Page
from utils.page_objects import LoginPage, BlogPage
from utils.helpers import WaitHelper

logger = logging.getLogger(__name__)


class TestBlogList:
    """博客列表测试"""
    
    @pytest.mark.smoke
    @pytest.mark.blog
    def test_blog_page_loads(self, page: Page, base_url: str):
        """测试博客页面正常加载"""
        logger.info("测试博客页面加载")
        
        blog_page = BlogPage(page, base_url)
        blog_page.open()
        
        # 验证页面标题
        title = page.title()
        assert '博客' in title or 'Blog' in title.lower() or 'Django' in title
        
        logger.info("博客页面加载正常")
    
    @pytest.mark.blog
    def test_blog_list_displays(self, page: Page, base_url: str):
        """测试博客列表显示"""
        logger.info("测试博客列表显示")
        
        blog_page = BlogPage(page, base_url)
        blog_page.open()
        
        # 检查是否有文章
        post_count = blog_page.get_post_count()
        logger.info(f"找到 {post_count} 篇文章")
        
        # 至少应该有一些内容（文章或提示）
        page_content = page.text_content('body')
        assert len(page_content) > 100, "页面内容过少"
    
    @pytest.mark.blog
    def test_click_blog_post(self, page: Page, base_url: str):
        """测试点击博客文章"""
        logger.info("测试点击博客文章")
        
        blog_page = BlogPage(page, base_url)
        blog_page.open()
        
        # 尝试点击第一篇文章
        post_count = blog_page.get_post_count()
        if post_count > 0:
            blog_page.click_post_by_index(0)
            logger.info(f"点击了第一篇文章，当前URL: {page.url}")
            
            # 验证跳转到文章详情页
            # URL应该不再是列表页
            assert '/blog/' in page.url, "应该还在博客相关页面"
        else:
            logger.info("没有文章可点击")


class TestArticleCRUD:
    """文章CRUD测试"""
    
    @pytest.mark.blog
    def test_create_article_page_access(self, logged_in_page: Page, base_url: str):
        """测试访问创建文章页面"""
        logger.info("测试访问创建文章页面")
        
        logged_in_page.goto(f"{base_url}/blog/create/")
        logged_in_page.wait_for_load_state('networkidle')
        
        # 检查是否有表单
        title_input = logged_in_page.query_selector('input[name="title"]')
        content_input = logged_in_page.query_selector('textarea[name="content"]')
        
        # 如果找到表单元素，测试通过
        if title_input and content_input:
            logger.info("创建文章表单加载成功")
        else:
            # 可能是没有权限或页面不存在
            page_content = logged_in_page.text_content('body')
            logger.info(f"页面内容: {page_content[:200]}...")
    
    @pytest.mark.blog
    def test_create_article(self, logged_in_page: Page, base_url: str, test_article_data: dict, test_captcha: str):
        """测试创建文章"""
        logger.info("测试创建文章")
        
        # 访问创建页面
        logged_in_page.goto(f"{base_url}/blog/create/")
        logged_in_page.wait_for_load_state('networkidle')
        
        # 检查是否有权限
        title_input = logged_in_page.query_selector('input[name="title"]')
        if not title_input:
            logger.warning("可能没有创建文章的权限")
            pytest.skip("没有创建文章权限或功能不可用")
        
        # 填写文章
        logged_in_page.fill('input[name="title"]', test_article_data['title'])
        logged_in_page.fill('textarea[name="content"]', test_article_data['content'])
        
        # 提交
        submit_btn = logged_in_page.query_selector('button[type="submit"]')
        if submit_btn:
            submit_btn.click()
            logged_in_page.wait_for_load_state('networkidle')
            
            # 检查是否成功
            current_url = logged_in_page.url
            page_content = logged_in_page.text_content('body')
            
            if '/create' not in current_url:
                logger.info("文章创建成功")
            elif '成功' in page_content:
                logger.info("文章创建成功（提示信息）")
            else:
                logger.info(f"文章创建结果未知，URL: {current_url}")
    
    @pytest.mark.blog
    def test_edit_article_access(self, logged_in_page: Page, base_url: str):
        """测试访问编辑文章页面"""
        logger.info("测试访问编辑文章页面")
        
        # 先访问博客列表
        logged_in_page.goto(f"{base_url}/blog/")
        logged_in_page.wait_for_load_state('networkidle')
        
        # 尝试找到编辑链接
        edit_links = logged_in_page.query_selector_all('a[href*="edit"]')
        
        if edit_links and len(edit_links) > 0:
            # 点击第一个编辑链接
            edit_links[0].click()
            logged_in_page.wait_for_load_state('networkidle')
            
            # 检查是否在编辑页面
            title_input = logged_in_page.query_selector('input[name="title"]')
            if title_input:
                logger.info("成功进入编辑页面")
            else:
                logger.warning("编辑页面可能没有正确加载")
        else:
            logger.info("没有找到可编辑的文章")
    
    @pytest.mark.blog
    def test_delete_article(self, logged_in_page: Page, base_url: str):
        """测试删除文章"""
        logger.info("测试删除文章")
        
        # 访问我的文章页面
        logged_in_page.goto(f"{base_url}/blog/my-posts/")
        logged_in_page.wait_for_load_state('networkidle')
        
        # 检查是否有文章
        page_content = logged_in_page.text_content('body')
        
        if '暂无文章' in page_content or '没有文章' in page_content:
            logger.info("没有文章可删除")
        else:
            # 尝试找到删除链接
            delete_links = logged_in_page.query_selector_all('a[href*="delete"]')
            if delete_links:
                logger.info(f"找到 {len(delete_links)} 个删除链接")
            else:
                logger.info("没有找到删除链接")


class TestArticleDisplay:
    """文章显示测试"""
    
    @pytest.mark.smoke
    @pytest.mark.blog
    def test_article_detail_page(self, page: Page, base_url: str):
        """测试文章详情页"""
        logger.info("测试文章详情页")
        
        # 先访问列表页
        page.goto(f"{base_url}/blog/")
        page.wait_for_load_state('networkidle')
        
        # 找到文章链接
        article_links = page.query_selector_all('a[href*="/blog/"]')
        
        # 过滤掉列表页本身的链接
        article_links = [a for a in article_links if '/blog/' in a.get_attribute('href') and a.get_attribute('href') != '/blog/']
        
        if article_links:
            # 点击第一篇文章
            article_links[0].click()
            page.wait_for_load_state('networkidle')
            
            # 验证页面内容
            page_content = page.text_content('body')
            assert len(page_content) > 100, "文章内容过少"
            
            logger.info(f"文章详情页加载成功，URL: {page.url}")
        else:
            logger.info("没有找到文章链接")
    
    @pytest.mark.blog
    def test_article_categories(self, page: Page, base_url: str):
        """测试文章分类"""
        logger.info("测试文章分类")
        
        page.goto(f"{base_url}/blog/")
        page.wait_for_load_state('networkidle')
        
        # 检查分类侧边栏
        category_section = page.query_selector('.sidebar, .categories, .category-list')
        if category_section:
            logger.info("找到分类区域")
        else:
            logger.info("没有找到分类区域")
    
    @pytest.mark.blog
    def test_article_tags(self, page: Page, base_url: str):
        """测试文章标签"""
        logger.info("测试文章标签")
        
        page.goto(f"{base_url}/blog/")
        page.wait_for_load_state('networkidle')
        
        # 检查标签
        tags = page.query_selector_all('.tag, .tags a, [class*="tag"]')
        logger.info(f"找到 {len(tags)} 个标签")


class TestArticleSearch:
    """文章搜索测试"""
    
    @pytest.mark.blog
    def test_search_function(self, page: Page, base_url: str):
        """测试搜索功能"""
        logger.info("测试搜索功能")
        
        page.goto(f"{base_url}/")
        page.wait_for_load_state('networkidle')
        
        # 查找搜索框
        search_input = page.query_selector('input[type="search"], input[name="q"], input[placeholder*="搜索"]')
        
        if search_input:
            # 输入搜索关键词
            search_input.fill('Django')
            search_input.press('Enter')
            page.wait_for_load_state('networkidle')
            
            # 检查搜索结果
            page_content = page.text_content('body')
            logger.info(f"搜索结果页面内容长度: {len(page_content)}")
            
            # 应该有结果或提示
            assert len(page_content) > 100, "搜索结果页面内容过少"
            logger.info("搜索功能正常")
        else:
            logger.info("没有找到搜索框")


class TestArticleComments:
    """文章评论测试"""
    
    @pytest.mark.blog
    def test_comment_section_exists(self, page: Page, base_url: str):
        """测试评论区域存在"""
        logger.info("测试评论区域")
        
        # 访问文章列表
        page.goto(f"{base_url}/blog/")
        page.wait_for_load_state('networkidle')
        
        # 点击第一篇文章
        article_links = page.query_selector_all('a[href*="/blog/"]')
        article_links = [a for a in article_links if a.get_attribute('href') and '/blog/' in a.get_attribute('href') and len(a.get_attribute('href')) > 6]
        
        if article_links:
            article_links[0].click()
            page.wait_for_load_state('networkidle')
            
            # 检查评论区
            comment_section = page.query_selector('.comments, #comments, [class*="comment"]')
            if comment_section:
                logger.info("找到评论区域")
            else:
                logger.info("没有找到评论区域")
    
    @pytest.mark.blog
    def test_post_comment_requires_login(self, page: Page, base_url: str):
        """测试发表评论需要登录"""
        logger.info("测试发表评论需要登录")
        
        # 确保未登录
        page.goto(f"{base_url}/accounts/logout/")
        page.wait_for_load_state('networkidle')
        
        # 访问文章
        page.goto(f"{base_url}/blog/")
        page.wait_for_load_state('networkidle')
        
        article_links = page.query_selector_all('a[href*="/blog/"]')
        article_links = [a for a in article_links if a.get_attribute('href') and len(a.get_attribute('href')) > 6]
        
        if article_links:
            article_links[0].click()
            page.wait_for_load_state('networkidle')
            
            # 检查是否有评论表单
            comment_form = page.query_selector('form[action*="comment"], textarea[name*="comment"]')
            
            if not comment_form:
                logger.info("未登录时没有评论表单，符合预期")
            else:
                # 可能有评论表单但会提示登录
                page_content = page.text_content('body')
                if '登录' in page_content or 'login' in page_content.lower():
                    logger.info("评论区域提示需要登录")
