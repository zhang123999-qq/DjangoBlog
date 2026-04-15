"""
API 统一响应格式

使用方法:
    from apps.api.response import APIResponse

    # 成功响应
    return APIResponse.success(data={'id': 1, 'name': 'test'})

    # 错误响应
    return APIResponse.error('操作失败', code=400)

    # 分页响应
    return APIResponse.paginated(
        data=posts,
        page=1,
        page_size=20,
        total=100
    )

响应格式:
    成功: {"code": 200, "message": "success", "data": {...}}
    失败: {"code": 400, "message": "错误信息", "errors": {...}}
"""

from typing import Any, Dict, List, Optional, Union
from rest_framework.response import Response
from rest_framework import status


class APIResponse:
    """
    统一 API 响应格式

    格式规范:
    - 成功: {"code": 200, "message": "success", "data": {...}}
    - 失败: {"code": 4xx/5xx, "message": "错误信息", "errors": {...}}
    """

    @staticmethod
    def success(
        data: Optional[Union[Dict, List, Any]] = None,
        message: str = "success",
        code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        成功响应

        Args:
            data: 响应数据
            message: 成功消息
            code: HTTP 状态码
            headers: 额外的响应头

        Returns:
            Response: DRF Response 对象
        """
        body = {
            "code": code,
            "message": message,
            "success": True,
        }
        if data is not None:
            body["data"] = data

        return Response(body, status=code, headers=headers)

    @staticmethod
    def error(
        message: str = "请求失败",
        code: int = 400,
        errors: Optional[Union[Dict, List, str]] = None,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        错误响应

        Args:
            message: 错误消息
            code: HTTP 状态码
            errors: 详细错误信息
            error_code: 业务错误码（如 "VALIDATION_ERROR"）
            headers: 额外的响应头

        Returns:
            Response: DRF Response 对象
        """
        body = {
            "code": code,
            "message": message,
            "success": False,
        }
        if errors is not None:
            body["errors"] = errors
        if error_code is not None:
            body["error_code"] = error_code

        return Response(body, status=code, headers=headers)

    @staticmethod
    def paginated(
        data: List, page: int, page_size: int, total: int, message: str = "success", extra: Optional[Dict] = None
    ) -> Response:
        """
        分页响应

        Args:
            data: 当前页数据
            page: 当前页码
            page_size: 每页数量
            total: 总数量
            message: 成功消息
            extra: 额外的响应字段

        Returns:
            Response: DRF Response 对象
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        body = {
            "code": 200,
            "message": message,
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }
        if extra:
            body.update(extra)

        return Response(body, status=status.HTTP_200_OK)

    @staticmethod
    def created(data: Optional[Union[Dict, List, Any]] = None, message: str = "创建成功") -> Response:
        """创建成功响应 (201)"""
        return APIResponse.success(data=data, message=message, code=status.HTTP_201_CREATED)

    @staticmethod
    def no_content(message: str = "删除成功") -> Response:
        """无内容响应 (204)"""
        return APIResponse.success(data=None, message=message, code=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def bad_request(message: str = "请求参数错误", errors: Optional[Union[Dict, List, str]] = None) -> Response:
        """400 错误"""
        return APIResponse.error(message=message, code=400, errors=errors)

    @staticmethod
    def unauthorized(message: str = "未授权，请先登录") -> Response:
        """401 未授权"""
        return APIResponse.error(message=message, code=401)

    @staticmethod
    def forbidden(message: str = "无权限访问") -> Response:
        """403 禁止访问"""
        return APIResponse.error(message=message, code=403)

    @staticmethod
    def not_found(message: str = "资源不存在") -> Response:
        """404 未找到"""
        return APIResponse.error(message=message, code=404)

    @staticmethod
    def conflict(message: str = "资源冲突") -> Response:
        """409 冲突"""
        return APIResponse.error(message=message, code=409)

    @staticmethod
    def too_many_requests(message: str = "请求过于频繁，请稍后再试") -> Response:
        """429 请求过多"""
        return APIResponse.error(message=message, code=429)

    @staticmethod
    def server_error(message: str = "服务器内部错误") -> Response:
        """500 服务器错误"""
        return APIResponse.error(message=message, code=500)


class APIResponseMixin:
    """
    ViewSet 响应混入类

    使用方法:
        class PostViewSet(APIResponseMixin, viewsets.ModelViewSet):
            def list(self, request):
                queryset = self.filter_queryset(self.get_queryset())
                page = self.paginate_queryset(queryset)
                return self.paginated_response(page, queryset.count())
    """

    def success_response(self, data=None, message="success"):
        """成功响应"""
        return APIResponse.success(data=data, message=message)

    def error_response(self, message="请求失败", code=400, errors=None):
        """错误响应"""
        return APIResponse.error(message=message, code=code, errors=errors)

    def paginated_response(self, data, total, page=None, page_size=None):
        """分页响应"""
        page = page or self.request.query_params.get("page", 1)
        page_size = page_size or self.request.query_params.get("page_size", 20)
        return APIResponse.paginated(data=data, page=int(page), page_size=int(page_size), total=total)
