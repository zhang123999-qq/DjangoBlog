"""创建测试数据"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from apps.blog.models import Category, Tag, Post
from apps.accounts.models import User
from django.utils import timezone

# 获取管理员用户
admin = User.objects.get(username='admin')

# 创建分类
cat, created = Category.objects.get_or_create(
    name='技术分享',
    defaults={'slug': 'tech-share'}
)
print(f'Category: {cat.name} ({"created" if created else "exists"})')

# 创建标签
tag1, _ = Tag.objects.get_or_create(name='Python', defaults={'slug': 'python'})
tag2, _ = Tag.objects.get_or_create(name='Django', defaults={'slug': 'django'})
print(f'Tags: {tag1.name}, {tag2.name}')

# 创建文章
post, created = Post.objects.get_or_create(
    title='Django 4.2 新特性详解',
    defaults={
        'slug': 'django-42-new-features',
        'summary': '本文详细介绍 Django 4.2 LTS 版本的新特性和改进。',
        'content': '''# Django 4.2 新特性详解

Django 4.2 LTS 于 2023 年 4 月发布，这是 Django 的长期支持版本，将提供 3 年的安全更新。

## 主要新特性

### 1. 异步视图和中间件增强

Django 4.2 对异步支持进行了重大改进，支持 async/await 语法。

### 2. 数据库连接池

新增 CONN_MAX_AGE 和 CONN_HEALTH_CHECKS 配置，支持数据库连接池。

### 3. 覆盖模型字段

新的 Field.db_returning 参数允许在插入时返回数据库生成的字段值。

## 总结

Django 4.2 是一个重要的 LTS 版本，建议所有项目尽快升级！''',
        'author': admin,
        'category': cat,
        'status': 'published',
        'allow_comments': True,
        'published_at': timezone.now(),
    }
)

if created:
    post.tags.add(tag1, tag2)
    print(f'Post created: {post.title}')
else:
    print(f'Post exists: {post.title}')

print(f'\nTotal: {Category.objects.count()} categories, {Tag.objects.count()} tags, {Post.objects.count()} posts')
