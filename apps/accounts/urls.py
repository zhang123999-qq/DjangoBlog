from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("captcha/refresh/", views.captcha_refresh, name="captcha_refresh"),
]
