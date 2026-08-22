import logging

from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.utils import timezone

from .models import ModerationAdmin, ModerationLog, ModerationReminder

logger = logging.getLogger(__name__)


def _log_service_error(op: str, exc: Exception, **context):
    logger.exception("[moderation.services.%s] failed: %s | context=%s", op, exc, context)


def approve_instance(instance, operator, note=""):
    """统一的审核通过方法。"""
    target_type = get_target_type(instance)
    try:
        with transaction.atomic():
            instance.review_status = "approved"
            instance.reviewed_by = operator
            instance.reviewed_at = timezone.now()
            instance.review_note = note
            instance.save()

            ModerationLog.objects.create(
                target_type=target_type,
                target_id=instance.id,
                action="approved",
                operator=operator,
                note=note,
            )

            update_related_counts(instance, target_type)
    except DatabaseError as e:
        _log_service_error(
            "approve_instance.database", e, target_type=target_type, target_id=getattr(instance, "id", None)
        )
        raise


def reject_instance(instance, operator, note=""):
    """统一的审核拒绝方法。"""
    target_type = get_target_type(instance)
    try:
        with transaction.atomic():
            instance.review_status = "rejected"
            instance.reviewed_by = operator
            instance.reviewed_at = timezone.now()
            instance.review_note = note
            instance.save()

            ModerationLog.objects.create(
                target_type=target_type,
                target_id=instance.id,
                action="rejected",
                operator=operator,
                note=note,
            )

            update_related_counts(instance, target_type)
    except DatabaseError as e:
        _log_service_error(
            "reject_instance.database", e, target_type=target_type, target_id=getattr(instance, "id", None)
        )
        raise


def auto_approve_instance(instance, note=""):
    """系统自动审核通过方法。"""
    target_type = get_target_type(instance)
    try:
        with transaction.atomic():
            instance.review_status = "approved"
            instance.reviewed_by = None
            instance.reviewed_at = timezone.now()
            instance.review_note = note
            instance.save()

            ModerationLog.objects.create(
                target_type=target_type,
                target_id=instance.id,
                action="approved",
                operator=None,
                note=note,
            )

            update_related_counts(instance, target_type)
    except DatabaseError as e:
        _log_service_error(
            "auto_approve_instance.database", e, target_type=target_type, target_id=getattr(instance, "id", None)
        )
        raise


def get_target_type(instance):
    """获取对象的类型。"""
    instance_type = instance.__class__.__name__.lower()
    if instance_type == "comment":
        return "comment"
    if instance_type == "topic":
        return "topic"
    if instance_type == "reply":
        return "reply"
    raise ValueError("Invalid instance type")


def update_related_counts(instance, target_type):
    """更新相关统计信息。"""
    try:
        if target_type == "topic" and hasattr(instance, "board"):
            instance.board.update_counts()
        elif target_type == "reply" and hasattr(instance, "topic"):
            instance.topic.update_reply_count()
    except Exception as e:
        _log_service_error("update_related_counts", e, target_type=target_type, target_id=getattr(instance, "id", None))


def get_assigned_admin(target_type):
    """获取指定内容类型的审核管理员（优先返回主要负责人）。"""
    User = get_user_model()
    try:
        moderation_admin = ModerationAdmin.objects.filter(target_type=target_type).order_by("-is_primary").first()
        if moderation_admin and moderation_admin.admin:
            return moderation_admin.admin
    except DatabaseError as e:
        _log_service_error("get_assigned_admin.database", e, target_type=target_type)
        return None

    try:
        return User.objects.filter(is_superuser=True).first()
    except DatabaseError as e:
        _log_service_error("get_assigned_admin.superuser", e, target_type=target_type)
        return None


def create_moderation_reminder(target_type, target_id):
    """创建审核提醒。"""
    try:
        reminder, created = ModerationReminder.objects.get_or_create(
            target_type=target_type,
            target_id=target_id,
            defaults={"assigned_admin": get_assigned_admin(target_type)},
        )

        if created:
            ModerationLog.objects.create(
                target_type=target_type,
                target_id=target_id,
                action="reminded",
                operator=reminder.assigned_admin,
                note="系统自动生成审核提醒",
            )

        return reminder
    except DatabaseError as e:
        _log_service_error("create_moderation_reminder.database", e, target_type=target_type, target_id=target_id)
        raise


def smart_moderate_instance(instance, content=None):
    """智能审核实例：通过统一的 strategy 层进行敏感词 + AI 双重检测。

    统一使用 strategy.py 中的审核逻辑，避免 baidu_moderation.py 和
    ai_service.py 两套代码路径产生不一致行为。
    """
    from .strategy import get_moderation_strategy

    if content is None:
        instance_type = instance.__class__.__name__.lower()
        if instance_type == "topic":
            content = f"{instance.title} {instance.content}"
        else:
            content = getattr(instance, "content", "")

    user = getattr(instance, "user", None) or getattr(instance, "author", None)
    strategy = get_moderation_strategy()
    result = strategy.moderate_content(user, content)

    status = result["status"]
    summary = result["message"]

    try:
        if status == "approved":
            auto_approve_instance(instance, summary)
            logger.info("%s %s 审核通过", instance.__class__.__name__, instance.id)
            return "approved", summary

        if status == "rejected":
            with transaction.atomic():
                instance.review_status = "rejected"
                instance.reviewed_by = None
                instance.reviewed_at = timezone.now()
                instance.review_note = summary
                instance.save()

                target_type = get_target_type(instance)
                ModerationLog.objects.create(
                    target_type=target_type,
                    target_id=instance.id,
                    action="rejected",
                    operator=None,
                    note=summary,
                )

                update_related_counts(instance, target_type)

            logger.warning("%s %s 识别违规，已自动拒绝", instance.__class__.__name__, instance.id)
            return "rejected", summary

        instance.review_status = "pending"
        instance.review_note = summary
        instance.save(update_fields=["review_status", "review_note"])
        logger.info("%s %s 进入人工审核队列: %s", instance.__class__.__name__, instance.id, summary)
        return "pending", summary

    except DatabaseError as e:
        _log_service_error(
            "smart_moderate_instance.database", e, instance_id=getattr(instance, "id", None), status=status
        )
        raise


def ai_batch_moderate(model_class, batch_size=100):
    """批量 AI 审核。"""
    stats = {"approved": 0, "rejected": 0, "pending": 0, "error": 0}

    pending_queryset = model_class.objects.filter(review_status="pending")[:batch_size]

    for instance in pending_queryset:
        try:
            status, _ = smart_moderate_instance(instance)
            stats[status] += 1
        except DatabaseError as e:
            _log_service_error(
                "ai_batch_moderate.database", e, model=model_class.__name__, instance_id=getattr(instance, "id", None)
            )
            stats["error"] += 1
        except Exception as e:
            _log_service_error(
                "ai_batch_moderate", e, model=model_class.__name__, instance_id=getattr(instance, "id", None)
            )
            stats["error"] += 1

    logger.info("%s 批量审核完成: %s", model_class.__name__, stats)
    return stats


def moderate_with_fallback(instance, content=None):
    """便捷审核入口：自动捕获异常，返回 (status, message) 元组。

    当审核服务不可用时，安全降级为 pending 状态，不阻塞业务流程。
    供各业务 app 的 services.py 统一调用，消除 try/except 样板代码。
    """
    try:
        return smart_moderate_instance(instance, content=content)
    except Exception as e:
        logger.warning("审核服务异常: %s", e)
        return "pending", "审核服务暂时不可用，稍后审核"
