"""
初始化默认数据的管理命令
"""
from django.core.management.base import BaseCommand
from apps.forum.models import Board
from apps.blog.models import Category, Tag


class Command(BaseCommand):
    help = '初始化默认数据：板块、分类、标签'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化默认数据...')
        
        # 创建默认论坛板块 (8个)
        boards_data = [
            {
                'name': '技术交流',
                'slug': 'tech',
                'description': '分享技术文章、开发经验、学习心得',
            },
            {
                'name': '问题求助',
                'slug': 'help',
                'description': '遇到问题？在这里寻求帮助',
            },
            {
                'name': '资源分享',
                'slug': 'resources',
                'description': '分享有价值的资源、工具、教程',
            },
            {
                'name': '灌水闲聊',
                'slug': 'chat',
                'description': '轻松聊天，分享生活趣事',
            },
            {
                'name': 'Python编程',
                'slug': 'python',
                'description': 'Python语言讨论、代码分享',
            },
            {
                'name': 'Web开发',
                'slug': 'web',
                'description': '前端后端开发讨论',
            },
            {
                'name': '人工智能',
                'slug': 'ai',
                'description': 'AI、机器学习、深度学习',
            },
            {
                'name': '数据库',
                'slug': 'database',
                'description': 'MySQL、Redis、MongoDB等数据库讨论',
            },
        ]
        
        boards_created = 0
        for board_data in boards_data:
            board, created = Board.objects.get_or_create(
                name=board_data['name'],
                defaults=board_data
            )
            if created:
                boards_created += 1
                self.stdout.write(f'  创建板块: {board.name}')
        
        self.stdout.write(f'论坛板块: 新建 {boards_created} 个')
        
        # 创建默认博客分类 (6个)
        categories_data = [
            {'name': '技术笔记', 'slug': 'tech-notes'},
            {'name': '项目实战', 'slug': 'projects'},
            {'name': '工具推荐', 'slug': 'tools'},
            {'name': '生活随笔', 'slug': 'life'},
            {'name': '编程学习', 'slug': 'learning'},
            {'name': '源码解析', 'slug': 'source-code'},
        ]
        
        categories_created = 0
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                categories_created += 1
                self.stdout.write(f'  创建分类: {category.name}')
        
        self.stdout.write(f'博客分类: 新建 {categories_created} 个')
        
        # 创建默认标签 (6个)
        tags_data = [
            {'name': 'Python', 'slug': 'python'},
            {'name': 'Django', 'slug': 'django'},
            {'name': 'JavaScript', 'slug': 'javascript'},
            {'name': '前端开发', 'slug': 'frontend'},
            {'name': '后端开发', 'slug': 'backend'},
            {'name': '网络安全', 'slug': 'security'},
        ]
        
        tags_created = 0
        for tag_data in tags_data:
            try:
                tag, created = Tag.objects.get_or_create(
                    slug=tag_data['slug'],
                    defaults=tag_data
                )
                if created:
                    tags_created += 1
                    self.stdout.write(f'  创建标签: {tag.name}')
            except Exception:
                # 如果slug冲突，尝试用name查找
                tag, created = Tag.objects.get_or_create(
                    name=tag_data['name'],
                    defaults={'slug': tag_data['slug']}
                )
                if created:
                    tags_created += 1
                    self.stdout.write(f'  创建标签: {tag.name}')
        
        self.stdout.write(f'博客标签: 新建 {tags_created} 个')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n初始化完成！\n'
                f'  板块: {boards_created} 个\n'
                f'  分类: {categories_created} 个\n'
                f'  标签: {tags_created} 个'
            )
        )
