from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.tool_list, name='tool_list'),
    path('<slug:tool_slug>/', views.tool_detail, name='tool_detail'),
]
