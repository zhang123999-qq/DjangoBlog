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


SEARCH_LIMIT_DEFAULT = 10
SEARCH_LIMIT_MAX = 50
SEARCH_PAGE_DEFAULT = 1
SEARCH_PAGE_SIZE_DEFAULT = 20
SEARCH_PAGE_SIZE_MAX = 100


def _parse_positive_int_param(request, name, default, *, min_value=1, max_value=None):
    """Parse and validate integer query params for public search APIs."""
    raw_value = request.query_params.get(name)
    if raw_value in (None, ""):
        return default, None

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None, APIResponse.bad_request(f"Invalid `{name}` parameter.")

    if value < min_value:
        return None, APIResponse.bad_request(f"`{name}` must be >= {min_value}.")

    if max_value is not None and value > max_value:
        return None, APIResponse.bad_request(f"`{name}` must be <= {max_value}.")

    return value, None


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
        limit, error_response = _parse_positive_int_param(
            request,
            "limit",
            SEARCH_LIMIT_DEFAULT,
            min_value=1,
            max_value=SEARCH_LIMIT_MAX,
        )
        if error_response is not None:
            return error_response

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
                            "hits": {"type": "array", "items": {"type": "object"}},
                            "total": {"type": "integer"},
                            "page": {"type": "integer"},
                            "page_size": {"type": "integer"},
                        },
                    },
                },
            }
        },
    )
    def get(self, request):
        """文章搜索"""
        query = request.query_params.get("q", "").strip()
        page, error_response = _parse_positive_int_param(
            request,
            "page",
            SEARCH_PAGE_DEFAULT,
            min_value=1,
        )
        if error_response is not None:
            return error_response

        page_size, error_response = _parse_positive_int_param(
            request,
            "page_size",
            SEARCH_PAGE_SIZE_DEFAULT,
            min_value=1,
            max_value=SEARCH_PAGE_SIZE_MAX,
        )
        if error_response is not None:
            return error_response

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
                            "hits": {"type": "array", "items": {"type": "object"}},
                            "total": {"type": "integer"},
                            "page": {"type": "integer"},
                            "page_size": {"type": "integer"},
                        },
                    },
                },
            }
        },
    )
    def get(self, request):
        """主题搜索"""
        query = request.query_params.get("q", "").strip()
        page, error_response = _parse_positive_int_param(
            request,
            "page",
            SEARCH_PAGE_DEFAULT,
            min_value=1,
        )
        if error_response is not None:
            return error_response

        page_size, error_response = _parse_positive_int_param(
            request,
            "page_size",
            SEARCH_PAGE_SIZE_DEFAULT,
            min_value=1,
            max_value=SEARCH_PAGE_SIZE_MAX,
        )
        if error_response is not None:
            return error_response

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

    @extend_schema(
        operation_id="search_health",
        summary="搜索服务健康检查",
        description="检查搜索服务是否正常运行",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                    "backend": {"type": "string"},
                },
            }
        },
    )
    def get(self, request):
        """健康检查"""
        is_healthy = SearchService.health_check()

        return Response(
            {
                "status": "healthy" if is_healthy else "unhealthy",
                "backend": type(SearchService.get_backend()).__name__,
            }
        )
