"""
自定义管理后台配置 - 优化版
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from apps.accounts.models import User, Profile
from apps.blog.models import Category, Tag, Post, Comment, CommentLike
from apps.forum.models import Board, Topic, Reply, ReplyLike
from moderation.models import SensitiveWord
from apps.core.models import SiteConfig
from apps.tools.registry import tool_registry


# 自定义 AdminSite
class DjangoBlogAdminSite(admin.AdminSite):
    site_header = 'DjangoBlog 管理后台'
    site_title = 'DjangoBlog Admin'
    index_title = '仪表盘'
    
    # 使用科技风格模板
    index_template = 'admin/index_tech.html'
    app_index_template = 'admin/app_index_tech.html'
    login_template = 'admin/login_tech.html'
    
    def index(self, request, extra_context=None):
        """自定义首页，添加统计数据"""
        import sys
 import platform
 from django.utils import timezone
 from django.conf import settings
        from apps.accounts.models import User
        from apps.blog.models import Post, Comment
        from apps.forum.models import Topic, Reply
        from apps.tools.registry import tool_registry
        
        extra_context = extra_context or {}
        
        # 工具统计
        tools = tool_registry.get_all_tools()
        tool_count = len(tools)
        
        # 系统信息
        db_backend = settings.DATABASES['default']['ENGINE'].split('.')[-1]
        if db_backend == 'mysql':
            db_engine_display = 'MySQL'
        elif db_backend == 'sqlite3':
            db_engine_display = 'SQLite'
        elif db_backend == 'postgresql':
            db_engine_display = 'PostgreSQL'
        else:
            db_engine_display = db_backend.upper()
        
        # 数据库版本
        db_version = ''
        try:
            with settings.DATABASES['default'] as db_config:
                if 'mysql' in db_config.get('ENGINE', ''):
                    import pymysql
                    conn = pymysql.connect(
                        host=db_config.get('HOST', 'localhost'),
                        port=int(db_config.get('PORT', 3306)),
                        user=db_config.get('USER', ''),
                        password=db_config.get('PASSWORD', ''),
                        database=db_config.get('NAME', ''),
                    )
                    cursor = conn.cursor()
                    cursor.execute('SELECT VERSION()')
                    db_version = cursor.fetchone()[0]
                    conn.close()
                elif 'sqlite3' in db_config.get('ENGINE', ''):
                    import sqlite3
                    db_version = '3.x'
        except:
            pass
        
        # Redis 信息
        redis_info = ''
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
            info = r.info()
            redis_info = f"Redis {info.get('redis_version', 'Unknown')}"
        except:
            redis_info = '未启用'
        
        extra_context.update({
            # 系统信息
            'django_version': __import__('django').VERSION,
            'django_version_str': '.'.join(map(str, __import__('django').VERSION[:2])),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'python_version_full': platform.python_version(),
            'db_engine': db_engine_display,
            'db_version': db_version,
            'redis_info': redis_info,
            'server_time': timezone.now(),
            'os_info': f"{platform.system()} {platform.release()}",
            
            # 业务统计
            'user_count': User.objects.count(),
            'post_count': Post.objects.filter(status='published').count(),
            'topic_count': Topic.objects.count(),
            'comment_count': Comment.objects.count() + Reply.objects.count(),
            'tool_count': tool_count,
            'category_count': Category.objects.count(),
            'tag_count': Tag.objects.count(),
            'board_count': Board.objects.count(),
            'tools_list': tools[:10],
            'tools_count': tool_count,
        })
        
        # 今日统计
        today = datetime.now().date()
        extra_context['today_users'] = User.objects.filter(date_joined__date=today).count()
        extra_context['today_posts'] = Post.objects.filter(created_at__date=today).count()
        extra_context['today_comments'] = Comment.objects.filter(created_at__date=today).count()
        
        # 待审核
        extra_context['pending_comments'] = Comment.objects.filter(review_status='pending').count()
        extra_context['pending_replies'] = Reply.objects.filter(review_status='pending').count()
        extra_context['pending_topics'] = Topic.objects.filter(review_status='pending').count()
        
        # 总浏览量
        total_views = Post.objects.aggregate(total=Sum('views_count'))['total'] or 0
        extra_context['total_views'] = total_views
        
        # 最近7天数据（用于图表）
        week_ago = datetime.now() - timedelta(days=7)
        week_data = []
        for i in range(7):
            day = (datetime.now() - timedelta(days=6-i)).date()
            day_posts = Post.objects.filter(created_at__date=day).count()
            day_comments = Comment.objects.filter(created_at__date=day).count()
            week_data.append({
                'date': day.strftime('%m-%d'),
                'posts': day_posts,
                'comments': day_comments
            })
        extra_context['week_data'] = week_data
        
        return super().index(request, extra_context)
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        return urls


admin_site = DjangoBlogAdminSite(name='admin')

# 重新注册默认模型
from django.contrib.auth.models import Group
from django.contrib.admin.sites import site

# 取消默认注册
for model, model_admin in list(site._registry.items()):
    site.unregister(model)


# ========== 用户管理 ==========
@admin.register(User, site=admin_site)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'nickname', 'is_staff', 'is_active', 'date_joined', 'user_actions']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'nickname']
    ordering = ['-date_joined']
    actions = ['activate_users', 'deactivate_users', 'reset_passwords']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('username', 'email', 'nickname', 'password')
        }),
        ('权限设置', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('重要日期', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    def user_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">查看资料</a>',
            reverse('admin:accounts_profile_change', args=[obj.profile.id])
        )
    user_actions.short_description = '操作'
    
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'成功激活 {count} 个用户')
    activate_users.short_description = '激活所选用户'
    
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'成功禁用 {count} 个用户')
    deactivate_users.short_description = '禁用所选用户'
    
    def reset_passwords(self, request, queryset):
        # 这里的密码重置需要特殊处理
        count = queryset.count()
        self.message_user(request, f'已选择 {count} 个用户进行密码重置（需要手动重置）')
    reset_passwords.short_description = '重置所选用户密码'


@admin.register(Profile, site=admin_site)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio', 'website', 'created_at']
    search_fields = ['user__username', 'user__email']
    list_filter = ['created_at']


# ========== 博客管理 ==========
@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    actions = ['delete_selected']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = '文章数'


@admin.register(Tag, site=admin_site)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    actions = ['delete_selected']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = '文章数'


@admin.register(Post, site=admin_site)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'views_count', 'allow_comments', 'published_at', 'post_actions']
    list_filter = ['status', 'category', 'allow_comments', 'published_at', 'author']
    search_fields = ['title', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    date_hierarchy = 'published_at'
    actions = ['publish_posts', 'unpublish_posts', 'delete_selected']
    
    fieldsets = (
        ('文章内容', {
            'fields': ('title', 'slug', 'summary', 'content', 'author')
        }),
        ('分类标签', {
            'fields': ('category', 'tags')
        }),
        ('发布设置', {
            'fields': ('status', 'allow_comments', 'published_at')
        }),
    )
    
    def post_actions(self, obj):
        if obj.status == 'published':
            return format_html(
                '<a class="button" href="{}" target="_blank">查看文章</a>',
                f'/blog/{obj.slug}/'
            )
        return '-'
    post_actions.short_description = '操作'
    
    def publish_posts(self, request, queryset):
        count = queryset.update(status='published')
        self.message_user(request, f'成功发布 {count} 篇文章')
    publish_posts.short_description = '发布所选文章'
    
    def unpublish_posts(self, request, queryset):
        count = queryset.update(status='draft')
        self.message_user(request, f'成功取消发布 {count} 篇文章')
    unpublish_posts.short_description = '取消发布所选文章'


@admin.register(Comment, site=admin_site)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'post', 'content_short', 'review_status', 'like_count', 'created_at']
    list_filter = ['review_status', 'created_at']
    search_fields = ['content', 'user__username', 'post__title']
    actions = ['approve_comments', 'reject_comments', 'delete_selected']
    list_editable = ['review_status']
    
    def user_info(self, obj):
        if obj.user:
            return obj.user.username
        return f'{obj.name} ({obj.email})'
    user_info.short_description = '评论者'
    
    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = '内容'
    
    def approve_comments(self, request, queryset):
        count = queryset.update(review_status='approved')
        self.message_user(request, f'成功审核通过 {count} 条评论')
    approve_comments.short_description = '审核通过所选评论'
    
    def reject_comments(self, request, queryset):
        count = queryset.update(review_status='rejected')
        self.message_user(request, f'成功拒绝 {count} 条评论')
    reject_comments.short_description = '拒绝所选评论'


# ========== 论坛管理 ==========
@admin.register(Board, site=admin_site)
class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description_short', 'topic_count', 'reply_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    actions = ['delete_selected']
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = '描述'


@admin.register(Topic, site=admin_site)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'board', 'is_pinned', 'is_locked', 'views_count', 'reply_count', 'created_at']
    list_filter = ['is_pinned', 'is_locked', 'board', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    actions = ['pin_topics', 'unpin_topics', 'lock_topics', 'unlock_topics', 'delete_selected']
    list_editable = ['is_pinned', 'is_locked']
    
    def pin_topics(self, request, queryset):
        count = queryset.update(is_pinned=True)
        self.message_user(request, f'成功置顶 {count} 个主题')
    pin_topics.short_description = '置顶所选主题'
    
    def unpin_topics(self, request, queryset):
        count = queryset.update(is_pinned=False)
        self.message_user(request, f'成功取消置顶 {count} 个主题')
    unpin_topics.short_description = '取消置顶所选主题'
    
    def lock_topics(self, request, queryset):
        count = queryset.update(is_locked=True)
        self.message_user(request, f'成功锁定 {count} 个主题')
    lock_topics.short_description = '锁定所选主题'
    
    def unlock_topics(self, request, queryset):
        count = queryset.update(is_locked=False)
        self.message_user(request, f'成功解锁 {count} 个主题')
    unlock_topics.short_description = '解锁所选主题'


@admin.register(Reply, site=admin_site)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['author', 'topic', 'content_short', 'review_status', 'like_count', 'created_at']
    list_filter = ['created_at', 'review_status']
    search_fields = ['content', 'author__username', 'topic__title']
    actions = ['approve_replies', 'reject_replies', 'delete_selected']
    list_editable = ['review_status']
    
    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = '内容'
    
    def approve_replies(self, request, queryset):
        count = queryset.update(review_status='approved')
        self.message_user(request, f'成功审核通过 {count} 条回复')
    approve_replies.short_description = '审核通过所选回复'
    
    def reject_replies(self, request, queryset):
        count = queryset.update(review_status='rejected')
        self.message_user(request, f'成功拒绝 {count} 条回复')
    reject_replies.short_description = '拒绝所选回复'


# ========== 内容审核 ==========
@admin.register(SensitiveWord, site=admin_site)
class SensitiveWordAdmin(admin.ModelAdmin):
    list_display = ['word', 'category', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['word']
    list_editable = ['is_active', 'category']
    actions = ['activate_words', 'deactivate_words', 'delete_selected']
    
    def activate_words(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'成功启用 {count} 个敏感词')
    activate_words.short_description = '启用所选敏感词'
    
    def deactivate_words(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'成功禁用 {count} 个敏感词')
    deactivate_words.short_description = '禁用所选敏感词'


# ========== 网站配置 ==========
@admin.register(SiteConfig, site=admin_site)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'is_installed', 'allow_registration', 'created_at']
    fieldsets = (
        ('网站信息', {
            'fields': ('site_name', 'site_title', 'site_description', 'logo')
        }),
        ('系统设置', {
            'fields': ('is_installed', 'allow_registration')
        }),
    )

    def has_add_permission(self, request):
        # 只允许一条配置
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)


# 注册 Group 和 Site
from django.contrib.sites.models import Site

admin_site.register(Group)

@admin.register(Site, site=admin_site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['domain', 'name']
    search_fields = ['domain', 'name']
