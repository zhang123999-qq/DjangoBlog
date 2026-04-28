"""
核心视图测试

测试覆盖:
- home_view: 首页视图
- search_view: 搜索视图
- contact_view: 联系我们视图
- healthz_view: 健康检查视图
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.core.cache import cache
from apps.accounts.models import User
from apps.blog.models import Post, Category


@pytest.mark.django_db
class TestHomeView:
    """首页视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="技术", slug="tech")
        self.post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="内容",
            author=self.user,
            status="published"
        )
        self.home_url = reverse('core:home')

    def test_home_view_loads(self):
        """测试首页加载"""
        response = self.client.get(self.home_url)
        assert response.status_code == 200
        assert 'latest_posts' in response.context
        assert 'post_count' in response.context

    def test_home_view_caching(self):
        """测试首页缓存"""
        # 第一次访问
        response1 = self.client.get(self.home_url)
        assert response1.status_code == 200

        # 第二次访问（应该命中缓存）
        response2 = self.client.get(self.home_url)
        assert response2.status_code == 200

        # 清除缓存后再次访问
        cache.clear()
        response3 = self.client.get(self.home_url)
        assert response3.status_code == 200

    def test_home_view_context_data(self):
        """测试首页上下文数据"""
        response = self.client.get(self.home_url)
        assert response.status_code == 200

        # 检查必要的上下文变量
        required_keys = [
            'latest_posts', 'hot_topics', 'popular_tools',
            'post_count', 'topic_count', 'comment_count',
            'user_count', 'tool_count', 'view_count'
        ]
        for key in required_keys:
            assert key in response.context, f"Missing context key: {key}"

    def test_home_view_only_published_posts(self):
        """测试首页只显示已发布文章"""
        # 创建草稿文章
        Post.objects.create(
            title="草稿文章",
            slug="draft-post",
            content="草稿内容",
            author=self.user,
            status="draft"
        )

        response = self.client.get(self.home_url)
        assert response.status_code == 200

        # 检查只有已发布的文章
        latest_posts = response.context['latest_posts']
        for post in latest_posts:
            assert post.status == 'published'

    def test_home_view_performance(self):
        """测试首页性能（查询次数）"""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.home_url)
            assert response.status_code == 200

        # 检查查询次数（应该在合理范围内）
        assert len(queries) <= 10, f"Too many queries: {len(queries)}"


@pytest.mark.django_db
class TestContactView:
    """联系我们视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.contact_url = reverse('core:contact')

    def test_contact_view_get(self):
        """测试联系我们页面GET请求"""
        response = self.client.get(self.contact_url)
        assert response.status_code == 200
        assert 'core/contact.html' in [t.name for t in response.templates]

    def test_contact_view_post(self):
        """测试联系我们页面POST请求"""
        response = self.client.post(self.contact_url, {
            'name': '测试用户',
            'email': 'test@example.com',
            'message': '这是一条测试消息'
        })
        # 应该重定向回联系我们页面
        assert response.status_code == 302
        assert response.url == reverse('core:contact')

    def test_contact_view_post_shows_message(self):
        """测试联系我们POST后显示成功消息"""
        response = self.client.post(self.contact_url, {
            'name': '测试用户',
            'email': 'test@example.com',
            'message': '这是一条测试消息'
        }, follow=True)

        # 检查是否有成功消息
        assert len(response.context['messages']) > 0
        messages = list(response.context['messages'])
        assert any('感谢您的留言' in str(message) for message in messages)

    def test_contact_view_anonymous_access(self):
        """测试匿名用户可以访问联系我们页面"""
        response = self.client.get(self.contact_url)
        assert response.status_code == 200

    def test_contact_view_authenticated_access(self):
        """测试登录用户可以访问联系我们页面"""
        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(self.contact_url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestSearchView:
    """搜索视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="技术", slug="tech")
        self.post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="这是测试内容",
            author=self.user,
            status="published"
        )
        self.search_url = reverse('core:search')

    def test_search_view_empty_query(self):
        """测试空搜索词"""
        response = self.client.get(self.search_url, {'q': ''})
        assert response.status_code == 200
        assert len(response.context['results']['posts']) == 0
        assert len(response.context['results']['topics']) == 0

    def test_search_view_with_query(self):
        """测试有搜索词"""
        response = self.client.get(self.search_url, {'q': '测试'})
        assert response.status_code == 200
        assert '测试' in response.context['query']

    def test_search_view_sanitization(self):
        """测试搜索词清理"""
        # 测试XSS清理
        response = self.client.get(self.search_url, {'q': '<script>alert("xss")</script>'})
        assert response.status_code == 200
        assert '<script>' not in response.context['query']

        # 测试SQL注入清理
        response = self.client.get(self.search_url, {'q': "'; DROP TABLE users; --"})
        assert response.status_code == 200
        assert 'DROP TABLE' not in response.context['query']

    def test_search_view_length_limit(self):
        """测试搜索词长度限制"""
        long_query = 'a' * 150  # 超过100字符
        response = self.client.get(self.search_url, {'q': long_query})
        assert response.status_code == 200
        assert len(response.context['query']) <= 100

    def test_search_view_result_limit(self):
        """测试搜索结果数量限制"""
        # 创建多个文章
        for i in range(25):
            Post.objects.create(
                title=f"测试文章{i}",
                slug=f"test-post-{i}",
                content=f"测试内容{i}",
                author=self.user,
                status="published"
            )

        response = self.client.get(self.search_url, {'q': '测试'})
        assert response.status_code == 200
        assert len(response.context['results']['posts']) <= 20  # 最多20条


@pytest.mark.django_db
class TestHealthCheckViews:
    """健康检查视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.healthz_url = reverse('core:healthz')
        self.readiness_url = reverse('core:readiness')
        self.liveness_url = reverse('core:liveness')

    def test_healthz_view_healthy(self):
        """测试健康检查正常状态"""
        response = self.client.get(self.healthz_url)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'checks' in data
        assert 'duration_ms' in data
        assert 'version' in data

    def test_readiness_view(self):
        """测试就绪检查"""
        response = self.client.get(self.readiness_url)
        assert response.status_code == 200
        data = response.json()
        assert 'ready' in data
        assert 'checks' in data

    def test_liveness_view(self):
        """测试存活检查"""
        response = self.client.get(self.liveness_url)
        assert response.status_code == 200
        data = response.json()
        assert data['alive'] is True

    def test_healthz_view_anonymous_access(self):
        """测试匿名用户可以访问健康检查"""
        response = self.client.get(self.healthz_url)
        assert response.status_code == 200

    def test_healthz_view_response_format(self):
        """测试健康检查响应格式"""
        response = self.client.get(self.healthz_url)
        data = response.json()

        # 检查必要的字段
        required_fields = ['status', 'checks', 'duration_ms', 'version']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        # 检查checks字段
        assert 'database' in data['checks']
        assert 'cache' in data['checks']
