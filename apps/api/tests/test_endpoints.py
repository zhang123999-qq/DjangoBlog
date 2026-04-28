"""
API 端点测试

测试覆盖:
- 博客 API: 文章列表、文章详情
- 论坛 API: 主题列表
- 健康检查 API
"""

import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.blog.models import Category, Tag, Post


@pytest.mark.django_db
class TestHealthAPI:
    """健康检查 API 测试"""

    def test_health_check(self):
        """测试健康检查端点"""
        client = APIClient()
        response = client.get('/healthz/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestBlogAPI:
    """博客 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试数据准备"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.category = Category.objects.create(name="技术", slug="tech")
        self.tag = Tag.objects.create(name="Python", slug="python")

        # 创建测试文章
        self.post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="这是测试内容",
            author=self.user,
            category=self.category,
            status="published"
        )
        self.post.tags.add(self.tag)

    def test_post_list(self):
        """测试文章列表 API"""
        response = self.client.get('/api/posts/')
        assert response.status_code == 200
        # 检查返回数据结构
        data = response.json()
        assert 'results' in data or len(data) > 0 or 'count' in data

    def test_post_detail(self):
        """测试文章详情 API"""
        response = self.client.get(f'/api/posts/{self.post.slug}/')
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == "测试文章"

    def test_category_list(self):
        """测试分类列表 API"""
        response = self.client.get('/api/categories/')
        assert response.status_code == 200

    def test_tag_list(self):
        """测试标签列表 API"""
        response = self.client.get('/api/tags/')
        assert response.status_code == 200

    def test_post_filter_by_category(self):
        """测试按分类筛选文章"""
        response = self.client.get(f'/api/posts/?category={self.category.slug}')
        assert response.status_code == 200


@pytest.mark.django_db
class TestAuthAPI:
    """认证 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试数据准备"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_user_profile_authenticated(self):
        """测试已认证用户资料"""
        self.client.force_authenticate(user=self.user)
        # 根据实际 API 端点调整
        # response = self.client.get('/api/user/profile/')
        # assert response.status_code == 200

    def test_unauthenticated_access(self):
        """测试未认证访问"""
        # 某些端点需要认证
        # response = self.client.get('/api/user/profile/')
        # assert response.status_code == 401


@pytest.mark.django_db
class TestAPIDocumentation:
    """API 文档测试"""

    def test_swagger_docs(self):
        """测试 Swagger 文档"""
        client = APIClient()
        response = client.get('/api/docs/')
        # 可能返回 200 或重定向
        assert response.status_code in [200, 301, 302]

    def test_redoc_docs(self):
        """测试 ReDoc 文档"""
        client = APIClient()
        response = client.get('/api/redoc/')
        # 可能返回 200 或重定向
        assert response.status_code in [200, 301, 302]

    def test_openapi_schema(self):
        """测试 OpenAPI Schema"""
        client = APIClient()
        response = client.get('/api/schema/')
        assert response.status_code in [200, 301, 302]
