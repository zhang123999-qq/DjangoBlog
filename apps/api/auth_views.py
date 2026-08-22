"""认证相关 API 视图

提供基于 Django Session 的 REST 认证端点，供前端 SPA 调用。
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle

from apps.api.response import APIResponse
from apps.accounts.models import User


class LoginRateThrottle(AnonRateThrottle):
    """登录接口限流：10次/分钟"""

    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    """注册接口限流：5次/小时"""

    scope = "register"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def api_login(request):
    """
    用户登录

    POST /api/auth/login/
    Body: {"username": "xxx", "password": "xxx"}

    成功后在 Session 中记录登录状态，前端后续请求自动携带 Cookie。
    """
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return APIResponse.bad_request(
            message="用户名和密码不能为空",
            errors={"username": "必填" if not username else None, "password": "必填" if not password else None},
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return APIResponse.unauthorized(message="用户名或密码错误")

    if not user.is_active:
        return APIResponse.forbidden(message="账号已被禁用")

    login(request, user)

    return APIResponse.success(
        data=_user_data(user),
        message="登录成功",
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def api_register(request):
    """
    用户注册

    POST /api/auth/register/
    Body: {"username": "xxx", "email": "xxx", "password": "xxx", "password_confirm": "xxx"}

    注册成功后自动登录。
    """
    username = request.data.get("username", "").strip()
    email = request.data.get("email", "").strip()
    password = request.data.get("password", "")
    password_confirm = request.data.get("password_confirm", "")

    errors: dict[str, str | None] = {}

    if not username:
        errors["username"] = "必填"
    elif len(username) < 3:
        errors["username"] = "用户名至少 3 个字符"
    elif User.objects.filter(username=username).exists():
        errors["username"] = "用户名已存在"

    if not email:
        errors["email"] = "必填"

    if not password:
        errors["password"] = "必填"
    elif len(password) < 8:
        errors["password"] = "密码至少 8 个字符"
    else:
        # 执行 Django 密码强度验证（CommonPassword、NumericPassword 等）
        try:
            validate_password(password, user=User(username=username, email=email))
        except Exception as e:
            errors["password"] = "; ".join(e.messages) if hasattr(e, "messages") else str(e)

    if password != password_confirm:
        errors["password_confirm"] = "两次密码不一致"

    if any(v is not None for v in errors.values()):
        return APIResponse.bad_request(message="注册信息有误", errors=errors)

    user = User.objects.create_user(username=username, email=email, password=password)

    login(request, user)

    return APIResponse.created(
        data=_user_data(user),
        message="注册成功",
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """
    用户登出

    POST /api/auth/logout/
    需要已登录状态。
    """
    logout(request)
    return APIResponse.success(message="已退出登录")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_user_info(request):
    """
    获取当前登录用户信息

    GET /api/auth/user/
    返回当前 Session 对应的用户详情。
    """
    return APIResponse.success(data=_user_data(request.user))


@api_view(["GET"])
@permission_classes([AllowAny])
def api_csrf_token(request):
    """
    获取 CSRF Token

    GET /api/auth/csrf/
    Django 的 CsrfViewMiddleware 会在响应中设置 csrftoken Cookie。
    前端只需调用此端点触发 Cookie 设置，然后从 Cookie 中读取 token。
    """
    return APIResponse.success(message="CSRF cookie set")


def _user_data(user: User) -> dict[str, object]:
    """构造用户信息字典"""
    data: dict[str, object] = {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "is_staff": user.is_staff,
        "nickname": getattr(user, "nickname", "") or "",
    }
    # 尝试获取 profile 扩展信息
    try:
        profile = user.profile
        data["avatar"] = getattr(profile, "avatar", "") or ""
        data["bio"] = getattr(profile, "bio", "") or ""
    except Exception:
        pass
    return data
