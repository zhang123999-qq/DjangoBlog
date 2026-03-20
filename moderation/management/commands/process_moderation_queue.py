from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from apps.blog.models import Comment
from apps.forum.models import Topic, Reply
from moderation.services import create_moderation_reminder, auto_approve_instance
from moderation.utils import check_sensitive_content


class Command(BaseCommand):
    """
    处理审核队列的命令
    - 查找超过 6 小时未审核的 pending 内容，生成提醒
    - 查找超过 24 小时未审核且无敏感词的 pending 内容，自动审核通过
    """
    help = '处理审核队列，生成提醒和自动审核'

    def handle(self, *args, **kwargs):
        self.stdout.write('开始处理审核队列...')
        
        # 获取当前时间
        now = timezone.now()
        
        # 处理评论
        self.process_comments(now)
        
        # 处理主题
        self.process_topics(now)
        
        # 处理回复
        self.process_replies(now)
        
        self.stdout.write('审核队列处理完成')
    
    def process_comments(self, now):
        """处理评论审核"""
        # 查找超过 6 小时未审核的评论
        six_hours_ago = now - timezone.timedelta(hours=6)
        pending_comments_6h = Comment.objects.filter(
            review_status='pending',
            created_at__lt=six_hours_ago
        )
        
        for comment in pending_comments_6h:
            # 生成提醒
            create_moderation_reminder('comment', comment.id)
            self.stdout.write(f'为评论 {comment.id} 生成审核提醒')
        
        # 查找超过 24 小时未审核的评论
        twenty_four_hours_ago = now - timezone.timedelta(hours=24)
        pending_comments_24h = Comment.objects.filter(
            review_status='pending',
            created_at__lt=twenty_four_hours_ago
        )
        
        for comment in pending_comments_24h:
            # 检查是否包含敏感词
            has_sensitive, _ = check_sensitive_content(comment.content)
            if not has_sensitive:
                # 自动审核通过
                auto_approve_instance(comment, '系统自动审核通过')
                self.stdout.write(f'评论 {comment.id} 自动审核通过')
    
    def process_topics(self, now):
        """处理主题审核"""
        # 查找超过 6 小时未审核的主题
        six_hours_ago = now - timezone.timedelta(hours=6)
        pending_topics_6h = Topic.objects.filter(
            review_status='pending',
            created_at__lt=six_hours_ago
        )
        
        for topic in pending_topics_6h:
            # 生成提醒
            create_moderation_reminder('topic', topic.id)
            self.stdout.write(f'为主题 {topic.id} 生成审核提醒')
        
        # 查找超过 24 小时未审核的主题
        twenty_four_hours_ago = now - timezone.timedelta(hours=24)
        pending_topics_24h = Topic.objects.filter(
            review_status='pending',
            created_at__lt=twenty_four_hours_ago
        )
        
        for topic in pending_topics_24h:
            # 检查是否包含敏感词
            content = f"{topic.title} {topic.content}"
            has_sensitive, _ = check_sensitive_content(content)
            if not has_sensitive:
                # 自动审核通过
                auto_approve_instance(topic, '系统自动审核通过')
                self.stdout.write(f'主题 {topic.id} 自动审核通过')
    
    def process_replies(self, now):
        """处理回复审核"""
        # 查找超过 6 小时未审核的回复
        six_hours_ago = now - timezone.timedelta(hours=6)
        pending_replies_6h = Reply.objects.filter(
            review_status='pending',
            created_at__lt=six_hours_ago
        )
        
        for reply in pending_replies_6h:
            # 生成提醒
            create_moderation_reminder('reply', reply.id)
            self.stdout.write(f'为回复 {reply.id} 生成审核提醒')
        
        # 查找超过 24 小时未审核的回复
        twenty_four_hours_ago = now - timezone.timedelta(hours=24)
        pending_replies_24h = Reply.objects.filter(
            review_status='pending',
            created_at__lt=twenty_four_hours_ago
        )
        
        for reply in pending_replies_24h:
            # 检查是否包含敏感词
            has_sensitive, _ = check_sensitive_content(reply.content)
            if not has_sensitive:
                # 自动审核通过
                auto_approve_instance(reply, '系统自动审核通过')
                self.stdout.write(f'回复 {reply.id} 自动审核通过')
