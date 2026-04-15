"""
搜索 API 视图

提供全局搜索、文章搜索、主题搜索等 API
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from apps.core.search import SearchService
from apps.api.response import APIResponse


class GlobalSearchView(APIView):
    """
    全局搜索 API

    同时搜索文章和主题
    """

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="global_search",
        summary="全局搜索",
        description="同时搜索文章和论坛主题",
        parameters=[
            OpenApiParameter(
                name="q",
                description="搜索关键词",
                required=True,
                type=str,
            ),
            OpenApiParameter(
                name="limit",
                description="每个类型返回的最大结果数",
                required=False,
                type=int,
                default=10,
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "posts": {"type": "object"},
                            "topics": {"type": "object"},
                            "total": {"type": "integer"},
                        },
                    },
                },
            }
        },
        examples=[
            OpenApiExample(
                "搜索示例",
                value={
                    "code": 200,
                    "message": "success",
                    "success": True,
                    "data": {
                        "posts": {"hits": [{"id": "1", "title": "Django 入门教程", "content": "..."}], "total": 5},
                        "topics": {"hits": [], "total": 0},
                        "total": 5,
                    },
                },
            )
        ],
    )
    def get(self, request):
        """全局搜索"""
        query = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 10))

        if not query:
            return APIResponse.bad_request("请提供搜索关键词")

        if len(query) < 2:
            return APIResponse.bad_request("搜索关键词至少 2 个字符")

        # 执行搜索
        results = SearchService.global_search(query, limit=limit)

        return APIResponse.success(data=results)


class PostSearchView(APIView):
    """
    文章搜索 API

    仅搜索文章
    """

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="search_posts",
        summary="文章搜索",
        description="搜索博客文章",
        parameters=[
            OpenApiParameter(
                name="q",
                description="搜索关键词",
                required=True,
                type=str,
            ),
            OpenApiParameter(
                name="page",
                description="页码",
                required=False,
                type=int,
                default=1,
            ),
            OpenApiParameter(
                name="page_size",
                description="每页数量",
                required=False,
                type=int,
                default=20,
            ),
        ],
    )
    def get(self, request):
        """文章搜索"""
        query = request.query_params.get("q", "").strip()
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        if not query:
            return APIResponse.bad_request("请提供搜索关键词")

        if len(query) < 2:
            return APIResponse.bad_request("搜索关键词至少 2 个字符")

        # 执行搜索
        offset = (page - 1) * page_size
        results = SearchService.search_posts(
            query,
            limit=page_size,
            offset=offset,
            fields=["title", "content", "summary"],
        )

        return APIResponse.paginated(
            data=results.get("hits", []),
            page=page,
            page_size=page_size,
            total=results.get("total", 0),
        )


class TopicSearchView(APIView):
    """
    主题搜索 API

    仅搜索论坛主题
    """

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="search_topics",
        summary="主题搜索",
        description="搜索论坛主题",
        parameters=[
            OpenApiParameter(
                name="q",
                description="搜索关键词",
                required=True,
                type=str,
            ),
            OpenApiParameter(
                name="page",
                description="页码",
                required=False,
                type=int,
                default=1,
            ),
            OpenApiParameter(
                name="page_size",
                description="每页数量",
                required=False,
                type=int,
                default=20,
            ),
        ],
    )
    def get(self, request):
        """主题搜索"""
        query = request.query_params.get("q", "").strip()
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        if not query:
            return APIResponse.bad_request("请提供搜索关键词")

        if len(query) < 2:
            return APIResponse.bad_request("搜索关键词至少 2 个字符")

        # 执行搜索
        offset = (page - 1) * page_size
        results = SearchService.search_topics(
            query,
            limit=page_size,
            offset=offset,
            fields=["title", "content"],
        )

        return APIResponse.paginated(
            data=results.get("hits", []),
            page=page,
            page_size=page_size,
            total=results.get("total", 0),
        )


class SearchHealthView(APIView):
    """
    搜索服务健康检查
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """健康检查"""
        is_healthy = SearchService.health_check()

        return Response(
            {
                "status": "healthy" if is_healthy else "unhealthy",
                "backend": type(SearchService.get_backend()).__name__,
            }
        )
