"""
Forum 模型测试

测试覆盖:
- Board: 创建、slug自动生成、计数更新
- Topic: 创建、审核状态、浏览量、排序
- Reply: 创建、审核状态、回复统计
- ReplyLike: 点赞、唯一约束
"""

import pytest

from apps.accounts.models import User
from apps.forum.models import Board, Topic, Reply, ReplyLike


# ============================================================
# Board 测试
# ============================================================

@pytest.mark.django_db
class TestBoardModel:

    def test_create_board(self):
        """测试创建版块"""
        board = Board.objects.create(name="技术讨论", description="技术交流区")
        assert board.name == "技术讨论"
        assert board.slug is not None
        assert board.topic_count == 0
        assert board.reply_count == 0

    def test_board_slug_auto_generate(self):
        """测试 slug 自动生成"""
        board = Board.objects.create(name="生活水区")
        assert board.slug
        assert len(board.slug) > 0
        assert board.slug != ""

    def test_board_slug_unique(self):
        """测试 slug 唯一性"""
        Board.objects.create(name="技术")
        # 同名版块应该因为 slug 冲突而失败
        with pytest.raises(Exception):
            Board.objects.create(name="技术")

    def test_board_str(self):
        """测试字符串表示"""
        board = Board.objects.create(name="灌水专区")
        assert str(board) == "灌水专区"

    def test_board_ordering(self):
        """测试按名称排序"""
        Board.objects.create(name="ZZZ")
        Board.objects.create(name="AAA")
        boards = list(Board.objects.all())
        assert boards[0].name == "AAA"
        assert boards[1].name == "ZZZ"

    def test_board_get_absolute_url(self):
        """测试获取绝对URL"""
        board = Board.objects.create(name="技术", slug="tech")
        url = board.get_absolute_url()
        assert "tech" in url

    def test_board_update_counts_empty(self):
        """测试空版块的计数更新"""
        board = Board.objects.create(name="测试版块")
        board.update_counts()
        assert board.topic_count == 0
        assert board.reply_count == 0


# ============================================================
# Topic 测试
# ============================================================

@pytest.mark.django_db
class TestTopicModel:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            username="tester", email="test@forum.com", password="pass123"
        )
        self.board = Board.objects.create(name="技术", slug="tech")

    def test_create_topic(self):
        """测试创建主题"""
        topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="第一个帖子",
            content="这是内容",
            review_status="approved",
        )
        assert topic.title == "第一个帖子"
        assert topic.reply_count == 0
        assert topic.views_count == 0
        assert topic.is_pinned is False
        assert topic.is_approved

    def test_topic_default_status_pending(self):
        """测试主题默认待审核"""
        topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="待审核",
            content="内容",
        )
        assert topic.is_pending
        assert not topic.is_approved

    def test_topic_str(self):
        """测试字符串表示"""
        topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="测试标题",
            content="内容",
        )
        assert str(topic) == "测试标题"

    def test_topic_get_absolute_url(self):
        """测试URL生成"""
        topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="URL测试",
            content="内容",
            review_status="approved",
        )
        url = topic.get_absolute_url()
        assert str(topic.id) in url

    def test_topic_increase_views(self):
        """测试浏览量递增"""
        topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="热门帖",
            content="内容",
            review_status="approved",
        )
        initial = topic.views_count
        topic.increase_views()
        assert topic.views_count == initial + 1

    def test_topic_review_status_properties(self):
        """测试审核状态属性"""
        topic = Topic.objects.create(
            board=self.board, author=self.user,
            title="状态测试", content="内容",
            review_status="pending",
        )
        assert topic.is_pending
        assert not topic.is_approved
        assert not topic.is_rejected

        topic.review_status = "approved"
        topic.save()
        assert topic.is_approved
        assert not topic.is_pending

        topic.review_status = "rejected"
        topic.save()
        assert topic.is_rejected

    def test_topic_pinned_ordering(self):
        """测试置顶帖排在前面"""
        Topic.objects.create(
            board=self.board, author=self.user,
            title="普通帖", content="内容",
            review_status="approved",
        )
        Topic.objects.create(
            board=self.board, author=self.user,
            title="置顶帖", content="内容",
            review_status="approved",
            is_pinned=True,
        )
        topics = list(Topic.objects.filter(review_status="approved"))
        assert topics[0].is_pinned

    def test_topic_indexes_exist(self):
        """确认 Topic 模型有数据库索引定义"""
        assert len(Topic._meta.indexes) >= 3


# ============================================================
# Reply 测试
# ============================================================

@pytest.mark.django_db
class TestReplyModel:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            username="replyer", email="reply@test.com", password="pass123"
        )
        self.board = Board.objects.create(name="技术", slug="tech2")
        self.topic = Topic.objects.create(
            board=self.board, author=self.user,
            title="主题帖", content="主题内容",
            review_status="approved",
        )

    def test_create_reply(self):
        """测试创建回复"""
        reply = Reply.objects.create(
            topic=self.topic,
            author=self.user,
            content="这是回复内容",
        )
        assert reply.content == "这是回复内容"
        assert reply.like_count == 0
        assert reply.is_pending
        assert not reply.is_deleted

    def test_reply_str(self):
        """测试字符串表示"""
        reply = Reply.objects.create(
            topic=self.topic, author=self.user,
            content="回复内容",
        )
        assert "replyer" in str(reply)

    def test_reply_review_status(self):
        """测试回复审核状态"""
        reply = Reply.objects.create(
            topic=self.topic, author=self.user, content="内容",
        )
        assert reply.is_pending

        reply.review_status = "approved"
        reply.save()
        assert reply.is_approved

        reply.review_status = "rejected"
        reply.save()
        assert reply.is_rejected

    def test_topic_update_reply_count(self):
        """测试主题更新回复数"""
        Reply.objects.create(
            topic=self.topic, author=self.user,
            content="回复1", review_status="approved",
        )
        Reply.objects.create(
            topic=self.topic, author=self.user,
            content="回复2", review_status="approved",
        )
        self.topic.update_reply_count()
        assert self.topic.reply_count == 2

    def test_reply_ordering(self):
        """测试回复按时间正序"""
        Reply.objects.create(
            topic=self.topic, author=self.user, content="第一条",
            review_status="approved",
        )
        Reply.objects.create(
            topic=self.topic, author=self.user, content="第二条",
            review_status="approved",
        )
        replies = list(Reply.objects.filter(topic=self.topic))
        assert replies[0].content == "第一条"
        assert replies[1].content == "第二条"


# ============================================================
# ReplyLike 测试
# ============================================================

@pytest.mark.django_db
class TestReplyLikeModel:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            username="liker", email="like@test.com", password="pass123"
        )
        self.author = User.objects.create_user(
            username="poster", email="poster@test.com", password="pass123"
        )
        self.board = Board.objects.create(name="区", slug="zone")
        self.topic = Topic.objects.create(
            board=self.board, author=self.author,
            title="帖", content="内容", review_status="approved",
        )
        self.reply = Reply.objects.create(
            topic=self.topic, author=self.author,
            content="回复", review_status="approved",
        )

    def test_create_like(self):
        """测试创建点赞"""
        like = ReplyLike.objects.create(user=self.user, reply=self.reply)
        assert like.user == self.user
        assert like.reply == self.reply

    def testlike_unique_constraint(self):
        """测试同一用户不能重复点赞同一回复"""
        ReplyLike.objects.create(user=self.user, reply=self.reply)
        with pytest.raises(Exception):  # IntegrityError
            ReplyLike.objects.create(user=self.user, reply=self.reply)

    def test_different_users_can_like(self):
        """测试不同用户可以点赞同一回复"""
        user2 = User.objects.create_user(username="liker2", email="l2@test.com", password="p")
        ReplyLike.objects.create(user=self.user, reply=self.reply)
        like2 = ReplyLike.objects.create(user=user2, reply=self.reply)
        assert like2 is not None

    def test_update_like_count(self):
        """测试更新点赞数"""
        ReplyLike.objects.create(user=self.user, reply=self.reply)
        user2 = User.objects.create_user(username="l2", email="l2@t.com", password="p")
        ReplyLike.objects.create(user=user2, reply=self.reply)
        self.reply.update_like_count()
        assert self.reply.like_count == 2


# ============================================================
# 表单验证测试
# ============================================================

@pytest.mark.django_db
class TestTopicForm:
    """主题表单测试"""

    def setup_method(self):
        """设置测试数据"""
        from apps.forum.forms import TopicForm
        self.TopicForm = TopicForm

    def test_valid_topic_form(self):
        """测试有效的主题表单"""
        form = self.TopicForm(data={
            'title': '这是一个有效的主题标题',
            'content': '这是一个有效的主题内容，至少10个字符'
        })
        assert form.is_valid()

    def test_title_too_short(self):
        """测试标题过短"""
        form = self.TopicForm(data={
            'title': '短',  # 少于5个字符
            'content': '这是一个有效的主题内容，至少10个字符'
        })
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_title_too_long(self):
        """测试标题过长"""
        long_title = 'a' * 201  # 超过200字符
        form = self.TopicForm(data={
            'title': long_title,
            'content': '这是一个有效的主题内容，至少10个字符'
        })
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_content_too_short(self):
        """测试内容过短"""
        form = self.TopicForm(data={
            'title': '这是一个有效的主题标题',
            'content': '短'  # 少于10个字符
        })
        assert not form.is_valid()
        assert 'content' in form.errors

    def test_content_too_long(self):
        """测试内容过长"""
        long_content = 'a' * 10001  # 超过10000字符
        form = self.TopicForm(data={
            'title': '这是一个有效的主题标题',
            'content': long_content
        })
        assert not form.is_valid()
        assert 'content' in form.errors

    def test_content_whitespace_stripped(self):
        """测试内容自动去除首尾空格"""
        form = self.TopicForm(data={
            'title': '  这是一个有效的主题标题  ',
            'content': '  这是一个有效的主题内容，至少10个字符  '
        })
        assert form.is_valid()
        assert form.cleaned_data['title'] == '这是一个有效的主题标题'
        assert form.cleaned_data['content'] == '这是一个有效的主题内容，至少10个字符'


@pytest.mark.django_db
class TestReplyForm:
    """回复表单测试"""

    def setup_method(self):
        """设置测试数据"""
        from apps.forum.forms import ReplyForm
        self.ReplyForm = ReplyForm

    def test_valid_reply_form(self):
        """测试有效的回复表单"""
        form = self.ReplyForm(data={
            'content': '这是一个有效的回复内容，至少5个字符'
        })
        assert form.is_valid()

    def test_content_too_short(self):
        """测试回复内容过短"""
        form = self.ReplyForm(data={
            'content': '短'  # 少于5个字符
        })
        assert not form.is_valid()
        assert 'content' in form.errors

    def test_content_too_long(self):
        """测试回复内容过长"""
        long_content = 'a' * 5001  # 超过5000字符
        form = self.ReplyForm(data={
            'content': long_content
        })
        assert not form.is_valid()
        assert 'content' in form.errors

    def test_content_whitespace_stripped(self):
        """测试回复内容自动去除首尾空格"""
        form = self.ReplyForm(data={
            'content': '  这是一个有效的回复内容，至少5个字符  '
        })
        assert form.is_valid()
        assert form.cleaned_data['content'] == '这是一个有效的回复内容，至少5个字符'
