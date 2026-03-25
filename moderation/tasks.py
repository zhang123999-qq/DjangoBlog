"""
Celery 异步审核任务

支持：
- 异步 AI 审核
- 异步图片审核
- 批量审核
- 审核提醒
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


def _log_task_error(task_name: str, exc: Exception, **context):
    """统一任务错误日志，便于检索和告警聚合。"""
    logger.exception('[%s] failed: %s | context=%s', task_name, exc, context)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_moderate_text(self, content_type: str, content_id: int, content: str, user_id: int = None):
    """异步文本审核。"""
    from .models import ModerationLog
    from .reputation import UserReputation
    from .strategy import get_moderation_strategy

    logger.info('开始异步审核: %s #%s', content_type, content_id)

    try:
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning('用户不存在: %s', user_id)

        strategy = get_moderation_strategy()
        result = strategy.moderate_content(user, content)
        logger.info('审核结果: %s - %s', result.get('status'), result.get('message'))

        obj = get_content_object(content_type, content_id)
        if obj:
            obj.review_status = result['status']
            obj.review_note = result['message']
            obj.save(update_fields=['review_status', 'review_note'])

            ModerationLog.objects.create(
                target_type=content_type,
                target_id=content_id,
                action='approved' if result['status'] == 'approved' else 'rejected' if result['status'] == 'rejected' else 'reminded',
                note=result['message'],
            )

            # 更新用户信誉
            if user and user.is_authenticated:
                reputation = UserReputation.get_or_create_for_user(user)
                reputation.increment_posts(approved=(result['status'] == 'approved'))

                if result['status'] == 'approved':
                    bonus = getattr(settings, 'REPUTATION_APPROVE_BONUS', 1)
                    reputation.update_score(bonus, '内容审核通过')
                elif result['status'] == 'rejected':
                    penalty = getattr(settings, 'REPUTATION_REJECT_PENALTY', 5)
                    reputation.update_score(-penalty, '内容被拒绝')

        # 如果需要人工审核，创建提醒
        if result['status'] == 'pending':
            create_moderation_reminder(content_type, content_id)

        return result

    except DatabaseError as e:
        _log_task_error('async_moderate_text.database', e, content_type=content_type, content_id=content_id, user_id=user_id)
        raise self.retry(exc=e)
    except Exception as e:
        _log_task_error('async_moderate_text', e, content_type=content_type, content_id=content_id, user_id=user_id)
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_moderate_image(self, content_type: str, content_id: int, image_path: str = None, image_url: str = None, user_id: int = None):
    """异步图片审核。"""
    from .models import ModerationLog
    from .strategy import get_moderation_strategy

    logger.info('开始异步图片审核: %s #%s', content_type, content_id)

    try:
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning('用户不存在: %s', user_id)

        strategy = get_moderation_strategy()
        result = strategy.moderate_image(user, image_path=image_path, image_url=image_url)

        logger.info('图片审核结果: %s', result.get('status'))

        obj = get_content_object(content_type, content_id)
        if obj:
            obj.review_status = result['status']
            obj.review_note = result['message']
            obj.save(update_fields=['review_status', 'review_note'])

            ModerationLog.objects.create(
                target_type=content_type,
                target_id=content_id,
                action='approved' if result['status'] == 'approved' else 'rejected',
                note=result['message'],
            )

        return result

    except DatabaseError as e:
        _log_task_error('async_moderate_image.database', e, content_type=content_type, content_id=content_id, user_id=user_id)
        raise self.retry(exc=e)
    except Exception as e:
        _log_task_error('async_moderate_image', e, content_type=content_type, content_id=content_id, user_id=user_id)
        raise self.retry(exc=e)


@shared_task
def check_pending_moderation():
    """检查待审核内容，生成提醒。"""
    from .models import ModerationAdmin, ModerationReminder

    logger.info('开始检查待审核内容')

    threshold = timezone.now() - timedelta(hours=6)

    # 批量获取所有审核管理员映射
    admin_mapping = {m.target_type: m.admin for m in ModerationAdmin.objects.all()}

    existing_reminders = set(
        ModerationReminder.objects.filter(is_processed=False).values_list('target_type', 'target_id')
    )

    pending_items = []

    try:
        from apps.blog.models import Comment

        pending_comments = Comment.objects.filter(review_status='pending', created_at__lt=threshold).values_list('id', flat=True)
        for comment_id in pending_comments:
            if ('comment', comment_id) not in existing_reminders:
                pending_items.append(('comment', comment_id))
    except (ImportError, DatabaseError) as e:
        _log_task_error('check_pending_moderation.comments', e)

    try:
        from apps.forum.models import Topic

        pending_topics = Topic.objects.filter(review_status='pending', created_at__lt=threshold).values_list('id', flat=True)
        for topic_id in pending_topics:
            if ('topic', topic_id) not in existing_reminders:
                pending_items.append(('topic', topic_id))
    except (ImportError, DatabaseError) as e:
        _log_task_error('check_pending_moderation.topics', e)

    reminders_to_create = [
        ModerationReminder(target_type=target_type, target_id=target_id, assigned_admin=admin_mapping.get(target_type))
        for target_type, target_id in pending_items
    ]

    if reminders_to_create:
        ModerationReminder.objects.bulk_create(reminders_to_create, ignore_conflicts=True)

    logger.info('生成了 %s 条审核提醒', len(reminders_to_create))
    return len(reminders_to_create)


@shared_task
def auto_approve_old_pending():
    """自动通过超过 24 小时无敏感词的待审核内容。"""
    from .models import ModerationLog
    from .utils import check_sensitive_content

    logger.info('开始自动通过旧待审核内容')

    threshold = timezone.now() - timedelta(hours=24)
    approved_count = 0
    logs_to_create = []

    try:
        from apps.blog.models import Comment

        pending_comments = list(Comment.objects.filter(review_status='pending', created_at__lt=threshold))
        batch_size = 100
        for i in range(0, len(pending_comments), batch_size):
            batch = pending_comments[i:i + batch_size]
            to_approve = []
            for comment in batch:
                has_sensitive, _ = check_sensitive_content(comment.content)
                if not has_sensitive:
                    comment.review_status = 'approved'
                    comment.review_note = '系统自动通过（超时无敏感词）'
                    to_approve.append(comment)
                    logs_to_create.append(
                        ModerationLog(
                            target_type='comment',
                            target_id=comment.id,
                            action='approved',
                            note='系统自动通过（超时无敏感词）',
                        )
                    )
            if to_approve:
                Comment.objects.bulk_update(to_approve, ['review_status', 'review_note'], batch_size)
                approved_count += len(to_approve)
    except (ImportError, DatabaseError) as e:
        _log_task_error('auto_approve_old_pending.comments', e)

    try:
        from apps.forum.models import Topic

        pending_topics = list(Topic.objects.filter(review_status='pending', created_at__lt=threshold))
        batch_size = 100
        for i in range(0, len(pending_topics), batch_size):
            batch = pending_topics[i:i + batch_size]
            to_approve = []
            for topic in batch:
                has_sensitive, _ = check_sensitive_content(topic.content)
                if not has_sensitive:
                    topic.review_status = 'approved'
                    topic.review_note = '系统自动通过（超时无敏感词）'
                    to_approve.append(topic)
                    logs_to_create.append(
                        ModerationLog(
                            target_type='topic',
                            target_id=topic.id,
                            action='approved',
                            note='系统自动通过（超时无敏感词）',
                        )
                    )
            if to_approve:
                Topic.objects.bulk_update(to_approve, ['review_status', 'review_note'], batch_size)
                approved_count += len(to_approve)
    except (ImportError, DatabaseError) as e:
        _log_task_error('auto_approve_old_pending.topics', e)

    if logs_to_create:
        ModerationLog.objects.bulk_create(logs_to_create, batch_size=100)

    logger.info('自动通过了 %s 条内容', approved_count)
    return approved_count


@shared_task
def update_reputation_clean_days():
    """更新用户信誉连续无违规天数。"""
    from .reputation import UserReputation

    logger.info('开始更新用户信誉连续无违规天数')

    reputations = UserReputation.objects.all()
    updated_count = 0

    for reputation in reputations:
        old_clean_days = reputation.clean_days
        reputation.check_clean_days()
        if reputation.clean_days != old_clean_days:
            updated_count += 1

    logger.info('更新了 %s 个用户的连续无违规天数', updated_count)
    return updated_count


def get_content_object(content_type: str, content_id: int):
    """获取内容对象。"""
    try:
        if content_type == 'comment':
            from apps.blog.models import Comment

            return Comment.objects.get(id=content_id)
        if content_type == 'topic':
            from apps.forum.models import Topic

            return Topic.objects.get(id=content_id)
        if content_type == 'reply':
            from apps.forum.models import Reply

            return Reply.objects.get(id=content_id)

        logger.warning('未知 content_type: %s', content_type)
        return None
    except DatabaseError as e:
        _log_task_error('get_content_object.database', e, content_type=content_type, content_id=content_id)
        return None
    except Exception as e:
        _log_task_error('get_content_object', e, content_type=content_type, content_id=content_id)
        return None


def create_moderation_reminder(content_type: str, content_id: int):
    """创建审核提醒。"""
    from .models import ModerationAdmin, ModerationReminder

    try:
        if ModerationReminder.objects.filter(
            target_type=content_type,
            target_id=content_id,
            is_processed=False,
        ).exists():
            return

        assigned_admin = None
        try:
            mod_admin = ModerationAdmin.objects.get(target_type=content_type)
            assigned_admin = mod_admin.admin
        except ModerationAdmin.DoesNotExist:
            assigned_admin = None

        ModerationReminder.objects.create(
            target_type=content_type,
            target_id=content_id,
            assigned_admin=assigned_admin,
        )

        logger.info('创建审核提醒: %s #%s', content_type, content_id)
    except DatabaseError as e:
        _log_task_error('create_moderation_reminder.database', e, content_type=content_type, content_id=content_id)
