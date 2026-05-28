import gzip
import json
import socket
from io import BytesIO
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.blog.models import Category, Comment, Post
from apps.forum.models import Board, Reply, Topic
from apps.tools.tool_modules.http_request_tool import HTTPRequestTool, _prepare_pinned_request_target
from apps.tools.tool_modules.port_scan_tool import _resolve_public_target


class CoreTestCase(TestCase):
    def test_healthz_view(self):
        """测试健康检查视图返回200和健康检查详情"""
        # healthz路径在安装中间件的豁免列表中，不需要创建安装锁文件
        response = self.client.get(reverse("core:healthz"))
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload.get("status"), "healthy")
        self.assertIn("checks", payload)
        self.assertTrue(payload["checks"].get("database"))
        self.assertTrue(payload["checks"].get("cache"))
        self.assertIn("duration_ms", payload)
        self.assertIn("version", payload)


class APISecurityRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="api-user",
            email="api-user@example.com",
            password="pass123456",
        )
        self.category = Category.objects.create(name="api-category")
        self.post = Post.objects.create(
            title="api post",
            content="api post content",
            summary="api summary",
            author=self.user,
            category=self.category,
            status="published",
        )
        Comment.objects.create(
            post=self.post,
            user=self.user,
            content="approved account comment",
            review_status="approved",
        )
        Comment.objects.create(
            post=self.post,
            name="guest",
            email="guest@example.com",
            content="approved guest comment",
            review_status="approved",
        )
        self.board = Board.objects.create(name="api-board")
        self.topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="approved topic",
            content="approved topic content",
            review_status="approved",
        )
        Reply.objects.create(
            topic=self.topic,
            author=self.user,
            content="approved reply",
            review_status="approved",
        )
        self.pending_topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="pending topic token",
            content="pending topic content",
            review_status="pending",
        )

    def test_public_post_detail_does_not_expose_author_email(self):
        response = self.client.get(f"/api/posts/{self.post.slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("email", response.json()["author"])

    def test_public_comments_endpoint_does_not_expose_email_addresses(self):
        response = self.client.get(f"/api/posts/{self.post.slug}/comments/")

        self.assertEqual(response.status_code, 200)
        for item in response.json()["results"]:
            self.assertNotIn("email", item)
            if item.get("user"):
                self.assertNotIn("email", item["user"])

    def test_public_topic_detail_does_not_expose_author_email(self):
        response = self.client.get(f"/api/topics/{self.topic.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("email", response.json()["author"])

    def test_pending_topics_are_hidden_from_public_search(self):
        response = self.client.get("/api/search/topics/?q=pending topic token")

        self.assertEqual(response.status_code, 200)
        returned_ids = [item["id"] for item in response.json()["data"]]
        self.assertNotIn(str(self.pending_topic.id), returned_ids)

    def test_invalid_search_pagination_returns_bad_request(self):
        response = self.client.get("/api/search/posts/?q=api&page=abc")

        self.assertEqual(response.status_code, 400)

    def test_invalid_global_search_limit_returns_bad_request(self):
        response = self.client.get("/api/search/?q=api&limit=abc")

        self.assertEqual(response.status_code, 400)


class MethodSafetyRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="method-user",
            email="method-user@example.com",
            password="pass123456",
        )
        self.client.login(username="method-user", password="pass123456")

        self.category = Category.objects.create(name="method-category")
        self.post = Post.objects.create(
            title="method post",
            content="method post content",
            author=self.user,
            category=self.category,
            status="published",
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content="approved comment",
            review_status="approved",
        )

        self.board = Board.objects.create(name="method-board")
        self.topic = Topic.objects.create(
            board=self.board,
            author=self.user,
            title="method topic",
            content="method topic content",
            review_status="approved",
        )
        self.reply = Reply.objects.create(
            topic=self.topic,
            author=self.user,
            content="approved reply",
            review_status="approved",
        )

    def test_comment_like_requires_post(self):
        response = self.client.get(reverse("blog:like_comment", args=[self.comment.id]))

        self.assertEqual(response.status_code, 405)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.like_count, 0)

    def test_reply_like_requires_post(self):
        response = self.client.get(reverse("forum:like_reply", args=[self.reply.id]))

        self.assertEqual(response.status_code, 405)
        self.reply.refresh_from_db()
        self.assertEqual(self.reply.like_count, 0)


class _FakeResponse:
    def __init__(self, status=200, headers=None, reason="OK", data=b"{}"):
        self.status = status
        self.headers = headers or {}
        self.reason = reason
        self.data = data


class NetworkToolSecurityTests(SimpleTestCase):
    @patch(
        "apps.tools.tool_modules.http_request_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )
    def test_prepare_pinned_request_target_rewrites_public_domain(self, _mock_getaddrinfo):
        parsed, pinned_url, host_header, resolved_ip, error = _prepare_pinned_request_target(
            "https://example.com/api?q=1"
        )

        self.assertIsNone(error)
        self.assertEqual(parsed.hostname, "example.com")
        self.assertEqual(pinned_url, "https://93.184.216.34/api?q=1")
        self.assertEqual(host_header, "example.com")
        self.assertEqual(resolved_ip, "93.184.216.34")

    @patch(
        "apps.tools.tool_modules.http_request_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))],
    )
    def test_prepare_pinned_request_target_rejects_internal_resolution(self, _mock_getaddrinfo):
        _parsed, _pinned_url, _host_header, _resolved_ip, error = _prepare_pinned_request_target("https://example.com/")

        self.assertIsNotNone(error)
        self.assertIn("内网地址", error)

    def test_prepare_pinned_request_target_rejects_internal_literal_ip(self):
        _parsed, _pinned_url, _host_header, _resolved_ip, error = _prepare_pinned_request_target(
            "http://127.0.0.1/admin"
        )

        self.assertIsNotNone(error)
        self.assertIn("内网地址", error)

    @patch(
        "apps.tools.tool_modules.http_request_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )
    def test_send_request_uses_pinned_public_ip(self, _mock_getaddrinfo):
        tool = HTTPRequestTool()

        with patch.object(tool, "_perform_request", return_value=_FakeResponse()) as mock_perform_request:
            response_meta = tool._send_request("GET", "https://example.com/path", {}, "", "application/json", 5, False)

        self.assertEqual(response_meta["resolved_ip"], "93.184.216.34")
        self.assertEqual(mock_perform_request.call_args.args[1], "https://93.184.216.34/path")
        self.assertEqual(mock_perform_request.call_args.args[5], "example.com")
        self.assertEqual(mock_perform_request.call_args.args[6], "example.com")

    @patch(
        "apps.tools.tool_modules.http_request_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )
    def test_send_request_revalidates_redirect_targets(self, _mock_getaddrinfo):
        tool = HTTPRequestTool()
        first_response = _FakeResponse(status=302, headers={"Location": "http://127.0.0.1/admin"})

        with patch.object(tool, "_perform_request", return_value=first_response):
            with self.assertRaises(ValueError):
                tool._send_request("GET", "https://example.com/path", {}, "", "application/json", 5, True)

    @patch(
        "apps.tools.tool_modules.port_scan_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )
    def test_resolve_public_target_returns_pinned_ip(self, _mock_getaddrinfo):
        resolved_ip, error = _resolve_public_target("example.com")

        self.assertIsNone(error)
        self.assertEqual(resolved_ip, "93.184.216.34")

    @patch(
        "apps.tools.tool_modules.port_scan_tool.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))],
    )
    def test_resolve_public_target_rejects_internal_resolution(self, _mock_getaddrinfo):
        resolved_ip, error = _resolve_public_target("example.com")

        self.assertIsNone(resolved_ip)
        self.assertIn("禁止扫描", error)


class BackupRestoreTests(TestCase):
    """备份与恢复功能测试"""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="backupadmin",
            email="backupadmin@example.com",
            password="backuppass123",
        )
        self.normal_user = User.objects.create_user(
            username="backupuser",
            email="backupuser@example.com",
            password="backuppass123",
            is_staff=True,
        )
        self.category = Category.objects.create(name="backup-cat")
        self.post = Post.objects.create(
            title="backup post",
            content="backup content",
            author=self.superuser,
            category=self.category,
            status="published",
        )

    def test_backup_page_requires_login(self):
        response = self.client.get("/admin/backup/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.headers.get("Location", ""))

    def test_backup_page_requires_superuser(self):
        self.client.login(username="backupuser", password="backuppass123")
        response = self.client.get("/admin/backup/")
        self.assertEqual(response.status_code, 403)

    def test_backup_page_loads_for_superuser(self):
        self.client.login(username="backupadmin", password="backuppass123")
        response = self.client.get("/admin/backup/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "数据备份与恢复")
        self.assertContains(response, "下载备份文件")

    def test_download_backup_returns_gzip(self):
        self.client.login(username="backupadmin", password="backuppass123")
        response = self.client.get("/admin/backup/?action=download")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/gzip")
        self.assertIn("djangoblog_backup_", response["Content-Disposition"])
        self.assertIn(".json.gz", response["Content-Disposition"])

    def test_download_backup_contains_valid_json(self):
        self.client.login(username="backupadmin", password="backuppass123")
        response = self.client.get("/admin/backup/?action=download")

        decompressed = gzip.decompress(response.content)
        data = json.loads(decompressed)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        model_names = {r["model"] for r in data}
        self.assertIn("accounts.user", model_names)
        self.assertIn("blog.post", model_names)
        self.assertIn("blog.category", model_names)

    def test_restore_requires_post(self):
        self.client.login(username="backupadmin", password="backuppass123")
        response = self.client.get("/admin/restore/")
        self.assertEqual(response.status_code, 302)

    def test_restore_requires_file(self):
        self.client.login(username="backupadmin", password="backuppass123")
        response = self.client.post("/admin/restore/")
        self.assertEqual(response.status_code, 302)
        # Should redirect back with error message

    def test_restore_rejects_non_superuser(self):
        self.client.login(username="backupuser", password="backuppass123")
        response = self.client.post("/admin/restore/")
        self.assertEqual(response.status_code, 403)

    def test_full_backup_and_restore_cycle(self):
        """完整的备份→恢复流程"""
        self.client.login(username="backupadmin", password="backuppass123")

        # Step 1: download backup
        response = self.client.get("/admin/backup/?action=download")
        backup_data = response.content

        # Step 2: modify data (add new post)
        Post.objects.create(
            title="extra post",
            content="extra content",
            author=self.superuser,
            category=self.category,
            status="published",
        )
        self.assertEqual(Post.objects.count(), 2)

        # Step 3: restore original backup
        from django.core.files.uploadedfile import SimpleUploadedFile

        backup_file = SimpleUploadedFile(
            "backup.json.gz",
            backup_data,
            content_type="application/gzip",
        )
        response = self.client.post("/admin/restore/", {"backup_file": backup_file})
        self.assertEqual(response.status_code, 302)

        # Step 4: verify data restored (extra post should be gone)
        self.assertEqual(Post.objects.count(), 1)
        self.assertTrue(Post.objects.filter(title="backup post").exists())
        self.assertFalse(Post.objects.filter(title="extra post").exists())

    def test_user_natural_key(self):
        """测试 User 模型的 natural_key 方法"""
        key = self.superuser.natural_key()
        self.assertEqual(key, ("backupadmin",))
