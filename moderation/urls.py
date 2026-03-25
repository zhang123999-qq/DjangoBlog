from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('', views.moderation_dashboard, name='dashboard'),
    path('approve/<str:content_type>/<int:content_id>/', views.approve_content, name='approve'),
    path('reject/<str:content_type>/<int:content_id>/', views.reject_content, name='reject'),

    # JSON API endpoints（统一错误码）
    path('api/approve/<str:content_type>/<int:content_id>/', views.approve_content_api, name='approve-api'),
    path('api/reject/<str:content_type>/<int:content_id>/', views.reject_content_api, name='reject-api'),
]
