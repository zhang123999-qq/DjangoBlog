from django.urls import path
from . import views

app_name = "forum"

urlpatterns = [
    path("", views.BoardListView.as_view(), name="board_list"),
    path("board/<slug:board_slug>/", views.TopicListView.as_view(), name="topic_list"),
    path("board/<slug:board_slug>/topic/<int:topic_id>/", views.TopicDetailView.as_view(), name="topic_detail"),
    path("board/<slug:board_slug>/topic/create/", views.topic_create_view, name="topic_create"),
    path("board/<slug:board_slug>/topic/<int:topic_id>/reply/", views.reply_create_view, name="reply_create"),
    path("reply/<int:reply_id>/like/", views.like_reply_view, name="like_reply"),
]
