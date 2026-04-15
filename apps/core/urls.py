from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("search/", views.search_view, name="search"),
    # 健康检查端点（Kubernetes 风格）
    path("healthz/", views.healthz_view, name="healthz"),
    path("readiness/", views.readiness_view, name="readiness"),
    path("liveness/", views.liveness_view, name="liveness"),
    path("contact/", views.contact_view, name="contact"),
    path("settings/", views.settings_view, name="settings"),
]
