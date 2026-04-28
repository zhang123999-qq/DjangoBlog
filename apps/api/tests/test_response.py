"""
API 响应格式测试

测试覆盖:
- 成功响应格式
- 错误响应格式
- 分页响应格式
- 异常处理器
"""

import pytest
from rest_framework.test import APIRequestFactory
from apps.api.response import APIResponse
from apps.api.exception_handler import (
    exception_handler,
    BusinessError,
    ResourceNotFound,
    PermissionDeniedError,
)


class TestAPIResponse:
    """API 响应格式测试"""

    def test_success_response(self):
        """测试成功响应"""
        response = APIResponse.success(data={'id': 1, 'name': 'test'})

        assert response.status_code == 200
        assert response.data['code'] == 200
        assert response.data['message'] == 'success'
        assert response.data['success'] is True
        assert response.data['data'] == {'id': 1, 'name': 'test'}

    def test_success_response_with_custom_message(self):
        """测试自定义消息的成功响应"""
        response = APIResponse.success(data={'id': 1}, message='创建成功')

        assert response.data['message'] == '创建成功'

    def test_error_response(self):
        """测试错误响应"""
        response = APIResponse.error(message='参数错误', code=400)

        assert response.status_code == 400
        assert response.data['code'] == 400
        assert response.data['message'] == '参数错误'
        assert response.data['success'] is False

    def test_error_response_with_errors(self):
        """测试带详细错误的响应"""
        errors = {'name': ['该字段必填'], 'email': ['邮箱格式错误']}
        response = APIResponse.error(
            message='验证失败',
            code=400,
            errors=errors
        )

        assert response.data['errors'] == errors

    def test_paginated_response(self):
        """测试分页响应"""
        data = [{'id': 1}, {'id': 2}]
        response = APIResponse.paginated(
            data=data,
            page=1,
            page_size=20,
            total=100
        )

        assert response.status_code == 200
        assert response.data['data'] == data
        assert response.data['pagination']['page'] == 1
        assert response.data['pagination']['page_size'] == 20
        assert response.data['pagination']['total'] == 100
        assert response.data['pagination']['total_pages'] == 5
        assert response.data['pagination']['has_next'] is True
        assert response.data['pagination']['has_prev'] is False

    def test_created_response(self):
        """测试创建成功响应"""
        response = APIResponse.created(data={'id': 1})

        assert response.status_code == 201
        assert response.data['message'] == '创建成功'

    def test_bad_request_response(self):
        """测试 400 响应"""
        response = APIResponse.bad_request(message='参数错误')

        assert response.status_code == 400
        assert response.data['message'] == '参数错误'

    def test_unauthorized_response(self):
        """测试 401 响应"""
        response = APIResponse.unauthorized()

        assert response.status_code == 401
        assert '登录' in response.data['message']

    def test_forbidden_response(self):
        """测试 403 响应"""
        response = APIResponse.forbidden()

        assert response.status_code == 403

    def test_not_found_response(self):
        """测试 404 响应"""
        response = APIResponse.not_found()

        assert response.status_code == 404

    def test_too_many_requests_response(self):
        """测试 429 响应"""
        response = APIResponse.too_many_requests()

        assert response.status_code == 429

    def test_server_error_response(self):
        """测试 500 响应"""
        response = APIResponse.server_error()

        assert response.status_code == 500


@pytest.mark.django_db
class TestExceptionHandler:
    """异常处理器测试"""

    @pytest.fixture
    def factory(self):
        return APIRequestFactory()

    def test_validation_error_handling(self, factory):
        """测试验证错误处理"""
        from rest_framework.exceptions import ValidationError

        request = factory.get('/')
        exc = ValidationError(detail={'name': ['该字段必填']})
        context = {'request': request}

        response = exception_handler(exc, context)

        assert response is not None
        assert response.status_code == 400
        assert response.data['success'] is False

    def test_not_found_handling(self, factory):
        """测试 404 处理"""
        from rest_framework.exceptions import NotFound

        request = factory.get('/')
        exc = NotFound()
        context = {'request': request}

        response = exception_handler(exc, context)

        assert response is not None
        assert response.status_code == 404

    def test_permission_denied_handling(self, factory):
        """测试权限拒绝处理"""
        from rest_framework.exceptions import PermissionDenied

        request = factory.get('/')
        exc = PermissionDenied()
        context = {'request': request}

        response = exception_handler(exc, context)

        assert response is not None
        assert response.status_code == 403

    def test_throttled_handling(self, factory):
        """测试限流处理"""
        from rest_framework.exceptions import Throttled

        request = factory.get('/')
        exc = Throttled()
        context = {'request': request}

        response = exception_handler(exc, context)

        assert response is not None
        assert response.status_code == 429

    def test_business_error_handling(self, factory):
        """测试业务异常处理"""
        request = factory.get('/')
        exc = BusinessError(detail='业务处理失败')
        context = {'request': request}

        response = exception_handler(exc, context)

        assert response is not None
        assert response.status_code == 400

    def test_custom_business_errors(self):
        """测试自定义业务异常"""
        # ResourceNotFound
        exc = ResourceNotFound()
        assert exc.status_code == 404

        # PermissionDeniedError
        exc = PermissionDeniedError()
        assert exc.status_code == 403
