"""评论相关 API 视图"""

import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.api.response import APIResponse
from apps.blog import services as blog_services
from apps.blog.services import CommentsClosedError, ValidationError

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_create_comment(request, slug: str):
    """
    创建评论

    POST /api/posts/{slug}/comments/create/
    Body: {"content": "评论内容"}

    需要登录。CSRF Token 通过 X-CSRFToken 请求头传递。
    """
    content = request.data.get("content", "").strip()
    ip_address = _get_client_ip(request)

    try:
        result = blog_services.create_comment(
            slug=slug,
            user=request.user,
            content=content,
            ip_address=ip_address,
        )
    except CommentsClosedError:
        return APIResponse.bad_request(message="该文章已关闭评论")
    except ValidationError as e:
        return APIResponse.bad_request(message=str(e))
    except Exception:
        return APIResponse.not_found(message="文章不存在")

    status = result["status"]
    data = result["result"]

    if status == "approved":
        return APIResponse.created(data=data, message="评论已发布")
    elif status == "rejected":
        return APIResponse.error(message=f"评论未通过审核: {result['message']}", code=400)
    else:
        return APIResponse.created(data=data, message="评论已提交，等待审核")


def _get_client_ip(request) -> str | None:
    """获取客户端 IP"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()  # type: ignore[no-any-return]
    ip = request.META.get("REMOTE_ADDR")
    return ip if isinstance(ip, str) else None  # type: ignore[no-any-return]
