"""API 视图"""
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from apps.blog.models import Category, Tag, Post, Comment
from apps.forum.models import Board, Topic, Reply
from .serializers import (
    CategorySerializer,
    TagSerializer,
    PostSerializer,
    PostListSerializer,
    CommentSerializer,
    BoardSerializer,
    TopicSerializer,
    TopicListSerializer,
    ReplySerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """分类 API"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """获取分类下的文章（分页）"""
        category = self.get_object()
        posts = (
            Post.objects.filter(category=category, status='published')
            .select_related('author', 'category')
            .prefetch_related('tags')
        )

        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """标签 API"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """文章 API"""

    queryset = Post.objects.filter(status='published').select_related('author', 'category').prefetch_related('tags')
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'tags', 'author']
    search_fields = ['title', 'content', 'summary']
    ordering_fields = ['published_at', 'views_count', 'created_at']
    ordering = ['-published_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increase_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """获取文章评论（分页）"""
        post = self.get_object()
        comments = Comment.objects.filter(post=post, review_status='approved').select_related('user')

        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class BoardViewSet(viewsets.ReadOnlyModelViewSet):
    """版块 API"""

    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """获取版块下的主题（分页）"""
        board = self.get_object()
        topics = Topic.objects.filter(board=board, review_status='approved').select_related('author', 'board')

        page = self.paginate_queryset(topics)
        if page is not None:
            serializer = TopicListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TopicListSerializer(topics, many=True)
        return Response(serializer.data)


class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """主题 API"""

    queryset = Topic.objects.filter(review_status='approved').select_related('author', 'board').prefetch_related('replies__author')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['board', 'author']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'views_count', 'reply_count']
    ordering = ['-is_pinned', '-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return TopicListSerializer
        return TopicSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increase_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """获取主题回复（分页）"""
        topic = self.get_object()
        replies = Reply.objects.filter(topic=topic, review_status='approved', is_deleted=False).select_related('author', 'topic')

        page = self.paginate_queryset(replies)
        if page is not None:
            serializer = ReplySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReplySerializer(replies, many=True)
        return Response(serializer.data)
