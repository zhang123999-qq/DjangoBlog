from django.urls import path
from . import views

app_name = "tools"

urlpatterns = [
    path("", views.tool_list, name="tool_list"),
    path("my-ip/json/", views.my_ip_json, name="my_ip_json"),
    path("<slug:tool_slug>/", views.tool_detail, name="tool_detail"),
]
