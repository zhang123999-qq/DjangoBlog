from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
import logging
from .models import ModerationLog, ModerationAdmin, ModerationReminder
from .utils import check_sensitive_content

logger = logging.getLogger(__name__)


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


def smart_moderate_instance(instance, content=None):
    """
    智能审核实例：敏感词 + AI 双重检测
    
    流程：
    1. 敏感词检测（本地，快速）
    2. AI 语义审核（百度内容审核）
    
    结果：
    - AI 通过 → 自动发布
    - AI 拒绝 → 自动拒绝
    - AI 疑似/敏感词命中 → 待人工审核
    
    Args:
        instance: 审核对象（Comment/Topic/Reply）
        content: 要审核的内容，默认从实例中提取
    
    Returns:
        tuple: (status, message)
            - status: 'approved' | 'rejected' | 'pending'
            - message: 审核结果说明
    """
    from .baidu_moderation import smart_moderate, get_moderation_summary
    
    # 获取要审核的内容
    if content is None:
        # 根据实例类型获取内容
        instance_type = instance.__class__.__name__.lower()
        if instance_type == 'topic':
            content = f"{instance.title} {instance.content}"
        else:
            content = getattr(instance, 'content', '')
    
    # 执行智能审核
    status, details = smart_moderate(content)
    
    # 生成审核摘要
    summary = get_moderation_summary(status, details)
    
    # 根据结果处理
    if status == 'approved':
        # AI 审核通过，自动发布
        auto_approve_instance(instance, summary)
        logger.info(f'{instance.__class__.__name__} {instance.id} AI审核通过')
        return 'approved', summary
    
    elif status == 'rejected':
        # AI 识别违规，自动拒绝
        instance.review_status = 'rejected'
        instance.reviewed_by = None  # 系统自动拒绝
        instance.reviewed_at = timezone.now()
        instance.review_note = summary
        instance.save()
        
        # 创建审核日志
        target_type = get_target_type(instance)
        ModerationLog.objects.create(
            target_type=target_type,
            target_id=instance.id,
            action='rejected',
            operator=None,
            note=summary
        )
        
        logger.warning(f'{instance.__class__.__name__} {instance.id} AI识别违规，已自动拒绝')
        return 'rejected', summary
    
    else:
        # 疑似或敏感词命中，进入人工审核队列
        instance.review_status = 'pending'
        instance.review_note = summary
        instance.save()
        
        logger.info(f'{instance.__class__.__name__} {instance.id} 进入人工审核队列: {summary}')
        return 'pending', summary


def ai_batch_moderate(model_class, batch_size=100):
    """
    批量 AI 审核
    
    对所有待审核内容进行 AI 审核，适合定时任务调用
    
    Args:
        model_class: 模型类（Comment/Topic/Reply）
        batch_size: 每批处理数量
    
    Returns:
        dict: 统计结果 {'approved': n, 'rejected': n, 'pending': n}
    """
    stats = {'approved': 0, 'rejected': 0, 'pending': 0, 'error': 0}
    
    # 获取待审核内容
    pending_queryset = model_class.objects.filter(review_status='pending')[:batch_size]
    
    for instance in pending_queryset:
        try:
            status, _ = smart_moderate_instance(instance)
            stats[status] += 1
        except Exception as e:
            logger.error(f'审核 {model_class.__name__} {instance.id} 失败: {e}')
            stats['error'] += 1
    
    logger.info(f'{model_class.__name__} 批量审核完成: {stats}')
    return stats
