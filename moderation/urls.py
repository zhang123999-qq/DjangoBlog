from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('', views.moderation_dashboard, name='dashboard'),
    path('approve/<str:content_type>/<int:content_id>/', views.approve_content, name='approve'),
    path('reject/<str:content_type>/<int:content_id>/', views.reject_content, name='reject'),
]
