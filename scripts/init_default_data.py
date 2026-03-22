#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化默认数据脚本

用法: python scripts/init_default_data.py

功能:
- 创建默认论坛板块 (8个)
- 创建默认博客分类 (6个)
- 创建默认标签 (6个)
"""
import os
import sys
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 添加项目路径
sys.path.insert(0, str(BASE_DIR))

# 设置 Django 设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# 初始化 Django
import django
django.setup()

# 导入模型
from apps.forum.models import Board
from apps.blog.models import Category, Tag


def init_boards():
    """创建默认论坛板块"""
    print('\n[论坛板块]')
    
    boards_data = [
        {'name': '技术交流', 'slug': 'tech', 'description': '分享技术文章、开发经验、学习心得'},
        {'name': '问题求助', 'slug': 'help', 'description': '遇到问题？在这里寻求帮助'},
        {'name': '资源分享', 'slug': 'resources', 'description': '分享有价值的资源、工具、教程'},
        {'name': '灌水闲聊', 'slug': 'chat', 'description': '轻松聊天，分享生活趣事'},
        {'name': 'Python编程', 'slug': 'python', 'description': 'Python语言讨论、代码分享'},
        {'name': 'Web开发', 'slug': 'web', 'description': '前端后端开发讨论'},
        {'name': '人工智能', 'slug': 'ai', 'description': 'AI、机器学习、深度学习'},
        {'name': '数据库', 'slug': 'database', 'description': 'MySQL、Redis、MongoDB等数据库讨论'},
    ]
    
    created = 0
    for data in boards_data:
        board, is_created = Board.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        if is_created:
            created += 1
            print(f'  + {board.name}')
    
    print(f'  新建: {created} 个，总计: {Board.objects.count()} 个')
    return created


def init_categories():
    """创建默认博客分类"""
    print('\n[博客分类]')
    
    categories_data = [
        {'name': '技术笔记', 'slug': 'tech-notes'},
        {'name': '项目实战', 'slug': 'projects'},
        {'name': '工具推荐', 'slug': 'tools'},
        {'name': '生活随笔', 'slug': 'life'},
        {'name': '编程学习', 'slug': 'learning'},
        {'name': '源码解析', 'slug': 'source-code'},
    ]
    
    created = 0
    for data in categories_data:
        category, is_created = Category.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        if is_created:
            created += 1
            print(f'  + {category.name}')
    
    print(f'  新建: {created} 个，总计: {Category.objects.count()} 个')
    return created


def init_tags():
    """创建默认标签"""
    print('\n[博客标签]')
    
    tags_data = [
        {'name': 'Python', 'slug': 'python'},
        {'name': 'Django', 'slug': 'django'},
        {'name': 'JavaScript', 'slug': 'javascript'},
        {'name': '前端开发', 'slug': 'frontend'},
        {'name': '后端开发', 'slug': 'backend'},
        {'name': '网络安全', 'slug': 'security'},
    ]
    
    created = 0
    for data in tags_data:
        try:
            tag, is_created = Tag.objects.get_or_create(
                slug=data['slug'],
                defaults=data
            )
            if is_created:
                created += 1
                print(f'  + {tag.name}')
        except Exception:
            tag, is_created = Tag.objects.get_or_create(
                name=data['name'],
                defaults={'slug': data['slug']}
            )
            if is_created:
                created += 1
                print(f'  + {tag.name}')
    
    print(f'  新建: {created} 个，总计: {Tag.objects.count()} 个')
    return created


def main():
    """主函数"""
    print('='*50)
    print('初始化默认数据')
    print('='*50)
    
    boards = init_boards()
    categories = init_categories()
    tags = init_tags()
    
    print('\n' + '='*50)
    print(f'完成！新建: {boards + categories + tags} 项')
    print('='*50)


if __name__ == '__main__':
    main()
