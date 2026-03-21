from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.http import HttpResponseForbidden, JsonResponse
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from moderation.services import smart_moderate_instance
from .models import Post, Category, Tag, Comment, CommentLike
from .forms import CommentForm


def get_categories_and_tags():
    """获取带发布文章数量的分类和标签"""
    categories = Category.objects.annotate(
        published_count=Count('posts', filter=models.Q(posts__status='published', posts__slug__isnull=False) & ~models.Q(posts__slug=''))
    )
    tags = Tag.objects.annotate(
        published_count=Count('posts', filter=models.Q(posts__status='published', posts__slug__isnull=False) & ~models.Q(posts__slug=''))
    )
    return categories, tags


class PostListView(ListView):
    """文章列表视图"""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        """获取查询集，支持分类和标签筛选"""
        queryset = Post.objects.filter(status='published', slug__isnull=False).exclude(slug='').select_related('author', 'category').prefetch_related('tags')
        
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
        """获取查询集，预加载相关数据"""
        return Post.objects.select_related('author', 'category').prefetch_related('tags', 'comments')

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
        # 获取已批准的评论
        context['comments'] = self.object.comments.filter(review_status='approved')
        # 评论表单
        context['comment_form'] = CommentForm(user=self.request.user)
        # 获取分类和标签
        context['categories'], context['tags'] = get_categories_and_tags()
        return context


def comment_create_view(request, post_slug):
    """创建评论视图"""
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
def like_comment_view(request, comment_id):
    """点赞评论视图"""
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
