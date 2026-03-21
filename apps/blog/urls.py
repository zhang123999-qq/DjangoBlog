from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # 文章列表和详情
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:category_slug>/', views.PostListView.as_view(), name='category'),
    path('tag/<slug:tag_slug>/', views.PostListView.as_view(), name='tag'),
    
    # 文章编辑（需要登录）
    path('create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('post/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('my-posts/', views.my_posts, name='my_posts'),
    path('drafts/', views.post_draft_list, name='drafts'),
    
    # 评论
    path('comment/<slug:post_slug>/', views.comment_create_view, name='comment_create'),
    path('comment/<int:comment_id>/like/', views.like_comment_view, name='like_comment'),
]
