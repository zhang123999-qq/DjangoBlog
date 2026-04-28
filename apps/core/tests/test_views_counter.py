"""
浏览量计数测试
"""

import pytest
from unittest.mock import MagicMock
from django.test import RequestFactory
from apps.core.views_counter import ViewsCounter, ViewsBuffer


class TestViewsBuffer:
    """内存缓冲区测试"""

    def test_add_view(self):
        """测试添加浏览记录"""
        buffer = ViewsBuffer()
        buffer._buffer.clear()
        buffer._recorded.clear()

        # 添加记录
        result = buffer.add('post', 1, 'user_1')

        assert result is True
        assert buffer._buffer['post'][1] == 1

    def test_prevent_duplicate(self):
        """测试防重复记录"""
        buffer = ViewsBuffer()
        buffer._buffer.clear()
        buffer._recorded.clear()

        # 添加记录
        buffer.add('post', 1, 'user_1')
        # 重复添加
        result = buffer.add('post', 1, 'user_1')

        assert result is False
        assert buffer._buffer['post'][1] == 1

    def test_different_users(self):
        """测试不同用户记录"""
        buffer = ViewsBuffer()
        buffer._buffer.clear()
        buffer._recorded.clear()

        # 不同用户
        buffer.add('post', 1, 'user_1')
        buffer.add('post', 1, 'user_2')
        buffer.add('post', 1, 'ip_127.0.0.1')

        assert buffer._buffer['post'][1] == 3

    def test_get_buffer_stats(self):
        """测试获取统计信息"""
        buffer = ViewsBuffer()
        buffer._buffer.clear()
        buffer._recorded.clear()

        buffer.add('post', 1, 'user_1')
        buffer.add('post', 2, 'user_2')
        buffer.add('topic', 1, 'user_3')

        stats = buffer.get_buffer_stats()

        assert stats['total_items'] == 3
        assert 'post' in stats['model_types']
        assert 'topic' in stats['model_types']


@pytest.mark.django_db
class TestViewsCounter:
    """浏览量计数器测试"""

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    @pytest.fixture
    def user(self):
        from apps.accounts.models import User
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def post(self, user):
        from apps.blog.models import Post, Category
        category = Category.objects.create(name='技术')
        post = Post.objects.create(
            title='测试文章',
            content='内容',
            author=user,
            category=category,
            status='published'
        )
        return post

    def test_increment_post(self, factory, post):
        """测试记录文章浏览量"""
        request = factory.get(f'/blog/post/{post.slug}/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        request.META = {'REMOTE_ADDR': '127.0.0.1'}

        # 清空缓冲区
        ViewsCounter._buffer._buffer.clear()
        ViewsCounter._buffer._recorded.clear()

        result = ViewsCounter.increment('post', post.id, request)

        assert result is True

    def test_increment_with_identifier(self):
        """测试使用自定义标识记录"""
        ViewsCounter._buffer._buffer.clear()
        ViewsCounter._buffer._recorded.clear()

        result = ViewsCounter.increment('post', 1, identifier='custom_id')

        assert result is True

    def test_increment_unsupported_model(self):
        """测试不支持的模型类型"""
        result = ViewsCounter.increment('invalid', 1, identifier='user_1')

        assert result is False

    def test_get_views(self, post):
        """测试获取浏览量"""
        views = ViewsCounter.get_views('post', post.id)

        assert isinstance(views, int)
        assert views >= 0

    def test_get_client_ip(self, factory):
        """测试获取客户端 IP"""
        request = factory.get('/')
        request.META = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_X_FORWARDED_FOR': '192.168.1.1, 10.0.0.1',
        }

        ip = ViewsCounter._get_client_ip(request)

        assert ip == '192.168.1.1'

    def test_sync_to_db(self, post):
        """测试同步到数据库"""
        # 添加一些浏览量
        ViewsCounter._buffer._buffer.clear()
        ViewsCounter._buffer.add('post', post.id, 'user_1')
        ViewsCounter._buffer.add('post', post.id, 'user_2')

        # 强制刷新到 Redis
        ViewsCounter._buffer.force_flush()

        # 同步到数据库
        result = ViewsCounter.sync_to_db('post')

        assert 'synced' in result
        assert 'errors' in result


class TestViewsCounterMiddleware:
    """中间件测试"""

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    def test_middleware_excluded_path(self, factory):
        """测试排除路径"""
        from apps.core.views_middleware import ViewsCounterMiddleware

        middleware = ViewsCounterMiddleware(lambda r: MagicMock())

        request = factory.get('/admin/')
        middleware(request)

        # 排除路径不应该记录浏览量
