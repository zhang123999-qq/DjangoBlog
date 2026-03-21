"""
Celery 异步审核任务

支持：
- 异步 AI 审核
- 异步图片审核
- 批量审核
- 审核提醒
"""

import logging
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_moderate_text(self, content_type: str, content_id: int, content: str, user_id: int = None):
    """异步文本审核
    
    Args:
        content_type: 内容类型 (comment/topic/reply)
        content_id: 内容 ID
        content: 内容文本
        user_id: 用户 ID
    """
    from .strategy import get_moderation_strategy
    from .models import ModerationLog, ModerationReminder
    from .reputation import UserReputation
    
    logger.info(f'开始异步审核: {content_type} #{content_id}')
    
    try:
        # 获取用户
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f'用户不存在: {user_id}')
        
        # 执行审核
        strategy = get_moderation_strategy()
        result = strategy.moderate_content(user, content)
        
        logger.info(f'审核结果: {result["status"]} - {result["message"]}')
        
        # 更新内容状态
        obj = get_content_object(content_type, content_id)
        if obj:
            obj.review_status = result['status']
            obj.review_note = result['message']
            obj.save(update_fields=['review_status', 'review_note'])
            
            # 记录日志
            ModerationLog.objects.create(
                target_type=content_type,
                target_id=content_id,
                action='approved' if result['status'] == 'approved' else 'rejected' if result['status'] == 'rejected' else 'reminded',
                note=result['message']
            )
            
            # 更新用户信誉
            if user and user.is_authenticated:
                reputation = UserReputation.get_or_create_for_user(user)
                reputation.increment_posts(approved=(result['status'] == 'approved'))
                
                # 根据结果调整信誉分
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
    
    except Exception as e:
        logger.error(f'异步审核失败: {e}')
        # 重试
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_moderate_image(self, content_type: str, content_id: int, image_path: str = None, image_url: str = None, user_id: int = None):
    """异步图片审核
    
    Args:
        content_type: 内容类型
        content_id: 内容 ID
        image_path: 图片路径
        image_url: 图片 URL
        user_id: 用户 ID
    """
    from .strategy import get_moderation_strategy
    from .models import ModerationLog
    from .reputation import UserReputation
    
    logger.info(f'开始异步图片审核: {content_type} #{content_id}')
    
    try:
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass
        
        strategy = get_moderation_strategy()
        result = strategy.moderate_image(user, image_path=image_path, image_url=image_url)
        
        logger.info(f'图片审核结果: {result["status"]}')
        
        # 更新内容状态
        obj = get_content_object(content_type, content_id)
        if obj:
            obj.review_status = result['status']
            obj.review_note = result['message']
            obj.save(update_fields=['review_status', 'review_note'])
            
            ModerationLog.objects.create(
                target_type=content_type,
                target_id=content_id,
                action='approved' if result['status'] == 'approved' else 'rejected',
                note=result['message']
            )
        
        return result
    
    except Exception as e:
        logger.error(f'异步图片审核失败: {e}')
        raise self.retry(exc=e)


@shared_task
def check_pending_moderation():
    """检查待审核内容，生成提醒
    
    定时任务：检查超过 6 小时未审核的内容
    """
    from .models import ModerationReminder, ModerationAdmin
    from django.db.models import Q
    
    logger.info('开始检查待审核内容')
    
    # 查找超过 6 小时未审核的内容
    threshold = timezone.now() - timedelta(hours=6)
    
    # 查找各类型的待审核内容
    pending_items = []
    
    # 检查评论
    try:
        from apps.blog.models import Comment
        pending_comments = Comment.objects.filter(
            review_status='pending',
            created_at__lt=threshold
        )
        for comment in pending_comments:
            pending_items.append(('comment', comment.id))
    except Exception as e:
        logger.error(f'检查评论失败: {e}')
    
    # 检查主题
    try:
        from apps.forum.models import Topic
        pending_topics = Topic.objects.filter(
            review_status='pending',
            created_at__lt=threshold
        )
        for topic in pending_topics:
            pending_items.append(('topic', topic.id))
    except Exception as e:
        logger.error(f'检查主题失败: {e}')
    
    # 生成提醒
    created_count = 0
    for target_type, target_id in pending_items:
        # 检查是否已有提醒
        if not ModerationReminder.objects.filter(
            target_type=target_type,
            target_id=target_id,
            is_processed=False
        ).exists():
            # 获取审核管理员
            try:
                mod_admin = ModerationAdmin.objects.get(target_type=target_type)
                assigned_admin = mod_admin.admin
            except ModerationAdmin.DoesNotExist:
                assigned_admin = None
            
            ModerationReminder.objects.create(
                target_type=target_type,
                target_id=target_id,
                assigned_admin=assigned_admin
            )
            created_count += 1
    
    logger.info(f'生成了 {created_count} 条审核提醒')
    return created_count


@shared_task
def auto_approve_old_pending():
    """自动通过超过 24 小时无敏感词的待审核内容
    
    定时任务：每天执行一次
    """
    from .models import ModerationLog
    from .utils import check_sensitive_content
    
    logger.info('开始自动通过旧待审核内容')
    
    threshold = timezone.now() - timedelta(hours=24)
    approved_count = 0
    
    # 处理评论
    try:
        from apps.blog.models import Comment
        pending_comments = Comment.objects.filter(
            review_status='pending',
            created_at__lt=threshold
        )
        for comment in pending_comments:
            has_sensitive, _ = check_sensitive_content(comment.content)
            if not has_sensitive:
                comment.review_status = 'approved'
                comment.review_note = '系统自动通过（超时无敏感词）'
                comment.save(update_fields=['review_status', 'review_note'])
                
                ModerationLog.objects.create(
                    target_type='comment',
                    target_id=comment.id,
                    action='approved',
                    note='系统自动通过（超时无敏感词）'
                )
                approved_count += 1
    except Exception as e:
        logger.error(f'自动通过评论失败: {e}')
    
    # 处理主题
    try:
        from apps.forum.models import Topic
        pending_topics = Topic.objects.filter(
            review_status='pending',
            created_at__lt=threshold
        )
        for topic in pending_topics:
            has_sensitive, _ = check_sensitive_content(topic.content)
            if not has_sensitive:
                topic.review_status = 'approved'
                topic.review_note = '系统自动通过（超时无敏感词）'
                topic.save(update_fields=['review_status', 'review_note'])
                
                ModerationLog.objects.create(
                    target_type='topic',
                    target_id=topic.id,
                    action='approved',
                    note='系统自动通过（超时无敏感词）'
                )
                approved_count += 1
    except Exception as e:
        logger.error(f'自动通过主题失败: {e}')
    
    logger.info(f'自动通过了 {approved_count} 条内容')
    return approved_count


@shared_task
def update_reputation_clean_days():
    """更新用户信誉连续无违规天数
    
    定时任务：每天执行一次
    """
    from .reputation import UserReputation
    
    logger.info('开始更新用户信誉连续无违规天数')
    
    reputations = UserReputation.objects.all()
    updated_count = 0
    
    for reputation in reputations:
        old_clean_days = reputation.clean_days
        reputation.check_clean_days()
        if reputation.clean_days != old_clean_days:
            updated_count += 1
    
    logger.info(f'更新了 {updated_count} 个用户的连续无违规天数')
    return updated_count


def get_content_object(content_type: str, content_id: int):
    """获取内容对象"""
    try:
        if content_type == 'comment':
            from apps.blog.models import Comment
            return Comment.objects.get(id=content_id)
        elif content_type == 'topic':
            from apps.forum.models import Topic
            return Topic.objects.get(id=content_id)
        elif content_type == 'reply':
            from apps.forum.models import Reply
            return Reply.objects.get(id=content_id)
    except Exception as e:
        logger.error(f'获取内容对象失败: {content_type} #{content_id} - {e}')
        return None


def create_moderation_reminder(content_type: str, content_id: int):
    """创建审核提醒"""
    from .models import ModerationReminder, ModerationAdmin
    
    # 检查是否已有提醒
    if ModerationReminder.objects.filter(
        target_type=content_type,
        target_id=content_id,
        is_processed=False
    ).exists():
        return
    
    # 获取审核管理员
    try:
        mod_admin = ModerationAdmin.objects.get(target_type=content_type)
        assigned_admin = mod_admin.admin
    except ModerationAdmin.DoesNotExist:
        assigned_admin = None
    
    ModerationReminder.objects.create(
        target_type=content_type,
        target_id=content_id,
        assigned_admin=assigned_admin
    )
    
    logger.info(f'创建审核提醒: {content_type} #{content_id}')
