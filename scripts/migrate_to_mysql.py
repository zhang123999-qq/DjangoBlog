#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据迁移脚本：SQLite -> MySQL

用法: python scripts/migrate_to_mysql.py

前置条件:
1. 安装并启动 MySQL
2. 创建目标数据库
3. 配置 .env 中的 MySQL 连接信息
"""
import os
import sys
import sqlite3
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 设置 Django 设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# 添加项目路径
sys.path.insert(0, str(BASE_DIR))

import django
django.setup()

from apps.blog.models import Category, Tag, Post, Comment
from apps.forum.models import Board, Topic, Reply
from apps.accounts.models import User, Profile

def migrate():
    print("开始迁移数据...")

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # 1. 用户
    print("迁移用户...")
    cursor.execute("SELECT id, username, email, password, is_staff, is_active, is_superuser, date_joined, last_login FROM accounts_user")
    for u in cursor.fetchall():
        User.objects.update_or_create(id=u[0], defaults={
            'username': u[1], 'email': u[2], 'password': u[3],
            'is_staff': u[4], 'is_active': u[5], 'is_superuser': u[6],
            'date_joined': u[7], 'last_login': u[8]
        })
    print(f"  用户: {cursor.execute('SELECT COUNT(*) FROM accounts_user').fetchone()[0]} 条")

    # 2. 用户资料
    print("迁移用户资料...")
    cursor.execute("SELECT id, user_id, avatar, bio, website, created_at, updated_at FROM accounts_profile")
    for p in cursor.fetchall():
        Profile.objects.update_or_create(id=p[0], defaults={
            'user_id': p[1], 'avatar': p[2], 'bio': p[3],
            'website': p[4], 'created_at': p[5], 'updated_at': p[6]
        })

    # 3. 分类
    print("迁移分类...")
    cursor.execute("SELECT id, name, slug, created_at, updated_at FROM blog_category")
    for c in cursor.fetchall():
        Category.objects.update_or_create(id=c[0], defaults={
            'name': c[1], 'slug': c[2], 'created_at': c[3], 'updated_at': c[4]
        })

    # 4. 标签
    print("迁移标签...")
    cursor.execute("SELECT id, name, slug, created_at, updated_at FROM blog_tag")
    for t in cursor.fetchall():
        Tag.objects.update_or_create(id=t[0], defaults={
            'name': t[1], 'slug': t[2], 'created_at': t[3], 'updated_at': t[4]
        })

    # 5. 文章
    print("迁移文章...")
    cursor.execute("""
        SELECT id, title, slug, summary, content, status, views_count, published_at,
               created_at, updated_at, author_id, category_id, allow_comments
        FROM blog_post
    """)
    posts = {}
    for p in cursor.fetchall():
        post = Post.objects.update_or_create(id=p[0], defaults={
            'title': p[1], 'slug': p[2], 'summary': p[3], 'content': p[4],
            'status': p[5], 'views_count': p[6], 'published_at': p[7],
            'created_at': p[8], 'updated_at': p[9], 'author_id': p[10],
            'category_id': p[11], 'allow_comments': p[12]
        })[0]
        posts[p[0]] = post
    print(f"  文章: {len(posts)} 条")

    # 6. 文章标签
    print("迁移文章标签...")
    cursor.execute("SELECT post_id, tag_id FROM blog_post_tags")
    for pt in cursor.fetchall():
        if pt[0] in posts:
            posts[pt[0]].tags.add(pt[1])

    # 7. 评论
    print("迁移评论...")
    cursor.execute("""
        SELECT id, post_id, user_id, name, email, content, is_approved, review_status,
               ip_address, user_agent, like_count, created_at, updated_at
        FROM blog_comment
    """)
    for c in cursor.fetchall():
        Comment.objects.update_or_create(id=c[0], defaults={
            'post_id': c[1], 'user_id': c[2], 'name': c[3], 'email': c[4],
            'content': c[5], 'is_approved': c[6], 'review_status': c[7],
            'ip_address': c[8], 'user_agent': c[9], 'like_count': c[10],
            'created_at': c[11], 'updated_at': c[12]
        })

    # 8. 版块（没有 order 字段）
    print("迁移版块...")
    cursor.execute("""
        SELECT id, name, slug, description, topic_count, reply_count,
               last_post_at, created_at, updated_at
        FROM forum_board
    """)
    for b in cursor.fetchall():
        Board.objects.update_or_create(id=b[0], defaults={
            'name': b[1], 'slug': b[2], 'description': b[3],
            'topic_count': b[4], 'reply_count': b[5], 'last_post_at': b[6],
            'created_at': b[7], 'updated_at': b[8]
        })

    # 9. 主题
    print("迁移主题...")
    cursor.execute("""
        SELECT id, title, content, views_count, reply_count, is_pinned, is_locked,
               last_reply_at, created_at, updated_at, author_id, board_id, review_status
        FROM forum_topic
    """)
    for t in cursor.fetchall():
        Topic.objects.update_or_create(id=t[0], defaults={
            'title': t[1], 'content': t[2], 'views_count': t[3],
            'reply_count': t[4], 'is_pinned': t[5], 'is_locked': t[6],
            'last_reply_at': t[7], 'created_at': t[8], 'updated_at': t[9],
            'author_id': t[10], 'board_id': t[11], 'review_status': t[12]
        })

    # 10. 回复
    print("迁移回复...")
    cursor.execute("""
        SELECT id, content, like_count, is_deleted, created_at, updated_at,
               author_id, topic_id, review_status
        FROM forum_reply
    """)
    for r in cursor.fetchall():
        Reply.objects.update_or_create(id=r[0], defaults={
            'content': r[1], 'like_count': r[2], 'is_deleted': r[3],
            'created_at': r[4], 'updated_at': r[5], 'author_id': r[6],
            'topic_id': r[7], 'review_status': r[8]
        })

    conn.close()
    print("\n迁移完成！")

if __name__ == '__main__':
    migrate()
