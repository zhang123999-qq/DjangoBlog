"""API 序列化器"""

from rest_framework import serializers

from apps.accounts.models import User
from apps.blog.models import Category, Comment, Post, Tag
from apps.forum.models import Board, Reply, Topic


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""

    avatar = serializers.CharField(source="profile.avatar", read_only=True)
    bio = serializers.CharField(source="profile.bio", read_only=True)
    website = serializers.CharField(source="profile.website", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "avatar", "bio", "website"]
        read_only_fields = ["id", "username"]


class _TaxonomySerializer(serializers.ModelSerializer):
    """分类/标签共享序列化器基类（name + slug + post_count）"""

    post_count = serializers.IntegerField(read_only=True)

    class Meta:
        fields = ["id", "name", "slug", "post_count", "created_at"]


class CategorySerializer(_TaxonomySerializer):
    """分类序列化器"""

    class Meta(_TaxonomySerializer.Meta):
        model = Category


class TagSerializer(_TaxonomySerializer):
    """标签序列化器"""

    class Meta(_TaxonomySerializer.Meta):
        model = Tag


class PostSerializer(serializers.ModelSerializer):
    """文章详情序列化器"""

    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "id", "title", "slug", "summary", "content", "status",
            "views_count", "allow_comments", "published_at", "created_at",
            "author", "category", "tags",
        ]


class PostListSerializer(serializers.ModelSerializer):
    """文章列表序列化器（轻量级，扁平化关联）"""

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

    class Meta:
        model = Board
        fields = ["id", "name", "slug", "description", "topic_count", "reply_count", "created_at"]


class TopicSerializer(serializers.ModelSerializer):
    """主题详情序列化器"""

    author = UserSerializer(read_only=True)
    board = BoardSerializer(read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id", "title", "content", "views_count", "reply_count",
            "is_pinned", "is_locked", "created_at", "author", "board",
        ]


class TopicListSerializer(serializers.ModelSerializer):
    """主题列表序列化器（轻量级，扁平化关联）"""

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
