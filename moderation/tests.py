"""Moderation test entrypoints and targeted regression tests."""

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.blog.models import Category, Comment, Post
from tests.test_moderation_smoke import *  # noqa: F401,F403


class ModerationViewTests(TestCase):
    def setUp(self):
        self.moderator = User.objects.create_user(
            username="moderator",
            email="moderator@example.com",
            password="pass123456",
            is_staff=True,
        )
        self.author = User.objects.create_user(
            username="author",
            email="author@example.com",
            password="pass123456",
        )
        self.category = Category.objects.create(name="moderation-category")
        self.post = Post.objects.create(
            title="moderation post",
            content="moderation post content",
            author=self.author,
            category=self.category,
            status="published",
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.author,
            content="pending comment awaiting review",
            review_status="pending",
        )
        self.approve_url = reverse("moderation:approve", args=["comment", self.comment.id])

    def test_approve_requires_post(self):
        self.client.login(username="moderator", password="pass123456")

        response = self.client.get(self.approve_url)

        self.assertEqual(response.status_code, 405)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.review_status, "pending")

    def test_post_approve_changes_review_status(self):
        self.client.login(username="moderator", password="pass123456")

        response = self.client.post(self.approve_url, follow=False)

        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.review_status, "approved")
