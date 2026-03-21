from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.contrib import messages
from moderation.utils import check_sensitive_content
from .models import Board, Topic, Reply, ReplyLike
from .forms import TopicForm, ReplyForm


class BoardListView(ListView):
    """版块列表视图"""
    model = Board
    template_name = 'forum/board_list.html'
    context_object_name = 'boards'


class TopicListView(ListView):
    """主题列表视图"""
    model = Topic
    template_name = 'forum/topic_list.html'
    context_object_name = 'topics'
    paginate_by = 20

    def get_queryset(self):
        """获取查询集，按版块筛选"""
        self.board = get_object_or_404(Board, slug=self.kwargs.get('board_slug'))
        return Topic.objects.filter(board=self.board, review_status='approved').select_related('author', 'board').order_by('-is_pinned', '-last_reply_at', '-created_at')

    def get_context_data(self, **kwargs):
        """获取上下文数据"""
        context = super().get_context_data(**kwargs)
        context['board'] = self.board
        return context


class TopicDetailView(DetailView):
    """主题详情视图"""
    model = Topic
    template_name = 'forum/topic_detail.html'
    context_object_name = 'topic'
    pk_url_kwarg = 'topic_id'

    def get_queryset(self):
        """获取查询集，按版块筛选"""
        board = get_object_or_404(Board, slug=self.kwargs.get('board_slug'))
        return Topic.objects.filter(board=board, review_status='approved').select_related('author', 'board').prefetch_related('replies__author')

    def get_object(self, queryset=None):
        """获取主题对象并增加浏览量"""
        obj = super().get_object(queryset)
        obj.increase_views()
        return obj

    def get_context_data(self, **kwargs):
        """获取上下文数据"""
        context = super().get_context_data(**kwargs)
        context['replies'] = self.object.replies.filter(is_deleted=False, review_status='approved')
        context['reply_form'] = ReplyForm()
        return context


@login_required
def topic_create_view(request, board_slug):
    """创建主题视图"""
    board = get_object_or_404(Board, slug=board_slug)
    
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.author = request.user
            
            # 敏感词检测
            content = f"{topic.title} {topic.content}"
            has_sensitive, hit_words = check_sensitive_content(content)
            if has_sensitive:
                topic.review_status = 'pending'
                topic.review_note = f'命中敏感词: {", ".join(hit_words)}'
            else:
                # 即使未命中敏感词，也保持默认 pending 状态
                topic.review_status = 'pending'
            
            topic.save()
            # 更新版块统计信息
            board.update_counts()
            # 显示审核提示
            messages.success(request, '主题已提交，等待审核后显示')
            return redirect(board.get_absolute_url())
    else:
        form = TopicForm()
    
    return render(request, 'forum/topic_form.html', {'form': form, 'board': board, 'title': '发布主题'})


@login_required
def reply_create_view(request, board_slug, topic_id):
    """创建回复视图"""
    topic = get_object_or_404(Topic, id=topic_id, board__slug=board_slug)
    
    # 检查主题是否被锁定
    if topic.is_locked:
        return HttpResponseForbidden('主题已被锁定，无法回复')
    
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.topic = topic
            reply.author = request.user
            
            # 敏感词检测
            has_sensitive, hit_words = check_sensitive_content(reply.content)
            if has_sensitive:
                reply.review_status = 'pending'
                reply.review_note = f'命中敏感词: {", ".join(hit_words)}'
            else:
                # 即使未命中敏感词，也保持默认 pending 状态
                reply.review_status = 'pending'
            
            reply.save()
            # 更新主题回复数和最后回复时间
            topic.update_reply_count()
            # 显示审核提示
            messages.success(request, '回复已提交，等待审核后显示')
            return redirect(topic.get_absolute_url())
    
    return redirect(topic.get_absolute_url())


@login_required
def like_reply_view(request, reply_id):
    """点赞回复视图"""
    reply = get_object_or_404(Reply, id=reply_id)
    
    # 检查回复是否已审核通过
    if reply.review_status != 'approved':
        return JsonResponse({
            'success': False,
            'message': '只能对已审核通过的回复点赞'
        })
    
    # 检查用户是否已经点赞
    like, created = ReplyLike.objects.get_or_create(user=request.user, reply=reply)
    
    if not created:
        # 已经点赞，取消点赞
        like.delete()
        liked = False
    else:
        # 新点赞
        liked = True
    
    # 更新回复点赞数
    reply.update_like_count()
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'like_count': reply.like_count,
        'message': '操作成功'
    })
