from django.db import models
from django.conf import settings
from django.urls import reverse
from django.db.models import F
from apps.core.utils import generate_slug


class Board(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    topic_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    last_post_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "版块"
        verbose_name_plural = "版块"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.slug:
            return reverse("forum:topic_list", args=[self.slug])
        return "#"

    def update_counts(self):
        """更新版块的主题数和回复数"""
        from django.db.models import Sum

        # 只统计审核通过的主题
        approved_topics = self.topics.filter(review_status="approved")
        self.topic_count = approved_topics.count()
        # 使用聚合查询计算回复数，避免N+1查询
        reply_count_result = approved_topics.aggregate(total_replies=Sum("reply_count"))
        self.reply_count = reply_count_result["total_replies"] or 0
        last_topic = approved_topics.order_by("-last_reply_at").first()
        if last_topic:
            self.last_post_at = last_topic.last_reply_at
        else:
            self.last_post_at = None
        self.save()


class Topic(models.Model):
    REVIEW_STATUS_CHOICES = (
        ("pending", "待审核"),
        ("approved", "已通过"),
        ("rejected", "已拒绝"),
    )

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="topics")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    content = models.TextField()
    views_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default="pending")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_topics",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    last_reply_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "主题"
        verbose_name_plural = "主题"
        ordering = ["-is_pinned", "-last_reply_at", "-created_at"]
        indexes = [
            models.Index(fields=["board", "-last_reply_at"]),
            models.Index(fields=["author"]),
            models.Index(fields=["review_status"]),
            models.Index(fields=["is_pinned"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("forum:topic_detail", args=[self.board.slug, self.id])

    def increase_views(self):
        """增加浏览量"""
        Topic.objects.filter(pk=self.pk).update(views_count=F("views_count") + 1)
        # 更新当前实例的值（纯整数递增，用于当前请求中的显示）
        if isinstance(self.views_count, int):
            self.views_count += 1

    def update_reply_count(self):
        """更新回复数和最后回复时间"""
        # 只统计审核通过且未删除的回复
        approved_replies = self.replies.filter(is_deleted=False, review_status="approved")
        self.reply_count = approved_replies.count()
        last_reply = approved_replies.order_by("-created_at").first()
        if last_reply:
            self.last_reply_at = last_reply.created_at
        else:
            self.last_reply_at = None
        self.save()
        # 更新版块的统计信息
        self.board.update_counts()

    @property
    def is_pending(self):
        return self.review_status == "pending"

    @property
    def is_approved(self):
        return self.review_status == "approved"

    @property
    def is_rejected(self):
        return self.review_status == "rejected"


class Reply(models.Model):
    REVIEW_STATUS_CHOICES = (
        ("pending", "待审核"),
        ("approved", "已通过"),
        ("rejected", "已拒绝"),
    )

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="replies")
    content = models.TextField()
    like_count = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default="pending")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_replies",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "回复"
        verbose_name_plural = "回复"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["topic", "-created_at"]),
            models.Index(fields=["author"]),
            models.Index(fields=["review_status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.author.username} 回复了 {self.topic.title}"

    def update_like_count(self):
        """更新点赞数（避免 save 覆盖其他字段）"""
        actual_count = self.likes.count()
        self.__class__.objects.filter(pk=self.pk).update(like_count=actual_count)
        self.like_count = actual_count

    @property
    def is_pending(self):
        return self.review_status == "pending"

    @property
    def is_approved(self):
        return self.review_status == "approved"

    @property
    def is_rejected(self):
        return self.review_status == "rejected"


class ReplyLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reply_likes")
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "回复点赞"
        verbose_name_plural = "回复点赞"
        unique_together = ["user", "reply"]

    def __str__(self):
        return f"{self.user.username} 点赞了回复"
