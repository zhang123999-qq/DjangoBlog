"""
论坛视图测试

测试覆盖:
- BoardListView: 版块列表视图
- TopicListView: 主题列表视图
- TopicDetailView: 主题详情视图
- topic_create_view: 创建主题视图
- reply_create_view: 回复视图
- like_reply_view: 点赞视图
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.core.cache import cache
from apps.accounts.models import User
from apps.forum.models import Board, Topic, Reply


@pytest.mark.django_db
class TestBoardListView:
    """版块列表视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.board = Board.objects.create(
            name="技术讨论",
            slug="tech",
            description="技术讨论版块"
        )
        self.board_list_url = reverse('forum:board_list')

    def test_board_list_view_loads(self):
        """测试版块列表加载"""
        response = self.client.get(self.board_list_url)
        assert response.status_code == 200
        assert 'boards' in response.context

    def test_board_list_view_caching(self):
        """测试版块列表缓存"""
        # 第一次访问
        response1 = self.client.get(self.board_list_url)
        assert response1.status_code == 200

        # 第二次访问（应该命中缓存）
        response2 = self.client.get(self.board_list_url)
        assert response2.status_code == 200

        # 清除缓存后再次访问
        cache.clear()
        response3 = self.client.get(self.board_list_url)
        assert response3.status_code == 200

    def test_board_list_view_context(self):
        """测试版块列表上下文"""
        response = self.client.get(self.board_list_url)
        assert response.status_code == 200

        # 检查版块数据
        boards = response.context['boards']
        assert len(boards) >= 1
        assert any(board.name == "技术讨论" for board in boards)


@pytest.mark.django_db
class TestTopicListView:
    """主题列表视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.board = Board.objects.create(
            name="技术讨论",
            slug="tech",
            description="技术讨论版块"
        )
        self.topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="测试主题",
            content="测试内容",
            review_status="approved"
        )
        self.topic_list_url = reverse('forum:topic_list', args=[self.board.slug])

    def test_topic_list_view_loads(self):
        """测试主题列表加载"""
        response = self.client.get(self.topic_list_url)
        assert response.status_code == 200
        assert 'topics' in response.context
        assert 'board' in response.context

    def test_topic_list_view_caching(self):
        """测试主题列表缓存"""
        # 第一次访问
        response1 = self.client.get(self.topic_list_url)
        assert response1.status_code == 200

        # 第二次访问（应该命中缓存）
        response2 = self.client.get(self.topic_list_url)
        assert response2.status_code == 200

        # 清除缓存后再次访问
        cache.clear()
        response3 = self.client.get(self.topic_list_url)
        assert response3.status_code == 200

    def test_topic_list_view_only_approved(self):
        """测试主题列表只显示已审核主题"""
        # 创建未审核主题
        Topic.objects.create(
            board=self.board,
            author=self.user,
            title="未审核主题",
            content="未审核内容",
            review_status="pending"
        )

        response = self.client.get(self.topic_list_url)
        assert response.status_code == 200

        # 检查只有已审核的主题
        topics = response.context['topics']
        for topic in topics:
            assert topic.review_status == 'approved'

    def test_topic_list_view_nonexistent_board(self):
        """测试不存在的版块"""
        url = reverse('forum:topic_list', args=['nonexistent-slug'])
        response = self.client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestTopicDetailView:
    """主题详情视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.board = Board.objects.create(
            name="技术讨论",
            slug="tech",
            description="技术讨论版块"
        )
        self.topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="测试主题",
            content="测试内容",
            review_status="approved"
        )
        self.topic_detail_url = reverse('forum:topic_detail', args=[self.board.slug, self.topic.id])

    def test_topic_detail_view_loads(self):
        """测试主题详情加载"""
        response = self.client.get(self.topic_detail_url)
        assert response.status_code == 200
        assert 'topic' in response.context
        assert 'replies' in response.context
        assert 'reply_form' in response.context

    def test_topic_detail_view_increases_views(self):
        """测试主题详情增加浏览量"""
        initial_views = self.topic.views_count

        # 访问主题详情
        response = self.client.get(self.topic_detail_url)
        assert response.status_code == 200

        # 刷新主题数据
        self.topic.refresh_from_db()
        assert self.topic.views_count == initial_views + 1

    def test_topic_detail_view_only_approved_replies(self):
        """测试主题详情只显示已审核回复"""
        # 创建未审核回复
        Reply.objects.create(
            topic=self.topic,
            author=self.user,
            content="未审核回复",
            review_status="pending"
        )

        # 创建已审核回复
        Reply.objects.create(
            topic=self.topic,
            author=self.user,
            content="已审核回复",
            review_status="approved"
        )

        response = self.client.get(self.topic_detail_url)
        assert response.status_code == 200

        # 检查只有已审核的回复
        replies = response.context['replies']
        for reply in replies:
            assert reply.review_status == 'approved'

    def test_topic_detail_view_nonexistent_topic(self):
        """测试不存在的主题"""
        url = reverse('forum:topic_detail', args=[self.board.slug, 9999])
        response = self.client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestTopicCreateView:
    """创建主题视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.board = Board.objects.create(
            name="技术讨论",
            slug="tech",
            description="技术讨论版块"
        )
        self.topic_create_url = reverse('forum:topic_create', args=[self.board.slug])

    def test_topic_create_view_get(self):
        """测试创建主题页面GET请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.topic_create_url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_topic_create_view_post(self):
        """测试创建主题POST请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.topic_create_url, {
            'title': '测试主题标题',
            'content': '测试主题内容，至少10个字符'
        })
        # 应该重定向到版块列表
        assert response.status_code == 302

        # 检查主题是否创建
        topic = Topic.objects.filter(title='测试主题标题').first()
        assert topic is not None
        assert topic.author == self.user
        assert topic.board == self.board
        assert topic.review_status == 'pending'

    def test_topic_create_view_unauthenticated(self):
        """测试未登录用户创建主题"""
        response = self.client.post(self.topic_create_url, {
            'title': '测试主题标题',
            'content': '测试主题内容，至少10个字符'
        })
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_topic_create_view_invalid_form(self):
        """测试无效表单"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.topic_create_url, {
            'title': '短',  # 标题太短
            'content': '测试主题内容，至少10个字符'
        })
        # 应该返回表单页面（带错误）
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_topic_create_view_nonexistent_board(self):
        """测试不存在的版块"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('forum:topic_create', args=['nonexistent-slug'])
        response = self.client.post(url, {
            'title': '测试主题标题',
            'content': '测试主题内容，至少10个字符'
        })
        assert response.status_code == 404


@pytest.mark.django_db
class TestReplyCreateView:
    """回复视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.board = Board.objects.create(
            name="技术讨论",
            slug="tech",
            description="技术讨论版块"
        )
        self.topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="测试主题",
            content="测试内容",
            review_status="approved"
        )
        self.reply_create_url = reverse('forum:reply_create', args=[self.board.slug, self.topic.id])

    def test_reply_create_view_post(self):
        """测试回复POST请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.reply_create_url, {
            'content': '测试回复内容，至少5个字符'
        })
        # 应该重定向到主题详情
        assert response.status_code == 302

        # 检查回复是否创建
        reply = Reply.objects.filter(topic=self.topic, content='测试回复内容，至少5个字符').first()
        assert reply is not None
        assert reply.author == self.user
        assert reply.review_status == 'pending'

    def test_reply_create_view_unauthenticated(self):
        """测试未登录用户回复"""
        response = self.client.post(self.reply_create_url, {
            'content': '测试回复内容，至少5个字符'
        })
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_reply_create_view_locked_topic(self):
        """测试锁定主题无法回复"""
        # 锁定主题
        self.topic.is_locked = True
        self.topic.save()

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.reply_create_url, {
            'content': '测试回复内容，至少5个字符'
        })
        # 应该返回403 Forbidden
        assert response.status_code == 403

    def test_reply_create_view_invalid_form(self):
        """测试无效回复表单"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.reply_create_url, {
            'content': '短'  # 回复太短
        })
        # 应该重定向回主题详情（表单验证失败）
        assert response.status_code == 302

        # 验证错误信息通过 messages 传递
        # 跟随重定向检查 messages
        response = self.client.get(response.url)
        messages_list = list(response.context['messages'])
        assert len(messages_list) > 0
        # 检查是否有包含"至少需要"的错误消息
        error_found = any('至少需要' in str(m) for m in messages_list)
        assert error_found, f"未找到表单验证错误消息，实际消息: {[str(m) for m in messages_list]}"

    def test_reply_create_view_nonexistent_topic(self):
        """测试不存在的主题"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('forum:reply_create', args=[self.board.slug, 9999])
        response = self.client.post(url, {
            'content': '测试回复内容，至少5个字符'
        })
        assert response.status_code == 404


@pytest.mark.django_db
class TestLikeReplyView:
    """点赞回复视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.board = Board.objects.create(
            name="技术讨论",
            slug="tech",
            description="技术讨论版块"
        )
        self.topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="测试主题",
            content="测试内容",
            review_status="approved"
        )
        self.reply = Reply.objects.create(
            topic=self.topic,
            author=self.user,
            content="测试回复",
            review_status="approved"
        )
        self.like_reply_url = reverse('forum:like_reply', args=[self.reply.id])

    def test_like_reply_view_post(self):
        """测试点赞回复"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.like_reply_url)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['liked'] is True
        assert data['like_count'] == 1

    def test_like_reply_view_unauthenticated(self):
        """测试未登录用户点赞"""
        response = self.client.post(self.like_reply_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_like_reply_view_unapproved_reply(self):
        """测试未审核回复无法点赞"""
        # 将回复状态改为pending
        self.reply.review_status = 'pending'
        self.reply.save()

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.like_reply_url)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert '只能对已审核通过的回复点赞' in data['message']

    def test_like_reply_view_toggle(self):
        """测试点赞切换（取消点赞）"""
        self.client.login(username='testuser', password='testpass123')

        # 第一次点赞
        response1 = self.client.post(self.like_reply_url)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1['liked'] is True

        # 第二次点赞（应该取消点赞）
        response2 = self.client.post(self.like_reply_url)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2['liked'] is False
        assert data2['like_count'] == 0

    def test_like_reply_view_nonexistent_reply(self):
        """测试不存在的回复"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('forum:like_reply', args=[9999])
        response = self.client.post(url)
        assert response.status_code == 404

    def test_like_reply_view_get_not_allowed(self):
        """GET requests must not mutate reply likes."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.like_reply_url)
        assert response.status_code == 405


@pytest.mark.django_db
class TestPermissionControl:
    """权限控制测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        self.board = Board.objects.create(
            name="技术讨论",
            slug="tech",
            description="技术讨论版块"
        )
        self.topic = Topic.objects.create(
            board=self.board,
            author=self.user1,
            title="测试主题",
            content="测试内容",
            review_status="approved"
        )
        self.reply = Reply.objects.create(
            topic=self.topic,
            author=self.user1,
            content="测试回复",
            review_status="approved"
        )

    def test_anonymous_cannot_create_topic(self):
        """测试匿名用户不能创建主题"""
        url = reverse('forum:topic_create', args=[self.board.slug])
        response = self.client.post(url, {
            'title': '测试主题标题',
            'content': '测试主题内容，至少10个字符'
        })
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_anonymous_cannot_reply(self):
        """测试匿名用户不能回复"""
        url = reverse('forum:reply_create', args=[self.board.slug, self.topic.id])
        response = self.client.post(url, {
            'content': '测试回复内容，至少5个字符'
        })
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_anonymous_cannot_like(self):
        """测试匿名用户不能点赞"""
        url = reverse('forum:like_reply', args=[self.reply.id])
        response = self.client.post(url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_any_user_can_view_boards(self):
        """测试任何用户都可以查看版块列表"""
        url = reverse('forum:board_list')
        response = self.client.get(url)
        assert response.status_code == 200

    def test_any_user_can_view_topics(self):
        """测试任何用户都可以查看主题列表"""
        url = reverse('forum:topic_list', args=[self.board.slug])
        response = self.client.get(url)
        assert response.status_code == 200

    def test_any_user_can_view_topic_detail(self):
        """测试任何用户都可以查看主题详情"""
        url = reverse('forum:topic_detail', args=[self.board.slug, self.topic.id])
        response = self.client.get(url)
        assert response.status_code == 200

    def test_locked_topic_cannot_reply(self):
        """测试锁定主题无法回复"""
        # 锁定主题
        self.topic.is_locked = True
        self.topic.save()

        self.client.login(username='user2', password='testpass123')
        url = reverse('forum:reply_create', args=[self.board.slug, self.topic.id])
        response = self.client.post(url, {
            'content': '测试回复内容，至少5个字符'
        })
        # 应该返回403 Forbidden
        assert response.status_code == 403

    def test_unapproved_reply_cannot_like(self):
        """测试未审核回复无法点赞"""
        # 创建未审核回复
        unapproved_reply = Reply.objects.create(
            topic=self.topic,
            author=self.user1,
            content="未审核回复",
            review_status="pending"
        )

        self.client.login(username='user2', password='testpass123')
        url = reverse('forum:like_reply', args=[unapproved_reply.id])
        response = self.client.post(url)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert '只能对已审核通过的回复点赞' in data['message']

    def test_only_approved_topics_visible(self):
        """测试只有已审核主题可见"""
        # 创建未审核主题
        Topic.objects.create(
            board=self.board,
            author=self.user1,
            title="未审核主题",
            content="未审核内容",
            review_status="pending"
        )

        url = reverse('forum:topic_list', args=[self.board.slug])
        response = self.client.get(url)
        assert response.status_code == 200

        # 棡查只有已审核的主题
        topics = response.context['topics']
        for topic in topics:
            assert topic.review_status == 'approved'

    def test_only_approved_replies_visible(self):
        """测试只有已审核回复可见"""
        # 创建未审核回复
        Reply.objects.create(
            topic=self.topic,
            author=self.user1,
            content="未审核回复",
            review_status="pending"
        )

        url = reverse('forum:topic_detail', args=[self.board.slug, self.topic.id])
        response = self.client.get(url)
        assert response.status_code == 200

        # 棡查只有已审核的回复
        replies = response.context['replies']
        for reply in replies:
            assert reply.review_status == 'approved'
