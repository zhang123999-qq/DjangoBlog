"""
浏览量记录中间件

自动记录页面浏览量
"""

import logging
import re
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse
from django.conf import settings

from .views_counter import ViewsCounter

logger = logging.getLogger(__name__)


class ViewsCounterMiddleware:
    """
    浏览量计数中间件

    自动记录文章、主题等内容的浏览量

    配置：
        VIEWS_COUNTER_PATTERNS = [
            (r'^/blog/post/(?P<slug>[-\\w]+)/$', 'post', 'slug'),
            (r'^/forum/topic/(?P<board_slug>[-\\w]+)/(?P<topic_id>\\d+)/$', 'topic', 'topic_id'),
        ]
    """

    # 默认匹配模式
    DEFAULT_PATTERNS = [
        # 博客文章
        {
            'pattern': r'^/blog/post/(?P<slug>[-\w]+)/$',
            'model_type': 'post',
            'lookup_field': 'slug',
            'queryset_method': 'get_by_slug',
        },
        # 论坛主题
        {
            'pattern': r'^/forum/topic/(?P<board_slug>[-\w]+)/(?P<topic_id>\d+)/$',
            'model_type': 'topic',
            'lookup_field': 'topic_id',
        },
    ]

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        # 合并配置
        self.patterns = getattr(settings, 'VIEWS_COUNTER_PATTERNS', self.DEFAULT_PATTERNS)
        # 编译正则
        self._compiled_patterns = [
            {**p, 'compiled': re.compile(p['pattern'])}
            for p in self.patterns
        ]
        # 排除的路径
        self.exclude_paths = getattr(settings, 'VIEWS_COUNTER_EXCLUDE', [
            '/admin/',
            '/api/',
            '/static/',
            '/media/',
        ])

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # 只处理 GET 请求
        if request.method == 'GET':
            self._process_request(request)

        response = self.get_response(request)
        return response

    def _process_request(self, request: HttpRequest) -> None:
        """处理请求"""
        path = request.path

        # 检查排除路径
        for exclude in self.exclude_paths:
            if path.startswith(exclude):
                return

        # 匹配模式
        for pattern_config in self._compiled_patterns:
            match = pattern_config['compiled'].match(path)
            if match:
                self._record_view(request, pattern_config, match.groupdict())
                break

    def _record_view(
        self,
        request: HttpRequest,
        pattern_config: dict,
        match_dict: dict
    ) -> None:
        """记录浏览量"""
        model_type = pattern_config['model_type']
        lookup_field = pattern_config['lookup_field']

        # 获取对象 ID
        lookup_value = match_dict.get(lookup_field)
        if not lookup_value:
            return

        object_id = self._resolve_object_id(model_type, lookup_field, lookup_value)
        if object_id is None:
            return

        # 记录浏览量
        ViewsCounter.increment(model_type, object_id, request)

    def _resolve_object_id(
        self,
        model_type: str,
        lookup_field: str,
        lookup_value: str
    ) -> Optional[int]:
        """
        解析对象 ID

        Args:
            model_type: 模型类型
            lookup_field: 查找字段
            lookup_value: 查找值

        Returns:
            Optional[int]: 对象 ID
        """
        # 如果查找字段就是 ID，直接返回
        if lookup_field in ('id', 'topic_id'):
            try:
                return int(lookup_value)
            except (ValueError, TypeError):
                return None

        # 否则需要查询数据库
        try:
            if model_type == 'post' and lookup_field == 'slug':
                from apps.blog.models import Post
                post = Post.objects.filter(slug=lookup_value).first()
                return post.id if post else None
        except Exception as e:
            logger.warning(f"解析对象 ID 失败: {e}")

        return None
