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
import sqlite3
import sys
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 设置 Django 设置
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# 添加项目路径
sys.path.insert(0, str(BASE_DIR))

# 延迟导入（避免 E402）
Category = Tag = Post = Comment = None
Board = Topic = Reply = None
User = Profile = None


def _setup_django():
    """初始化 Django 并导入模型。"""
    global Category, Tag, Post, Comment, Board, Topic, Reply, User, Profile

    import django

    django.setup()

    from apps.accounts.models import Profile as _Profile
    from apps.accounts.models import User as _User
    from apps.blog.models import Category as _Category
    from apps.blog.models import Comment as _Comment
    from apps.blog.models import Post as _Post
    from apps.blog.models import Tag as _Tag
    from apps.forum.models import Board as _Board
    from apps.forum.models import Reply as _Reply
    from apps.forum.models import Topic as _Topic

    Category, Tag, Post, Comment = _Category, _Tag, _Post, _Comment
    Board, Topic, Reply = _Board, _Topic, _Reply
    User, Profile = _User, _Profile


def migrate():
    _setup_django()

    print("开始迁移数据...")

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # 使用 ORM 获取真实表名（适配自定义 User 模型表名变更）
    user_table = User._meta.db_table
    profile_table = Profile._meta.db_table
    category_table = Category._meta.db_table
    tag_table = Tag._meta.db_table
    post_table = Post._meta.db_table
    _post_tags_table = "blog_post_tags"  # M2M 中间表（不通过 ORM 获取）
    comment_table = Comment._meta.db_table
    board_table = Board._meta.db_table
    topic_table = Topic._meta.db_table
    reply_table = Reply._meta.db_table

    # 1. 用户
    print("迁移用户...")
    cursor.execute(
        f"SELECT id, username, email, password, is_staff, is_active, is_superuser, date_joined, last_login FROM {user_table}"
    )
    for u in cursor.fetchall():
        User.objects.update_or_create(
            id=u[0],
            defaults={
                "username": u[1],
                "email": u[2],
                "password": u[3],
                "is_staff": u[4],
                "is_active": u[5],
                "is_superuser": u[6],
                "date_joined": u[7],
                "last_login": u[8],
            },
        )
    print(f"  用户: {cursor.execute(f'SELECT COUNT(*) FROM {user_table}').fetchone()[0]} 条")

    # 2. 用户资料
    print("迁移用户资料...")
    cursor.execute(f"SELECT id, user_id, avatar, bio, website, created_at, updated_at FROM {profile_table}")
    for p in cursor.fetchall():
        Profile.objects.update_or_create(
            id=p[0],
            defaults={
                "user_id": p[1],
                "avatar": p[2],
                "bio": p[3],
                "website": p[4],
                "created_at": p[5],
                "updated_at": p[6],
            },
        )

    # 3. 分类
    print("迁移分类...")
    cursor.execute(f"SELECT id, name, slug, created_at, updated_at FROM {category_table}")
    for c in cursor.fetchall():
        Category.objects.update_or_create(
            id=c[0],
            defaults={
                "name": c[1],
                "slug": c[2],
                "created_at": c[3],
                "updated_at": c[4],
            },
        )

    # 4. 标签
    print("迁移标签...")
    cursor.execute(f"SELECT id, name, slug, created_at, updated_at FROM {tag_table}")
    for t in cursor.fetchall():
        Tag.objects.update_or_create(
            id=t[0],
            defaults={
                "name": t[1],
                "slug": t[2],
                "created_at": t[3],
                "updated_at": t[4],
            },
        )

    # 5. 文章
    print("迁移文章...")
    cursor.execute(f"""
        SELECT id, title, slug, summary, content, status, views_count, published_at,
               created_at, updated_at, author_id, category_id, allow_comments
        FROM {post_table}
    """)
    posts = {}
    for p in cursor.fetchall():
        post = Post.objects.update_or_create(
            id=p[0],
            defaults={
                "title": p[1],
                "slug": p[2],
                "summary": p[3],
                "content": p[4],
                "status": p[5],
                "views_count": p[6],
                "published_at": p[7],
                "created_at": p[8],
                "updated_at": p[9],
                "author_id": p[10],
                "category_id": p[11],
                "allow_comments": p[12],
            },
        )[0]
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
    cursor.execute(f"""
        SELECT id, post_id, user_id, name, email, content, is_approved, review_status,
               ip_address, user_agent, like_count, created_at, updated_at
        FROM {comment_table}
    """)
    for c in cursor.fetchall():
        Comment.objects.update_or_create(
            id=c[0],
            defaults={
                "post_id": c[1],
                "user_id": c[2],
                "name": c[3],
                "email": c[4],
                "content": c[5],
                "is_approved": c[6],
                "review_status": c[7],
                "ip_address": c[8],
                "user_agent": c[9],
                "like_count": c[10],
                "created_at": c[11],
                "updated_at": c[12],
            },
        )

    # 8. 版块
    print("迁移版块...")
    cursor.execute(f"""
        SELECT id, name, slug, description, topic_count, reply_count,
               last_post_at, created_at, updated_at
        FROM {board_table}
    """)
    for b in cursor.fetchall():
        Board.objects.update_or_create(
            id=b[0],
            defaults={
                "name": b[1],
                "slug": b[2],
                "description": b[3],
                "topic_count": b[4],
                "reply_count": b[5],
                "last_post_at": b[6],
                "created_at": b[7],
                "updated_at": b[8],
            },
        )

    # 9. 主题
    print("迁移主题...")
    cursor.execute(f"""
        SELECT id, title, content, views_count, reply_count, is_pinned, is_locked,
               last_reply_at, created_at, updated_at, author_id, board_id, review_status
        FROM {topic_table}
    """)
    for t in cursor.fetchall():
        Topic.objects.update_or_create(
            id=t[0],
            defaults={
                "title": t[1],
                "content": t[2],
                "views_count": t[3],
                "reply_count": t[4],
                "is_pinned": t[5],
                "is_locked": t[6],
                "last_reply_at": t[7],
                "created_at": t[8],
                "updated_at": t[9],
                "author_id": t[10],
                "board_id": t[11],
                "review_status": t[12],
            },
        )

    # 10. 回复
    print("迁移回复...")
    cursor.execute(f"""
        SELECT id, content, like_count, is_deleted, created_at, updated_at,
               author_id, topic_id, review_status
        FROM {reply_table}
    """)
    for r in cursor.fetchall():
        Reply.objects.update_or_create(
            id=r[0],
            defaults={
                "content": r[1],
                "like_count": r[2],
                "is_deleted": r[3],
                "created_at": r[4],
                "updated_at": r[5],
                "author_id": r[6],
                "topic_id": r[7],
                "review_status": r[8],
            },
        )

    conn.close()
    print("\n迁移完成！")


if __name__ == "__main__":
    migrate()
