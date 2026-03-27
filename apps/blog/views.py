from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Prefetch
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.cache import cache
from django.utils.decorators import method_decorator
from moderation.services import smart_moderate_instance
from apps.core.rate_limit import rate_limit, rate_limit_by_user
from .models import Post, Category, Tag, Comment, CommentLike
from .forms import CommentForm, PostForm


def get_categories_and_tags():
    """
    获取带发布文章数量的分类和标签（带缓存）

    性能优化：
    - 使用 select_related 减少查询
    - 缓存 5 分钟
    - 只查询需要的字段
    """
    cache_key = 'blog_categories_tags'
    result = cache.get(cache_key)

    if result is None:
        # 优化查询：只选择需要的字段
        categories = list(
            Category.objects.annotate(
                published_count=Count('posts', filter=models.Q(
                    posts__status='published',
                    posts__slug__isnull=False
                ) & ~models.Q(posts__slug=''))
            ).only('name', 'slug')
        )

        tags = list(
            Tag.objects.annotate(
                published_count=Count('posts', filter=models.Q(
                    posts__status='published',
                    posts__slug__isnull=False
                ) & ~models.Q(posts__slug=''))
            ).only('name', 'slug')
        )

        result = (categories, tags)
        # 缓存 5 分钟
        cache.set(cache_key, result, 300)

    return result


class PostListView(ListView):
    """文章列表视图"""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        """
        获取查询集，支持分类和标签筛选

        性能优化：
        - select_related: 预加载 author, category（一对多/一对一）
        - prefetch_related: 预加载 tags（多对多）
        - only: 只查询需要的字段
        """
        queryset = Post.objects.filter(
            status='published',
            slug__isnull=False
        ).exclude(
            slug=''
        ).select_related(
            'author',
            'category'
        ).prefetch_related(
            Prefetch('tags', queryset=Tag.objects.only('name', 'slug'))
        ).only(
            'title',
            'slug',
            'summary',
            'views_count',
            'published_at',
            'allow_comments',
            'author__id',
            'author__username',
            'author__nickname',
            'category__id',
            'category__name',
            'category__slug',
        )

        # 分类筛选
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)

        # 标签筛选
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags=tag)

        return queryset

    def get_context_data(self, **kwargs):
        """获取上下文数据"""
        context = super().get_context_data(**kwargs)
        # 获取分类和标签
        context['categories'], context['tags'] = get_categories_and_tags()

        # 当前分类或标签
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)

        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            context['current_tag'] = get_object_or_404(Tag, slug=tag_slug)

        return context


class PostDetailView(DetailView):
    """文章详情视图"""
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'

    def get_queryset(self):
        """
        获取查询集，预加载相关数据

        性能优化：
        - select_related: author, category
        - prefetch_related: tags, comments
        """
        return Post.objects.select_related(
            'author',
            'category'
        ).prefetch_related(
            Prefetch('tags', queryset=Tag.objects.only('name', 'slug')),
            Prefetch(
                'comments',
                queryset=Comment.objects.filter(
                    review_status='approved'
                ).select_related('user').only(
                    'id',
                    'content',
                    'name',
                    'email',
                    'like_count',
                    'created_at',
                    'user__id',
                    'user__username',
                    'user__nickname',
                )
            )
        )

    def get_object(self, queryset=None):
        """获取文章对象并增加浏览数"""
        obj = super().get_object(queryset)
        # 只对已发布的文章增加浏览数
        if obj.status == 'published':
            obj.increase_views()
        return obj

    def get_context_data(self, **kwargs):
        """获取上下文数据"""
        context = super().get_context_data(**kwargs)
        # 评论已在 prefetch_related 中预加载，直接过滤即可
        # 不再执行额外查询
        context['comments'] = [
            c for c in self.object.comments.all()
            if c.review_status == 'approved'
        ]
        # 评论表单
        context['comment_form'] = CommentForm(user=self.request.user)
        # 获取分类和标签
        context['categories'], context['tags'] = get_categories_and_tags()
        return context


@rate_limit('comment', rate='10/m', method='POST')
def comment_create_view(request, post_slug):
    """
    创建评论视图

    性能优化：
    - 速率限制：每分钟最多 10 条评论
    - 防止垃圾评论和刷评
    """
    post = get_object_or_404(Post, slug=post_slug, status='published')

    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post

            # 记录用户信息
            if request.user.is_authenticated:
                comment.user = request.user
            else:
                # 游客评论，使用表单提交的姓名和邮箱
                comment.name = form.cleaned_data.get('name')
                comment.email = form.cleaned_data.get('email')

            # 记录IP地址和用户代理
            comment.ip_address = request.META.get('REMOTE_ADDR')
            comment.user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]

            # 先保存为 pending 状态
            comment.review_status = 'pending'
            comment.save()

            # 智能审核：敏感词 + AI 双重检测
            status, message = smart_moderate_instance(comment)

            # 根据审核结果显示提示
            if status == 'approved':
                messages.success(request, '评论已发布')
            elif status == 'rejected':
                messages.warning(request, f'评论未通过审核：{message}')
            else:
                messages.success(request, '评论已提交，等待审核后显示')

            return redirect(post.get_absolute_url())

    return redirect(post.get_absolute_url())


@login_required
@rate_limit('like', rate='30/m', method='POST')
def like_comment_view(request, comment_id):
    """
    点赞评论视图

    性能优化：
    - 速率限制：每分钟最多 30 次点赞
    - 防止刷赞
    """
    comment = get_object_or_404(Comment, id=comment_id)

    # 检查评论是否已审核通过
    if comment.review_status != 'approved':
        return JsonResponse({
            'success': False,
            'message': '只能对已审核通过的评论点赞'
        })

    # 检查用户是否已经点赞
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)

    if not created:
        # 已经点赞，取消点赞
        like.delete()
        liked = False
    else:
        # 新点赞
        liked = True

    # 更新评论点赞数
    comment.update_like_count()

    return JsonResponse({
        'success': True,
        'liked': liked,
        'like_count': comment.like_count,
        'message': '操作成功'
    })


# ==================== 文章编辑视图 ====================

@method_decorator(rate_limit_by_user('post_create', rate='5/h', method='POST'), name='dispatch')
class PostCreateView(LoginRequiredMixin, CreateView):
    """
    创建文章视图

    性能优化：
    - 速率限制：每小时最多创建 5 篇文章
    - 防止垃圾内容刷屏
    """
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, '文章创建成功！')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'], context['tags'] = get_categories_and_tags()
        context['title'] = '创建文章'
        context['submit_text'] = '发布文章'
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """更新文章视图"""
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    slug_field = 'slug'

    def test_func(self):
        """只有作者可以编辑"""
        post = self.get_object()
        return post.author == self.request.user or self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, '文章更新成功！')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'], context['tags'] = get_categories_and_tags()
        context['title'] = '编辑文章'
        context['submit_text'] = '保存修改'
        return context


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """删除文章视图"""
    model = Post
    slug_field = 'slug'
    success_url = reverse_lazy('blog:post_list')

    def test_func(self):
        """只有作者可以删除"""
        post = self.get_object()
        return post.author == self.request.user or self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        messages.success(request, '文章已删除！')
        return super().delete(request, *args, **kwargs)


@login_required
def post_draft_list(request):
    """我的草稿列表"""
    drafts = Post.objects.filter(author=request.user, status='draft').order_by('-updated_at')
    categories, tags = get_categories_and_tags()

    paginator = Paginator(drafts, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    return render(request, 'blog/post_draft_list.html', {
        'posts': page_obj,
        'categories': categories,
        'tags': tags,
        'title': '我的草稿'
    })


@login_required
def my_posts(request):
    """我的文章列表"""
    posts = Post.objects.filter(author=request.user).order_by('-updated_at')
    categories, tags = get_categories_and_tags()

    paginator = Paginator(posts, 20)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    return render(request, 'blog/my_posts.html', {
        'posts': page_obj,
        'categories': categories,
        'tags': tags,
        'title': '我的文章'
    })
