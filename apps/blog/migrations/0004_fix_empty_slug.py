from django.db import migrations
from django.utils.text import slugify
from django.utils import timezone


def fix_empty_slug(apps, schema_editor):
    """修复空 slug 数据"""
    Post = apps.get_model('blog', 'Post')
    # 查找所有 slug 为空或 None 的文章
    posts = Post.objects.filter(slug__isnull=True) | Post.objects.filter(slug='')
    
    for post in posts:
        # 生成 slug
        if post.title:
            post.slug = slugify(post.title)
        else:
            # 标题为空时，使用时间戳作为 slug
            post.slug = f'post-{timezone.now().timestamp():.0f}'
        
        # 确保 slug 唯一
        original_slug = post.slug
        counter = 1
        while True:
            # 排除当前实例本身
            queryset = Post.objects.filter(slug=post.slug)
            if post.pk:
                queryset = queryset.exclude(pk=post.pk)
            if not queryset.exists():
                break
            # slug 已存在，添加数字后缀
            post.slug = f'{original_slug}-{counter}'
            counter += 1
        
        post.save()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_comment_like_count_commentlike'),
    ]

    operations = [
        migrations.RunPython(fix_empty_slug),
    ]
