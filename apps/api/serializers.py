"""API 序列化器"""

from rest_framework import serializers
from apps.blog.models import Category, Tag, Post, Comment
from apps.forum.models import Board, Topic, Reply
from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""

    avatar = serializers.CharField(source="profile.avatar", read_only=True)
    bio = serializers.CharField(source="profile.bio", read_only=True)
    website = serializers.CharField(source="profile.website", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "avatar", "bio", "website"]
        read_only_fields = ["id", "username"]


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器"""

    post_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "post_count", "created_at"]


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""

    post_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "post_count", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    """文章序列化器"""

    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "content",
            "status",
            "views_count",
            "allow_comments",
            "published_at",
            "created_at",
            "author",
            "category",
            "tags",
        ]


class PostListSerializer(serializers.ModelSerializer):
    """文章列表序列化器"""

    author = serializers.CharField(source="author.username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Post
        fields = ["id", "title", "slug", "summary", "views_count", "published_at", "author", "category_name"]


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "content", "user", "name", "like_count", "created_at"]


class BoardSerializer(serializers.ModelSerializer):
    """版块序列化器"""

    topic_count = serializers.IntegerField(read_only=True)
    reply_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Board
        fields = ["id", "name", "slug", "description", "topic_count", "reply_count", "created_at"]


class TopicSerializer(serializers.ModelSerializer):
    """主题序列化器"""

    author = UserSerializer(read_only=True)
    board = BoardSerializer(read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id",
            "title",
            "content",
            "views_count",
            "reply_count",
            "is_pinned",
            "is_locked",
            "created_at",
            "author",
            "board",
        ]


class TopicListSerializer(serializers.ModelSerializer):
    """主题列表序列化器"""

    author = serializers.CharField(source="author.username", read_only=True)
    board_name = serializers.CharField(source="board.name", read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "title", "views_count", "reply_count", "is_pinned", "created_at", "author", "board_name"]


class ReplySerializer(serializers.ModelSerializer):
    """回复序列化器"""

    author = UserSerializer(read_only=True)

    class Meta:
        model = Reply
        fields = ["id", "content", "like_count", "created_at", "author"]
