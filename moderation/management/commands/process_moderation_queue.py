from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.blog.models import Comment
from apps.forum.models import Topic, Reply
from moderation.services import (
    create_moderation_reminder,
    smart_moderate_instance,
)
from moderation.utils import check_sensitive_content


class Command(BaseCommand):
    """
    处理审核队列的命令

    流程：
    1. AI 审核所有待审核内容（如果启用）
    2. 超过 6 小时未审核的，生成提醒通知管理员
    3. 超过 24 小时未审核且 AI 未启用的，使用敏感词检测自动通过
    """

    help = "处理审核队列：AI审核、生成提醒、自动处理"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ai-batch",
            type=int,
            default=100,
            help="AI批量审核的数量限制（默认100）",
        )
        parser.add_argument(
            "--skip-ai",
            action="store_true",
            help="跳过AI审核，只处理提醒",
        )

    def handle(self, *args, **kwargs):
        self.stdout.write("开始处理审核队列...")

        batch_size = kwargs.get("ai_batch", 100)
        skip_ai = kwargs.get("skip_ai", False)

        # 统计
        stats = {
            "ai_processed": 0,
            "approved": 0,
            "rejected": 0,
            "pending": 0,
            "reminders": 0,
        }

        # 步骤1：AI 批量审核（如果启用）
        if settings.BAIDU_MODERATION_ENABLED and not skip_ai:
            self.stdout.write("正在进行 AI 批量审核...")

            # 处理评论
            for comment in Comment.objects.filter(review_status="pending")[:batch_size]:
                status, _ = smart_moderate_instance(comment)
                stats["ai_processed"] += 1
                stats[status] += 1
                self.stdout.write(f"评论 {comment.id}: {status}")

            # 处理主题
            for topic in Topic.objects.filter(review_status="pending")[:batch_size]:
                status, _ = smart_moderate_instance(topic)
                stats["ai_processed"] += 1
                stats[status] += 1
                self.stdout.write(f"主题 {topic.id}: {status}")

            # 处理回复
            for reply in Reply.objects.filter(review_status="pending")[:batch_size]:
                status, _ = smart_moderate_instance(reply)
                stats["ai_processed"] += 1
                stats[status] += 1
                self.stdout.write(f"回复 {reply.id}: {status}")

            self.stdout.write(f"AI 审核完成: {stats}")

        # 步骤2：处理超时提醒
        now = timezone.now()
        six_hours_ago = now - timezone.timedelta(hours=6)

        # 评论提醒
        for comment in Comment.objects.filter(review_status="pending", created_at__lt=six_hours_ago):
            create_moderation_reminder("comment", comment.id)
            stats["reminders"] += 1
            self.stdout.write(f"为评论 {comment.id} 生成审核提醒")

        # 主题提醒
        for topic in Topic.objects.filter(review_status="pending", created_at__lt=six_hours_ago):
            create_moderation_reminder("topic", topic.id)
            stats["reminders"] += 1
            self.stdout.write(f"为主题 {topic.id} 生成审核提醒")

        # 回复提醒
        for reply in Reply.objects.filter(review_status="pending", created_at__lt=six_hours_ago):
            create_moderation_reminder("reply", reply.id)
            stats["reminders"] += 1
            self.stdout.write(f"为回复 {reply.id} 生成审核提醒")

        # 步骤3：处理超过24小时的待审核内容（AI未启用时的降级处理）
        if not settings.BAIDU_MODERATION_ENABLED or skip_ai:
            self.stdout.write("AI审核未启用，使用敏感词检测处理超时内容...")

            from moderation.services import auto_approve_instance

            twenty_four_hours_ago = now - timezone.timedelta(hours=24)

            # 评论
            for comment in Comment.objects.filter(review_status="pending", created_at__lt=twenty_four_hours_ago):
                has_sensitive, _ = check_sensitive_content(comment.content)
                if not has_sensitive:
                    auto_approve_instance(comment, "系统自动审核通过（超时无敏感词）")
                    self.stdout.write(f"评论 {comment.id} 超时自动通过")

            # 主题
            for topic in Topic.objects.filter(review_status="pending", created_at__lt=twenty_four_hours_ago):
                content = f"{topic.title} {topic.content}"
                has_sensitive, _ = check_sensitive_content(content)
                if not has_sensitive:
                    auto_approve_instance(topic, "系统自动审核通过（超时无敏感词）")
                    self.stdout.write(f"主题 {topic.id} 超时自动通过")

            # 回复
            for reply in Reply.objects.filter(review_status="pending", created_at__lt=twenty_four_hours_ago):
                has_sensitive, _ = check_sensitive_content(reply.content)
                if not has_sensitive:
                    auto_approve_instance(reply, "系统自动审核通过（超时无敏感词）")
                    self.stdout.write(f"回复 {reply.id} 超时自动通过")

        self.stdout.write(
            self.style.SUCCESS(
                f'审核队列处理完成: AI处理={stats["ai_processed"]}, '
                f'通过={stats["approved"]}, 拒绝={stats["rejected"]}, '
                f'待审={stats["pending"]}, 提醒={stats["reminders"]}'
            )
        )
