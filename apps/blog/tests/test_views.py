"""
博客视图测试

测试覆盖:
- comment_create_view: 评论创建视图
- like_comment_view: 评论点赞视图
"""

import pytest
from django.test import Client
from django.urls import reverse
from apps.accounts.models import User
from apps.blog.models import Category, Post, Comment


@pytest.mark.django_db
class TestCommentCreateView:
    """评论创建视图测试"""

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
        self.comment_url = reverse('blog:comment_create', args=[self.post.slug])

    def test_guest_can_comment(self):
        """测试游客可以评论"""
        response = self.client.post(self.comment_url, {
            'content': '游客评论内容',
            'name': '游客',
            'email': 'guest@example.com'
        })
        # 应该重定向到文章详情页
        assert response.status_code == 302
        # 检查评论是否创建
        assert Comment.objects.filter(post=self.post).exists()
        comment = Comment.objects.get(post=self.post)
        assert comment.content == '游客评论内容'
        assert comment.name == '游客'
        assert comment.email == 'guest@example.com'
        assert comment.user is None
        assert comment.review_status == 'pending'

    def test_authenticated_user_can_comment(self):
        """测试登录用户可以评论"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.comment_url, {
            'content': '登录用户评论内容'
        })
        # 应该重定向到文章详情页
        assert response.status_code == 302
        # 检查评论是否创建
        assert Comment.objects.filter(post=self.post).exists()
        comment = Comment.objects.get(post=self.post)
        assert comment.content == '登录用户评论内容'
        assert comment.user == self.user
        assert comment.review_status == 'pending'

    def test_comment_without_content_fails(self):
        """测试没有内容的评论失败"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.comment_url, {})
        # 应该重定向回文章页(表单验证失败)
        assert response.status_code == 302

        # 验证错误信息通过 messages 传递
        # 跟随重定向检查 messages
        response = self.client.get(response.url)
        messages_list = list(response.context['messages'])
        assert len(messages_list) > 0
        # 检查是否有包含"至少需要"的错误消息
        error_found = any('至少需要' in str(m) for m in messages_list)
        assert error_found, f"未找到表单验证错误消息，实际消息: {[str(m) for m in messages_list]}"

        # 检查评论是否创建
        assert not Comment.objects.filter(post=self.post).exists()

    def test_comment_on_nonexistent_post_fails(self):
        """测试对不存在的文章评论失败"""
        url = reverse('blog:comment_create', args=['nonexistent-slug'])
        response = self.client.post(url, {
            'content': '评论内容'
        })
        # 应该返回404
        assert response.status_code == 404

    def test_get_request_not_allowed(self):
        """测试GET请求不被允许"""
        response = self.client.get(self.comment_url)
        # 应该重定向到文章详情页
        assert response.status_code == 302
        # 检查评论是否创建
        assert not Comment.objects.filter(post=self.post).exists()


@pytest.mark.django_db
class TestLikeCommentView:
    """评论点赞视图测试"""

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
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content="测试评论",
            review_status="approved"
        )
        self.like_url = reverse('blog:like_comment', args=[self.comment.id])

    def test_unauthenticated_user_cannot_like(self):
        """测试未登录用户不能点赞"""
        response = self.client.post(self.like_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_authenticated_user_can_like(self):
        """测试登录用户可以点赞"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.like_url)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['liked'] is True
        assert data['like_count'] == 1

    def test_authenticated_user_can_unlike(self):
        """测试登录用户可以取消点赞"""
        self.client.login(username='testuser', password='testpass123')
        # 先点赞
        self.client.post(self.like_url)
        # 再取消点赞
        response = self.client.post(self.like_url)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['liked'] is False
        assert data['like_count'] == 0

    def test_cannot_like_pending_comment(self):
        """测试不能对未审核评论点赞"""
        # 将评论状态改为pending
        self.comment.review_status = 'pending'
        self.comment.save()

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.like_url)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert '只能对已审核通过的评论点赞' in data['message']

    def test_get_request_not_allowed(self):
        """测试GET请求不被允许"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.like_url)
        # 应该返回405 Method Not Allowed
        assert response.status_code == 405


@pytest.mark.django_db
class TestRateLimiting:
    """限流测试"""

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
        self.comment_url = reverse('blog:comment_create', args=[self.post.slug])
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content="测试评论",
            review_status="approved"
        )
        self.like_url = reverse('blog:like_comment', args=[self.comment.id])

    def test_comment_rate_limit(self):
        """测试评论限流"""
        self.client.login(username='testuser', password='testpass123')

        # 发送10条评论(应该成功)
        for i in range(10):
            response = self.client.post(self.comment_url, {
                'content': f'评论内容 {i}'
            })
            assert response.status_code == 302

        # 第11条评论应该被限流
        response = self.client.post(self.comment_url, {
            'content': '第11条评论'
        })
        # 应该返回429 Too Many Requests
        assert response.status_code == 429

    def test_like_rate_limit(self):
        """测试点赞限流"""
        self.client.login(username='testuser', password='testpass123')

        # 发送30次点赞(应该成功)
        for i in range(30):
            response = self.client.post(self.like_url)
            assert response.status_code == 200

        # 第31次点赞应该被限流
        response = self.client.post(self.like_url)
        # 应该返回429 Too Many Requests
        assert response.status_code == 429

    def test_rate_limit_by_ip(self):
        """测试按IP地址限流"""
        # 使用不同用户但相同IP
        User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )

        # 第一个用户发送10条评论
        self.client.login(username='testuser', password='testpass123')
        for i in range(10):
            response = self.client.post(self.comment_url, {
                'content': f'用户1评论 {i}'
            })
            assert response.status_code == 302

        # 第二个用户尝试评论(相同IP)
        self.client.login(username='testuser2', password='testpass123')
        response = self.client.post(self.comment_url, {
            'content': '用户2评论'
        })
        # 应该被限流(相同IP)
        assert response.status_code == 429
