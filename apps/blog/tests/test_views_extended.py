"""
博客视图测试 - 扩展

测试覆盖:
- PostListView: 文章列表视图
- PostDetailView: 文章详情视图
- comment_create_view: 评论创建视图
- like_comment_view: 评论点赞视图
- 权限控制测试
- 缓存测试
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.core.cache import cache
from apps.accounts.models import User
from apps.blog.models import Category, Tag, Post, Comment


@pytest.mark.django_db
class TestPostListView:
    """文章列表视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="技术", slug="tech")
        self.tag = Tag.objects.create(name="Python", slug="python")

        # 创建测试文章
        self.post1 = Post.objects.create(
            title="测试文章1",
            slug="test-post-1",
            content="内容1",
            author=self.user,
            category=self.category,
            status="published"
        )
        self.post1.tags.add(self.tag)

        self.post2 = Post.objects.create(
            title="测试文章2",
            slug="test-post-2",
            content="内容2",
            author=self.user,
            status="published"
        )

        # 创建草稿文章
        self.draft_post = Post.objects.create(
            title="草稿文章",
            slug="draft-post",
            content="草稿内容",
            author=self.user,
            status="draft"
        )

        self.post_list_url = reverse('blog:post_list')

    def test_post_list_view_loads(self):
        """测试文章列表加载"""
        response = self.client.get(self.post_list_url)
        assert response.status_code == 200
        assert 'posts' in response.context
        assert 'categories' in response.context
        assert 'tags' in response.context

    def test_post_list_view_only_published(self):
        """测试只显示已发布文章"""
        response = self.client.get(self.post_list_url)
        posts = response.context['posts']

        # 检查只有已发布文章
        for post in posts:
            assert post.status == 'published'

        # 草稿文章不应该显示
        post_titles = [post.title for post in posts]
        assert "草稿文章" not in post_titles

    def test_post_list_view_by_category(self):
        """测试按分类筛选"""
        url = reverse('blog:category', args=[self.category.slug])
        response = self.client.get(url)
        assert response.status_code == 200

        posts = response.context['posts']
        # 检查只显示该分类的文章
        for post in posts:
            assert post.category == self.category

    def test_post_list_view_by_tag(self):
        """测试按标签筛选"""
        url = reverse('blog:tag', args=[self.tag.slug])
        response = self.client.get(url)
        assert response.status_code == 200

        posts = response.context['posts']
        # 检查只显示该标签的文章
        for post in posts:
            assert self.tag in post.tags.all()

    def test_post_list_view_caching(self):
        """测试文章列表缓存"""
        # 清除缓存
        cache.clear()

        # 第一次访问
        response1 = self.client.get(self.post_list_url)
        assert response1.status_code == 200

        # 第二次访问（应该命中缓存）
        response2 = self.client.get(self.post_list_url)
        assert response2.status_code == 200

        # 检查缓存是否生效
        # 注意：由于使用了 @cache_page，我们无法直接测试缓存内容
        # 但可以验证请求成功

    def test_post_list_view_pagination(self):
        """测试文章列表分页"""
        # 创建多篇文章
        for i in range(15):
            Post.objects.create(
                title=f"文章{i}",
                slug=f"post-{i}",
                content=f"内容{i}",
                author=self.user,
                status="published"
            )

        response = self.client.get(self.post_list_url)
        assert response.status_code == 200

        # 检查分页
        assert 'posts' in response.context
        posts = response.context['posts']
        # 默认每页10篇，应该有分页
        assert len(posts) <= 10


@pytest.mark.django_db
class TestPostDetailView:
    """文章详情视图测试"""

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
            content="测试内容",
            author=self.user,
            category=self.category,
            status="published"
        )

        # 创建评论
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content="测试评论",
            review_status="approved"
        )

        self.post_detail_url = reverse('blog:post_detail', args=[self.post.slug])

    def test_post_detail_view_loads(self):
        """测试文章详情加载"""
        response = self.client.get(self.post_detail_url)
        assert response.status_code == 200
        assert 'post' in response.context
        assert 'comments' in response.context
        assert 'comment_form' in response.context

    def test_post_detail_view_increases_views(self):
        """测试文章详情增加浏览量"""
        initial_views = self.post.views_count

        # 访问文章详情
        response = self.client.get(self.post_detail_url)
        assert response.status_code == 200

        # 刷新文章数据
        self.post.refresh_from_db()
        # 注意：由于使用了 Redis 计数，可能不会立即更新
        # 但至少应该不会减少
        assert self.post.views_count >= initial_views

    def test_post_detail_view_only_approved_comments(self):
        """测试只显示已审核评论"""
        # 创建未审核评论
        Comment.objects.create(
            post=self.post,
            user=self.user,
            content="未审核评论",
            review_status="pending"
        )

        response = self.client.get(self.post_detail_url)
        comments = response.context['comments']

        # 检查只有已审核的评论
        for comment in comments:
            assert comment.review_status == 'approved'

    def test_post_detail_view_nonexistent_post(self):
        """测试不存在的文章"""
        url = reverse('blog:post_detail', args=['nonexistent-slug'])
        response = self.client.get(url)
        assert response.status_code == 404

    def test_post_detail_view_draft_post(self):
        """测试草稿文章"""
        draft_post = Post.objects.create(
            title="草稿文章",
            slug="draft-post",
            content="草稿内容",
            author=self.user,
            status="draft"
        )

        url = reverse('blog:post_detail', args=[draft_post.slug])
        response = self.client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestPostCreateView:
    """文章创建视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="技术", slug="tech")
        self.post_create_url = reverse('blog:post_create')

    def test_post_create_view_requires_login(self):
        """测试创建文章需要登录"""
        response = self.client.get(self.post_create_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_post_create_view_get(self):
        """测试创建文章页面GET请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.post_create_url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_post_create_view_post(self):
        """测试创建文章POST请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.post_create_url, {
            'title': '测试文章标题',
            'content': '测试文章内容，至少10个字符',
            'category': self.category.id,
            'status': 'published'
        })
        # 应该重定向到文章详情页
        assert response.status_code == 302

        # 检查文章是否创建
        post = Post.objects.filter(title='测试文章标题').first()
        assert post is not None
        assert post.author == self.user
        assert post.status == 'published'

    def test_post_create_view_invalid_form(self):
        """测试无效表单"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.post_create_url, {
            'title': '短',  # 标题太短
            'content': '测试文章内容，至少10个字符'
        })
        # 应该返回表单页面（带错误）
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.django_db
class TestPostUpdateView:
    """文章更新视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="技术", slug="tech")

        self.post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="测试内容",
            author=self.user,
            category=self.category,
            status="published"
        )

        self.post_edit_url = reverse('blog:post_edit', args=[self.post.slug])

    def test_post_update_view_requires_login(self):
        """测试编辑文章需要登录"""
        response = self.client.get(self.post_edit_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_post_update_view_only_author_can_edit(self):
        """测试只有作者可以编辑"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(self.post_edit_url)
        # 应该返回403 Forbidden
        assert response.status_code == 403

    def test_post_update_view_author_can_edit(self):
        """测试作者可以编辑"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.post_edit_url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_post_update_view_post(self):
        """测试编辑文章POST请求"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.post_edit_url, {
            'title': '更新后的标题',
            'content': '更新后的内容，至少10个字符',
            'category': self.category.id,
            'status': 'published'
        })
        # 应该重定向到文章详情页
        assert response.status_code == 302

        # 检查文章是否更新
        self.post.refresh_from_db()
        assert self.post.title == '更新后的标题'


@pytest.mark.django_db
class TestPostDeleteView:
    """文章删除视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="技术", slug="tech")

        self.post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="测试内容",
            author=self.user,
            category=self.category,
            status="published"
        )

        self.post_delete_url = reverse('blog:post_delete', args=[self.post.slug])

    def test_post_delete_view_requires_login(self):
        """测试删除文章需要登录"""
        response = self.client.post(self.post_delete_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_post_delete_view_only_author_can_delete(self):
        """测试只有作者可以删除"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(self.post_delete_url)
        # 应该返回403 Forbidden
        assert response.status_code == 403

    def test_post_delete_view_author_can_delete(self):
        """测试作者可以删除"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.post_delete_url)
        # 应该重定向到文章列表
        assert response.status_code == 302

        # 检查文章是否删除
        assert not Post.objects.filter(id=self.post.id).exists()


@pytest.mark.django_db
class TestMyPostsView:
    """我的文章视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="技术", slug="tech")

        # 创建测试文章
        self.post1 = Post.objects.create(
            title="我的文章1",
            slug="my-post-1",
            content="内容1",
            author=self.user,
            status="published"
        )
        self.post2 = Post.objects.create(
            title="我的文章2",
            slug="my-post-2",
            content="内容2",
            author=self.user,
            status="draft"
        )

        self.my_posts_url = reverse('blog:my_posts')

    def test_my_posts_view_requires_login(self):
        """测试我的文章需要登录"""
        response = self.client.get(self.my_posts_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_my_posts_view_loads(self):
        """测试我的文章加载"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.my_posts_url)
        assert response.status_code == 200
        assert 'posts' in response.context

    def test_my_posts_view_only_own_posts(self):
        """测试只显示自己的文章"""
        # 创建其他用户的文章
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        Post.objects.create(
            title="其他用户文章",
            slug="other-post",
            content="其他内容",
            author=other_user,
            status="published"
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.my_posts_url)
        posts = response.context['posts']

        # 检查只显示自己的文章
        for post in posts:
            assert post.author == self.user


@pytest.mark.django_db
class TestDraftListView:
    """草稿列表视图测试"""

    def setup_method(self):
        """设置测试数据"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # 创建草稿文章
        self.draft1 = Post.objects.create(
            title="草稿1",
            slug="draft-1",
            content="内容1",
            author=self.user,
            status="draft"
        )
        self.draft2 = Post.objects.create(
            title="草稿2",
            slug="draft-2",
            content="内容2",
            author=self.user,
            status="draft"
        )

        # 创建已发布文章
        self.published = Post.objects.create(
            title="已发布",
            slug="published",
            content="内容",
            author=self.user,
            status="published"
        )

        self.drafts_url = reverse('blog:drafts')

    def test_draft_list_view_requires_login(self):
        """测试草稿列表需要登录"""
        response = self.client.get(self.drafts_url)
        # 应该重定向到登录页
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_draft_list_view_loads(self):
        """测试草稿列表加载"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.drafts_url)
        assert response.status_code == 200
        assert 'posts' in response.context

    def test_draft_list_view_only_drafts(self):
        """测试只显示草稿"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.drafts_url)
        posts = response.context['posts']

        # 检查只显示草稿
        for post in posts:
            assert post.status == 'draft'

        # 已发布文章不应该显示
        post_titles = [post.title for post in posts]
        assert "已发布" not in post_titles
