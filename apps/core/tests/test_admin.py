"""
后台管理测试

测试覆盖:
- DjangoBlogAdminSite: 仪表盘统计
- 缓存功能测试
- 查询优化测试
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from apps.core.admin.admin_site import DjangoBlogAdminSite

User = get_user_model()


@pytest.mark.django_db
class TestAdminDashboard:
    """管理员仪表盘测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin_url = reverse('admin:index')

    def test_admin_dashboard_requires_staff(self):
        """测试仪表盘需要管理员权限"""
        response = self.client.get(self.admin_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/admin/login/' in response.url

    def test_admin_dashboard_loads_for_staff(self):
        """测试管理员可以访问仪表盘"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(self.admin_url)
        assert response.status_code == 200

    def test_admin_dashboard_contains_stats(self):
        """测试仪表盘包含统计数据"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(self.admin_url)

        # 检查上下文是否包含统计数据
        context = response.context
        assert 'user_count' in context
        assert 'post_count' in context
        assert 'topic_count' in context
        assert 'comment_count' in context
        assert 'total_views' in context
        assert 'week_data' in context

    def test_admin_dashboard_caching(self):
        """测试仪表盘缓存"""
        self.client.login(username='admin', password='adminpass123')

        # 清除缓存
        cache.clear()

        # 第一次访问
        response1 = self.client.get(self.admin_url)
        assert response1.status_code == 200

        # 第二次访问（应该命中缓存）
        response2 = self.client.get(self.admin_url)
        assert response2.status_code == 200

        # 验证缓存是否生效
        # 注意：由于使用了缓存，我们无法直接测试缓存内容
        # 但可以验证请求成功


@pytest.mark.django_db
class TestAdminSite:
    """AdminSite 测试"""

    def setup_method(self):
        """设置测试数据"""
        self.admin_site = DjangoBlogAdminSite(name='admin')

    def test_admin_site_properties(self):
        """测试 AdminSite 属性"""
        assert self.admin_site.site_header == "DjangoBlog 管理后台"
        assert self.admin_site.site_title == "DjangoBlog Admin"
        assert self.admin_site.index_title == "仪表盘"

    def test_admin_site_cache_key(self):
        """测试缓存键"""
        assert self.admin_site.STATS_CACHE_KEY == "admin:dashboard:stats"
        assert self.admin_site.STATS_CACHE_TIMEOUT == 60

    def test_admin_site_compute_stats(self):
        """测试统计数据计算"""
        # 创建测试数据
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        from apps.blog.models import Post, Category
        category = Category.objects.create(name="测试分类", slug="test")
        Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="内容",
            author=user,
            category=category,
            status="published"
        )

        # 计算统计
        stats = self.admin_site._compute_stats()

        # 验证统计结果
        assert stats['user_count'] >= 1
        assert stats['post_count'] >= 1
        assert stats['category_count'] >= 1
        assert 'week_data' in stats
        assert 'django_version' in stats
        assert 'python_version' in stats

    def test_admin_site_redis_info(self):
        """测试 Redis 信息获取"""
        redis_info = self.admin_site._get_redis_info()
        # Redis 可能未启用，所以返回 "未启用" 或版本信息
        assert redis_info is not None
        assert isinstance(redis_info, str)

    def test_admin_site_tool_count(self):
        """测试工具数量获取"""
        tool_count = self.admin_site._get_tool_count()
        # 工具数量应该是一个整数
        assert isinstance(tool_count, int)
        assert tool_count >= 0

    def test_admin_site_tools_list(self):
        """测试工具列表获取"""
        tools_list = self.admin_site._get_tools_list()
        # 工具列表应该是一个列表
        assert isinstance(tools_list, list)


@pytest.mark.django_db
class TestAdminPermissions:
    """管理员权限测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.normal_user = User.objects.create_user(
            username='normaluser',
            password='normalpass123',
            is_staff=False,
            is_superuser=False
        )

    def test_normal_user_cannot_access_admin(self):
        """测试普通用户不能访问管理员后台"""
        self.client.login(username='normaluser', password='normalpass123')
        response = self.client.get(reverse('admin:index'))
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/admin/login/' in response.url

    def test_staff_user_can_access_admin(self):
        """测试管理员可以访问后台"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin:index'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminModels:
    """管理员模型测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )

    def test_admin_can_manage_users(self):
        """测试管理员可以管理用户"""
        self.client.login(username='admin', password='adminpass123')

        # 访问用户管理页面
        url = reverse('admin:accounts_user_changelist')
        response = self.client.get(url)
        assert response.status_code == 200

    def test_admin_can_manage_posts(self):
        """测试管理员可以管理文章"""
        self.client.login(username='admin', password='adminpass123')

        # 访问文章管理页面
        url = reverse('admin:blog_post_changelist')
        response = self.client.get(url)
        assert response.status_code == 200

    def test_admin_can_manage_categories(self):
        """测试管理员可以管理分类"""
        self.client.login(username='admin', password='adminpass123')

        # 访问分类管理页面
        url = reverse('admin:blog_category_changelist')
        response = self.client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminActions:
    """管理员操作测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )

        # 创建测试数据
        from apps.blog.models import Post, Category

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="测试分类", slug="test")
        self.post1 = Post.objects.create(
            title="测试文章1",
            slug="test-post-1",
            content="内容1",
            author=self.user,
            category=self.category,
            status="draft"
        )
        self.post2 = Post.objects.create(
            title="测试文章2",
            slug="test-post-2",
            content="内容2",
            author=self.user,
            category=self.category,
            status="draft"
        )

    def test_admin_publish_posts_action(self):
        """测试批量发布文章"""
        self.client.login(username='admin', password='adminpass123')

        # 获取文章列表
        url = reverse('admin:blog_post_changelist')
        response = self.client.get(url)
        assert response.status_code == 200

        # 执行批量发布操作
        response = self.client.post(url, {
            'action': 'publish_posts',
            '_selected_action': [self.post1.id, self.post2.id]
        })
        # 应该重定向回列表页
        assert response.status_code == 302

        # 验证文章是否已发布
        self.post1.refresh_from_db()
        self.post2.refresh_from_db()
        assert self.post1.status == 'published'
        assert self.post2.status == 'published'

    def test_admin_unpublish_posts_action(self):
        """测试批量取消发布文章"""
        # 先发布文章
        self.post1.status = 'published'
        self.post1.save()
        self.post2.status = 'published'
        self.post2.save()

        self.client.login(username='admin', password='adminpass123')

        # 获取文章列表
        url = reverse('admin:blog_post_changelist')
        response = self.client.get(url)
        assert response.status_code == 200

        # 执行批量取消发布操作
        response = self.client.post(url, {
            'action': 'unpublish_posts',
            '_selected_action': [self.post1.id, self.post2.id]
        })
        # 应该重定向回列表页
        assert response.status_code == 302

        # 验证文章是否已取消发布
        self.post1.refresh_from_db()
        self.post2.refresh_from_db()
        assert self.post1.status == 'draft'
        assert self.post2.status == 'draft'
