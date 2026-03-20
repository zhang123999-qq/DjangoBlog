from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ModerationLog, ModerationAdmin, ModerationReminder
from .utils import check_sensitive_content


def approve_instance(instance, operator, note=""):
    """
    统一的审核通过方法
    
    Args:
        instance: 审核对象（Comment/Topic/Reply）
        operator: 审核管理员用户
        note: 审核备注
    """
    instance.review_status = 'approved'
    instance.reviewed_by = operator
    instance.reviewed_at = timezone.now()
    instance.review_note = note
    
    instance.save()
    
    # 创建审核日志
    target_type = get_target_type(instance)
    ModerationLog.objects.create(
        target_type=target_type,
        target_id=instance.id,
        action='approved',
        operator=operator,
        note=note
    )
    
    # 更新相关统计信息
    update_related_counts(instance, target_type)


def reject_instance(instance, operator, note=""):
    """
    统一的审核拒绝方法
    
    Args:
        instance: 审核对象（Comment/Topic/Reply）
        operator: 审核管理员用户
        note: 审核备注
    """
    instance.review_status = 'rejected'
    instance.reviewed_by = operator
    instance.reviewed_at = timezone.now()
    instance.review_note = note
    
    instance.save()
    
    # 创建审核日志
    target_type = get_target_type(instance)
    ModerationLog.objects.create(
        target_type=target_type,
        target_id=instance.id,
        action='rejected',
        operator=operator,
        note=note
    )
    
    # 更新相关统计信息
    update_related_counts(instance, target_type)


def auto_approve_instance(instance, note=""):
    """
    系统自动审核通过方法
    
    Args:
        instance: 审核对象（Comment/Topic/Reply）
        note: 审核备注
    """
    instance.review_status = 'approved'
    # 系统审核时 reviewed_by 为空
    instance.reviewed_by = None
    instance.reviewed_at = timezone.now()
    instance.review_note = note
    
    instance.save()
    
    # 创建审核日志
    target_type = get_target_type(instance)
    ModerationLog.objects.create(
        target_type=target_type,
        target_id=instance.id,
        action='approved',
        operator=None,  # 系统审核，operator 为空
        note=note
    )
    
    # 更新相关统计信息
    update_related_counts(instance, target_type)


def get_target_type(instance):
    """
    获取对象的类型
    
    Args:
        instance: 审核对象
    
    Returns:
        str: 对象类型（comment/topic/reply）
    """
    instance_type = instance.__class__.__name__.lower()
    if instance_type == 'comment':
        return 'comment'
    elif instance_type == 'topic':
        return 'topic'
    elif instance_type == 'reply':
        return 'reply'
    else:
        raise ValueError('Invalid instance type')


def update_related_counts(instance, target_type):
    """
    更新相关统计信息
    
    Args:
        instance: 审核对象
        target_type: 对象类型
    """
    if target_type == 'topic' and hasattr(instance, 'board'):
        # 更新版块统计
        instance.board.update_counts()
    elif target_type == 'reply' and hasattr(instance, 'topic'):
        # 更新主题统计
        instance.topic.update_reply_count()


def get_assigned_admin(target_type):
    """
    获取指定内容类型的审核管理员
    
    Args:
        target_type: 内容类型
    
    Returns:
        User: 审核管理员，如果没有设置则返回超级管理员
    """
    User = get_user_model()
    try:
        # 查找对应内容类型的审核管理员
        moderation_admin = ModerationAdmin.objects.get(target_type=target_type)
        if moderation_admin.admin:
            return moderation_admin.admin
    except ModerationAdmin.DoesNotExist:
        pass
    
    # 如果没有设置审核管理员，返回第一个超级管理员
    try:
        super_admin = User.objects.filter(is_superuser=True).first()
        return super_admin
    except User.DoesNotExist:
        return None


def create_moderation_reminder(target_type, target_id):
    """
    创建审核提醒
    
    Args:
        target_type: 内容类型
        target_id: 内容ID
    
    Returns:
        ModerationReminder: 创建的提醒对象
    """
    # 检查是否已经存在提醒
    try:
        reminder = ModerationReminder.objects.get(target_type=target_type, target_id=target_id)
        return reminder
    except ModerationReminder.DoesNotExist:
        pass
    
    # 获取指派管理员
    assigned_admin = get_assigned_admin(target_type)
    
    # 创建提醒
    reminder = ModerationReminder.objects.create(
        target_type=target_type,
        target_id=target_id,
        assigned_admin=assigned_admin
    )
    
    # 创建提醒日志
    ModerationLog.objects.create(
        target_type=target_type,
        target_id=target_id,
        action='reminded',
        operator=assigned_admin,
        note='系统自动生成审核提醒'
    )
    
    return reminder
