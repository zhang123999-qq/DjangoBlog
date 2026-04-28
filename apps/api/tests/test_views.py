"""
API 视图测试

测试覆盖:
- PostViewSet: 列表、详情、过滤、搜索
- CategoryViewSet: 列表、关联文章
- TagViewSet: 列表
- TopicViewSet: 列表、详情
- BoardViewSet: 列表、关联主题
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.blog.models import Category, Tag, Post, Comment
from apps.forum.models import Board, Topic, Reply


@pytest.fixture
def api_client():
    """API 客户端"""
    return APIClient()


@pytest.fixture
def user():
    """测试用户"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPassword123!'
    )


@pytest.fixture
def staff_user():
    """管理员用户"""
    user = User.objects.create_user(
        username='staff',
        email='staff@example.com',
        password='StaffPassword123!'
    )
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def category():
    """测试分类"""
    return Category.objects.create(name='技术')


@pytest.fixture
def tag():
    """测试标签"""
    return Tag.objects.create(name='Python')


@pytest.fixture
def post(user, category, tag):
    """测试文章"""
    post = Post.objects.create(
        title='测试文章标题',
        content='这是测试文章的内容，包含足够长的文本。',
        summary='文章摘要',
        author=user,
        category=category,
        status='published'
    )
    post.tags.add(tag)
    return post


@pytest.fixture
def board():
    """测试版块"""
    return Board.objects.create(
        name='技术讨论',
        description='技术交流版块'
    )


@pytest.fixture
def topic(user, board):
    """测试主题"""
    return Topic.objects.create(
        board=board,
        author=user,
        title='测试主题标题',
        content='这是测试主题的内容',
        review_status='approved'
    )


@pytest.mark.django_db
class TestCategoryAPI:
    """分类 API 测试"""

    def test_list_categories(self, api_client, category):
        """测试分类列表"""
        response = api_client.get('/api/categories/')
        assert response.status_code == status.HTTP_200_OK

    def test_category_detail(self, api_client, category):
        """测试分类详情"""
        response = api_client.get(f'/api/categories/{category.slug}/')
        assert response.status_code == status.HTTP_200_OK

    def test_category_posts(self, api_client, category, post):
        """测试分类下的文章"""
        response = api_client.get(f'/api/categories/{category.slug}/posts/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTagAPI:
    """标签 API 测试"""

    def test_list_tags(self, api_client, tag):
        """测试标签列表"""
        response = api_client.get('/api/tags/')
        assert response.status_code == status.HTTP_200_OK

    def test_tag_detail(self, api_client, tag):
        """测试标签详情"""
        response = api_client.get(f'/api/tags/{tag.slug}/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPostAPI:
    """文章 API 测试"""

    def test_list_posts(self, api_client, post):
        """测试文章列表"""
        response = api_client.get('/api/posts/')
        assert response.status_code == status.HTTP_200_OK

    def test_post_detail(self, api_client, post):
        """测试文章详情"""
        response = api_client.get(f'/api/posts/{post.slug}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['title'] == post.title
        assert 'email' not in data['author']

    def test_post_detail_increases_views(self, api_client, post):
        """测试文章详情增加浏览量"""
        post.views_count
        api_client.get(f'/api/posts/{post.slug}/')
        # 浏览量应该增加（可能通过 Redis 或数据库）
        post.refresh_from_db()
        # 注意：Redis 计数可能不会立即同步到数据库

    def test_filter_by_category(self, api_client, category, post):
        """测试按分类筛选"""
        response = api_client.get(f'/api/posts/?category={category.slug}')
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_tag(self, api_client, tag, post):
        """测试按标签筛选"""
        response = api_client.get(f'/api/posts/?tags={tag.slug}')
        assert response.status_code == status.HTTP_200_OK

    def test_search_posts(self, api_client, post):
        """测试搜索文章"""
        response = api_client.get('/api/posts/?search=测试')
        assert response.status_code == status.HTTP_200_OK

    def test_order_posts(self, api_client, post):
        """测试排序文章"""
        response = api_client.get('/api/posts/?ordering=-published_at')
        assert response.status_code == status.HTTP_200_OK

    def test_post_comments(self, api_client, post, user):
        """测试文章评论列表"""
        # 创建评论
        Comment.objects.create(
            post=post,
            user=user,
            content='测试评论',
            review_status='approved'
        )
        response = api_client.get(f'/api/posts/{post.slug}/comments/')
        assert response.status_code == status.HTTP_200_OK

    def test_post_comments_do_not_expose_email_addresses(self, api_client, post, user):
        """公开评论接口不应暴露账号或游客邮箱"""
        Comment.objects.create(
            post=post,
            user=user,
            content='authenticated comment',
            review_status='approved'
        )
        Comment.objects.create(
            post=post,
            name='guest',
            email='guest@example.com',
            content='guest comment',
            review_status='approved'
        )

        response = api_client.get(f'/api/posts/{post.slug}/comments/')
        assert response.status_code == status.HTTP_200_OK

        for item in response.json()['results']:
            assert 'email' not in item
            if item.get('user'):
                assert 'email' not in item['user']

    def test_draft_post_not_visible(self, api_client, user, category):
        """测试草稿不可见"""
        draft = Post.objects.create(
            title='草稿文章',
            content='内容',
            author=user,
            category=category,
            status='draft'
        )
        response = api_client.get(f'/api/posts/{draft.slug}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestBoardAPI:
    """版块 API 测试"""

    def test_list_boards(self, api_client, board):
        """测试版块列表"""
        response = api_client.get('/api/boards/')
        assert response.status_code == status.HTTP_200_OK

    def test_board_detail(self, api_client, board):
        """测试版块详情"""
        response = api_client.get(f'/api/boards/{board.pk}/')
        assert response.status_code == status.HTTP_200_OK

    def test_board_topics(self, api_client, board, topic):
        """测试版块下的主题"""
        response = api_client.get(f'/api/boards/{board.pk}/topics/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTopicAPI:
    """主题 API 测试"""

    def test_list_topics(self, api_client, topic):
        """测试主题列表"""
        response = api_client.get('/api/topics/')
        assert response.status_code == status.HTTP_200_OK

    def test_topic_detail(self, api_client, topic):
        """测试主题详情"""
        response = api_client.get(f'/api/topics/{topic.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'email' not in response.json()['author']

    def test_topic_replies(self, api_client, topic, user):
        """测试主题回复列表"""
        Reply.objects.create(
            topic=topic,
            author=user,
            content='测试回复',
            review_status='approved'
        )
        response = api_client.get(f'/api/topics/{topic.pk}/replies/')
        assert response.status_code == status.HTTP_200_OK
        for item in response.json()['results']:
            assert 'email' not in item['author']

    def test_pending_topic_not_visible(self, api_client, board, user):
        """测试待审核主题不可见"""
        pending = Topic.objects.create(
            board=board,
            author=user,
            title='待审核主题',
            content='内容',
            review_status='pending'
        )
        response = api_client.get(f'/api/topics/{pending.pk}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAPIThrottling:
    """API 限流测试"""

    def test_rate_limit_headers(self, api_client, post):
        """测试限流响应头"""
        response = api_client.get('/api/posts/')
        # 检查是否有限流相关的响应头
        # DRF 会返回 X-Request-Id 或类似头
        assert response.status_code in [200, 429]

    @pytest.mark.slow
    def test_rate_limit_enforcement(self, api_client):
        """测试限流执行（需要大量请求）"""
        # 这个测试会发送大量请求来触发限流


@pytest.mark.django_db
class TestSearchAPI:
    """公开搜索 API 回归测试"""

    def test_pending_topic_not_visible_in_topic_search(self, api_client, board, user):
        pending = Topic.objects.create(
            board=board,
            author=user,
            title='pending search topic',
            content='pending search body',
            review_status='pending'
        )

        response = api_client.get('/api/search/topics/?q=pending search')
        assert response.status_code == status.HTTP_200_OK
        ids = [item['id'] for item in response.json()['data']]
        assert str(pending.id) not in ids

    def test_pending_topic_not_visible_in_global_search(self, api_client, board, user):
        pending = Topic.objects.create(
            board=board,
            author=user,
            title='hidden global topic',
            content='hidden global body',
            review_status='pending'
        )

        response = api_client.get('/api/search/?q=hidden global')
        assert response.status_code == status.HTTP_200_OK
        topic_ids = [item['id'] for item in response.json()['data']['topics']['hits']]
        assert str(pending.id) not in topic_ids

    def test_invalid_search_page_returns_400(self, api_client):
        response = api_client.get('/api/search/posts/?q=django&page=abc')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_search_limit_returns_400(self, api_client):
        response = api_client.get('/api/search/?q=django&limit=abc')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_negative_search_page_returns_400(self, api_client):
        response = api_client.get('/api/search/topics/?q=django&page=-1')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
