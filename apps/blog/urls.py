from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:category_slug>/', views.PostListView.as_view(), name='category'),
    path('tag/<slug:tag_slug>/', views.PostListView.as_view(), name='tag'),
    path('comment/<slug:post_slug>/', views.comment_create_view, name='comment_create'),
    path('comment/<int:comment_id>/like/', views.like_comment_view, name='like_comment'),
]
