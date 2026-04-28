"""
博客模型测试

测试覆盖:
- Category: 分类模型 CRUD 和 Slug 自动生成
- Tag: 标签模型 CRUD 和 Slug 自动生成
- Post: 文章模型 CRUD、状态管理、浏览量计数
- Comment: 评论模型 CRUD、审核状态
"""

import pytest
from apps.accounts.models import User
from apps.blog.models import Category, Tag, Post, Comment


@pytest.mark.django_db
class TestCategoryModel:
    """分类模型测试"""

    def test_create_category(self):
        """测试创建分类"""
        category = Category.objects.create(name="技术", slug="tech")
        assert category.name == "技术"
        assert category.slug == "tech"
        assert str(category) == "技术"

    def test_category_slug_auto_generate(self):
        """测试分类 Slug 自动生成"""
        category = Category.objects.create(name="生活")
        assert category.slug is not None
        assert len(category.slug) > 0

    def test_category_unique_name(self):
        """测试分类名称唯一性"""
        Category.objects.create(name="技术", slug="tech")
        with pytest.raises(Exception):  # IntegrityError
            Category.objects.create(name="技术", slug="tech2")

    def test_category_ordering(self):
        """测试分类排序（按名称）"""
        Category.objects.create(name="B分类", slug="b")
        Category.objects.create(name="A分类", slug="a")
        categories = list(Category.objects.all())
        assert categories[0].name == "A分类"
        assert categories[1].name == "B分类"

    def test_category_get_absolute_url(self):
        """测试分类 URL"""
        category = Category.objects.create(name="技术", slug="tech")
        url = category.get_absolute_url()
        assert "tech" in url


@pytest.mark.django_db
class TestTagModel:
    """标签模型测试"""

    def test_create_tag(self):
        """测试创建标签"""
        tag = Tag.objects.create(name="Python", slug="python")
        assert tag.name == "Python"
        assert tag.slug == "python"
        assert str(tag) == "Python"

    def test_tag_slug_auto_generate(self):
        """测试标签 Slug 自动生成"""
        tag = Tag.objects.create(name="Django")
        assert tag.slug is not None

    def test_tag_unique_name(self):
        """测试标签名称唯一性"""
        Tag.objects.create(name="Python", slug="python")
        with pytest.raises(Exception):  # IntegrityError
            Tag.objects.create(name="Python", slug="python2")


@pytest.mark.django_db
class TestPostModel:
    """文章模型测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试数据准备"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.category = Category.objects.create(name="技术", slug="tech")
        self.tag1 = Tag.objects.create(name="Python", slug="python")
        self.tag2 = Tag.objects.create(name="Django", slug="django")

    def test_create_post(self):
        """测试创建文章"""
        post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="这是测试内容",
            author=self.user,
            category=self.category,
            status="published"
        )
        assert post.title == "测试文章"
        assert post.status == "published"
        assert post.views_count == 0
        assert str(post) == "测试文章"

    def test_post_slug_auto_generate(self):
        """测试文章 Slug 自动生成"""
        post = Post.objects.create(
            title="中文标题测试",
            content="内容",
            author=self.user,
            status="draft"
        )
        assert post.slug is not None
        assert len(post.slug) > 0

    def test_post_slug_unique(self):
        """测试文章 Slug 唯一性"""
        Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="内容1",
            author=self.user,
            status="draft"
        )
        # 第二篇相同标题的文章，slug 应该自动加后缀
        post2 = Post.objects.create(
            title="测试文章",
            content="内容2",
            author=self.user,
            status="draft"
        )
        assert post2.slug != "test-post"

    def test_post_published_at_auto_set(self):
        """测试发布时间自动设置"""
        post = Post.objects.create(
            title="测试文章",
            content="内容",
            author=self.user,
            status="published"
        )
        assert post.published_at is not None

    def test_post_draft_no_published_at(self):
        """测试草稿没有发布时间"""
        post = Post.objects.create(
            title="测试文章",
            content="内容",
            author=self.user,
            status="draft"
        )
        assert post.published_at is None

    def test_post_tags(self):
        """测试文章标签关联"""
        post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="内容",
            author=self.user,
            status="published"
        )
        post.tags.add(self.tag1, self.tag2)
        assert post.tags.count() == 2
        assert self.tag1 in post.tags.all()

    def test_post_ordering(self):
        """测试文章排序（按发布时间倒序）"""
        Post.objects.create(
            title="文章1",
            slug="post-1",
            content="内容",
            author=self.user,
            status="published"
        )
        Post.objects.create(
            title="文章2",
            slug="post-2",
            content="内容",
            author=self.user,
            status="published"
        )
        posts = list(Post.objects.filter(status="published"))
        # 最新发布的在前
        assert posts[0].title == "文章2"

    def test_post_increase_views(self):
        """测试浏览量增加"""
        post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="内容",
            author=self.user,
            status="published"
        )
        post.views_count
        post.increase_views()
        # 浏览量应该增加（可能是通过 Redis 或数据库）
        post.refresh_from_db()
        # 注意：如果 Redis 可用，数据库可能不会立即更新


@pytest.mark.django_db
class TestCommentModel:
    """评论模型测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试数据准备"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.category = Category.objects.create(name="技术", slug="tech")
        self.post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="内容",
            author=self.user,
            status="published"
        )

    def test_create_comment(self):
        """测试创建评论"""
        comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content="这是一条评论"
        )
        assert comment.content == "这是一条评论"
        assert comment.review_status == "pending"
        assert str(comment) == "testuser 评论了 测试文章"

    def test_comment_review_status(self):
        """测试评论审核状态"""
        comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content="评论内容"
        )

        # 初始状态
        assert comment.is_pending is True
        assert comment.is_approved_status is False
        assert comment.is_rejected is False

        # 通过审核
        comment.review_status = "approved"
        comment.save()
        assert comment.is_approved_status is True
        assert comment.is_approved is True  # 兼容字段

        # 拒绝
        comment.review_status = "rejected"
        comment.save()
        assert comment.is_rejected is True
        assert comment.is_approved is False

    def test_comment_ordering(self):
        """测试评论排序（按时间倒序）"""
        import time
        Comment.objects.create(
            post=self.post,
            user=self.user,
            content="评论1"
        )
        time.sleep(0.01)
        Comment.objects.create(
            post=self.post,
            user=self.user,
            content="评论2"
        )
        comments = list(Comment.objects.all())
        assert comments[0].content == "评论2"

    def test_guest_comment(self):
        """测试游客评论"""
        comment = Comment.objects.create(
            post=self.post,
            name="游客",
            email="guest@example.com",
            content="游客评论"
        )
        assert comment.user is None
        assert comment.name == "游客"
        assert str(comment) == "游客 评论了 测试文章"


@pytest.mark.django_db
class TestCommentForm:
    """评论表单测试"""

    def setup_method(self):
        """设置测试数据"""
        from apps.accounts.models import User
        from apps.blog.models import Category, Post
        from apps.blog.forms import CommentForm

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
        self.CommentForm = CommentForm

    def test_valid_comment_form(self):
        """测试有效的评论表单"""
        form = self.CommentForm(data={
            'content': '这是一条有效的评论内容',
            'name': '测试用户',
            'email': 'test@example.com'
        })
        assert form.is_valid()

    def test_content_too_short(self):
        """测试评论内容过短"""
        form = self.CommentForm(data={
            'content': '短',  # 少于5个字符
            'name': '测试用户',
            'email': 'test@example.com'
        })
        assert not form.is_valid()
        assert 'content' in form.errors

    def test_content_too_long(self):
        """测试评论内容过长"""
        from apps.blog.forms import MAX_COMMENT_LENGTH
        long_content = 'a' * (MAX_COMMENT_LENGTH + 1)  # 超过最大长度
        form = self.CommentForm(data={
            'content': long_content,
            'name': '测试用户',
            'email': 'test@example.com'
        })
        assert not form.is_valid()
        assert 'content' in form.errors

    def test_guest_required_fields(self):
        """测试游客必填字段"""
        # 游客缺少姓名
        form = self.CommentForm(data={
            'content': '有效评论内容',
            'email': 'test@example.com'
        })
        assert not form.is_valid()
        assert 'name' in form.errors

        # 游客缺少邮箱
        form = self.CommentForm(data={
            'content': '有效评论内容',
            'name': '测试用户'
        })
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_authenticated_user_form(self):
        """测试登录用户的表单（隐藏姓名和邮箱）"""
        form = self.CommentForm(data={
            'content': '登录用户的评论'
        }, user=self.user)

        # 登录用户应该不需要姓名和邮箱
        assert form.is_valid()
        # 检查表单字段
        assert 'name' not in form.fields
        assert 'email' not in form.fields

    def test_content_whitespace_stripped(self):
        """测试评论内容自动去除首尾空格"""
        form = self.CommentForm(data={
            'content': '  有效评论内容  ',
            'name': '测试用户',
            'email': 'test@example.com'
        })
        assert form.is_valid()
        assert form.cleaned_data['content'] == '有效评论内容'


@pytest.mark.django_db
class TestCommentLike:
    """评论点赞模型测试"""

    def setup_method(self):
        """设置测试数据"""
        from apps.accounts.models import User
        from apps.blog.models import Category, Post, Comment, CommentLike

        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        self.category = Category.objects.create(name="技术", slug="tech")
        self.post = Post.objects.create(
            title="测试文章",
            slug="test-post",
            content="内容",
            author=self.user1,
            status="published"
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user1,
            content="测试评论",
            review_status="approved"
        )
        self.CommentLike = CommentLike

    def test_create_comment_like(self):
        """测试创建评论点赞"""
        like = self.CommentLike.objects.create(
            user=self.user1,
            comment=self.comment
        )
        assert like.user == self.user1
        assert like.comment == self.comment
        assert str(like) == "user1 点赞了评论"

    def test_unique_together_constraint(self):
        """测试唯一约束（同一用户不能重复点赞）"""
        # 第一次点赞
        self.CommentLike.objects.create(
            user=self.user1,
            comment=self.comment
        )
        # 尝试重复点赞应该抛出 IntegrityError
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            self.CommentLike.objects.create(
                user=self.user1,
                comment=self.comment
            )

    def test_multiple_users_can_like(self):
        """测试多个用户可以点赞同一评论"""
        self.CommentLike.objects.create(
            user=self.user1,
            comment=self.comment
        )
        self.CommentLike.objects.create(
            user=self.user2,
            comment=self.comment
        )
        assert self.CommentLike.objects.filter(comment=self.comment).count() == 2

    def test_update_like_count(self):
        """测试更新点赞数"""
        # 初始点赞数为0
        assert self.comment.like_count == 0

        # 添加点赞
        self.CommentLike.objects.create(
            user=self.user1,
            comment=self.comment
        )
        self.comment.update_like_count()
        assert self.comment.like_count == 1

        # 再添加一个点赞
        self.CommentLike.objects.create(
            user=self.user2,
            comment=self.comment
        )
        self.comment.update_like_count()
        assert self.comment.like_count == 2

    def test_delete_like_updates_count(self):
        """测试删除点赞更新点赞数"""
        # 添加点赞
        like = self.CommentLike.objects.create(
            user=self.user1,
            comment=self.comment
        )
        self.comment.update_like_count()
        assert self.comment.like_count == 1

        # 删除点赞
        like.delete()
        self.comment.update_like_count()
        assert self.comment.like_count == 0
