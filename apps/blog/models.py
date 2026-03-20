from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import F
from apps.core.utils import generate_slug


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='分类名称')
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:category', args=[self.slug])


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名称')
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.slug:
            return reverse('blog:tag', args=[self.slug])
        return '#'  # 返回空链接，避免报错


class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('published', '发布'),
        ('archived', '归档'),
    )

    title = models.CharField(max_length=200, verbose_name='标题')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.TextField(max_length=500, blank=True, verbose_name='摘要')
    content = models.TextField(verbose_name='内容')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts', verbose_name='作者')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts', verbose_name='分类')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name='标签')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    allow_comments = models.BooleanField(default=True, verbose_name='允许评论')
    views_count = models.PositiveIntegerField(default=0, verbose_name='浏览量')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = '文章'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['author']),  # 添加作者索引
            models.Index(fields=['slug']),    # 添加slug索引
        ]

    def save(self, *args, **kwargs):
        # 生成 slug
        if not self.slug:
            if self.title:
                self.slug = slugify(self.title)
            else:
                # 标题为空时，使用时间戳作为 slug
                from django.utils import timezone
                self.slug = f'post-{timezone.now().timestamp():.0f}'
        
        # 确保 slug 唯一
        original_slug = self.slug
        counter = 1
        while True:
            # 排除当前实例本身
            queryset = Post.objects.filter(slug=self.slug)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            if not queryset.exists():
                break
            # slug 已存在，添加数字后缀
            self.slug = f'{original_slug}-{counter}'
            counter += 1
        
        # 设置发布时间
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', args=[self.slug])

    def increase_views(self):
        """增加浏览量（使用F表达式避免并发问题）"""
        Post.objects.filter(pk=self.pk).update(views_count=F('views_count') + 1)
        # 更新当前实例的值
        self.views_count = F('views_count') + 1
        # 重新从数据库获取最新值
        self.refresh_from_db(fields=['views_count'])


class Comment(models.Model):
    REVIEW_STATUS_CHOICES = (
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    )
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='文章')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments', verbose_name='用户')
    name = models.CharField(max_length=50, blank=True, verbose_name='姓名')
    email = models.EmailField(blank=True, verbose_name='邮箱')
    content = models.TextField(verbose_name='评论内容')
    is_approved = models.BooleanField(default=False)  # 保持兼容
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending', verbose_name='审核状态')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_comments', verbose_name='审核人')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    review_note = models.TextField(blank=True, verbose_name='审核备注')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.CharField(max_length=200, blank=True, verbose_name='用户代理')
    like_count = models.PositiveIntegerField(default=0, verbose_name='点赞数')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['review_status']),
            models.Index(fields=['user']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        if self.user:
            return f'{self.user.username} 评论了 {self.post.title}'
        return f'{self.name} 评论了 {self.post.title}'
    
    @property
    def is_pending(self):
        return self.review_status == 'pending'
    
    @property
    def is_approved_status(self):
        return self.review_status == 'approved'
    
    @property
    def is_rejected(self):
        return self.review_status == 'rejected'
    
    def update_like_count(self):
        """更新点赞数"""
        self.like_count = self.likes.count()
        self.save(update_fields=['like_count'])

    def save(self, *args, **kwargs):
        # 保持 is_approved 与 review_status 的兼容性
        if self.review_status == 'approved':
            self.is_approved = True
        else:
            self.is_approved = False
        super().save(*args, **kwargs)


class CommentLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_likes', verbose_name='用户')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes', verbose_name='评论')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '评论点赞'
        verbose_name_plural = '评论点赞'
        unique_together = ['user', 'comment']

    def __str__(self):
        return f'{self.user.username} 点赞了评论'
