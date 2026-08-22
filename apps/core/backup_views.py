"""
数据备份与恢复视图

提供全站数据的 JSON 备份下载和上传恢复功能。
仅超级用户可访问。
"""

import gzip
import io
import json
import logging
import tempfile
from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.db import connection
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)

MAX_RESTORE_SIZE = 50 * 1024 * 1024  # 50MB


def _superuser_required(view_func):
    """仅允许超级用户访问"""

    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("仅超级用户可执行此操作")
        return view_func(request, *args, **kwargs)

    return wrapper


@staff_member_required
@_superuser_required
def backup_view(request):
    """备份管理页面 + 下载备份"""
    if request.GET.get("action") == "download":
        return _download_backup(request)
    return render(request, "admin/backup.html")


def _download_backup(request):
    """生成并下载 gzip 压缩的 JSON 备份"""
    output = io.StringIO()
    call_command(
        "dumpdata",
        "--natural-foreign",
        "--natural-primary",
        "--indent",
        "2",
        stdout=output,
    )
    compressed = gzip.compress(output.getvalue().encode("utf-8"))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"djangoblog_backup_{timestamp}.json.gz"

    response = HttpResponse(compressed, content_type="application/gzip")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Content-Length"] = len(compressed)
    logger.info("管理员 %s 下载了数据备份", request.user.username)
    return response


@staff_member_required
@_superuser_required
def restore_view(request):
    """上传并恢复备份数据"""
    if request.method != "POST":
        return redirect("admin:backup")

    backup_file = request.FILES.get("backup_file")
    if not backup_file:
        messages.error(request, "请选择备份文件")
        return redirect("admin:backup")

    if backup_file.size > MAX_RESTORE_SIZE:
        messages.error(request, "文件过大，最大支持 50MB")
        return redirect("admin:backup")

    try:
        raw = backup_file.read()
        if backup_file.name.endswith(".gz"):
            data = gzip.decompress(raw)
        else:
            data = raw

        records = json.loads(data)
        if not isinstance(records, list):
            raise ValueError("备份格式错误：顶层应为 JSON 数组")

    except Exception as e:
        messages.error(request, f"文件解析失败：{e}")
        return redirect("admin:backup")

    try:
        _do_restore(records)
        logger.warning("管理员 %s 执行了数据恢复，共 %d 条记录", request.user.username, len(records))
        messages.success(request, f"恢复成功！共导入 {len(records)} 条记录")
    except Exception as e:
        logger.exception("数据恢复失败")
        messages.error(request, f"恢复失败：{e}")

    return redirect("admin:backup")


def _do_restore(records):
    """清空数据并导入备份"""
    # 按依赖顺序收集需要清空的表
    models_in_backup = set()
    for rec in records:
        models_in_backup.add(rec.get("model", ""))

    # 定义清空顺序（子表先删，父表后删）
    clear_order = [
        "notifications.notification",
        "moderation.reputationlog",
        "moderation.moderationlog",
        "moderation.moderationreminder",
        "moderation.userreputation",
        "forum.replylike",
        "forum.reply",
        "forum.topic",
        "forum.board",
        "blog.commentlike",
        "blog.comment",
        "blog.post",
        "blog.tag",
        "blog.category",
        "accounts.profile",
        "accounts.user",
        "core.siteconfig",
        "tools.toolconfig",
    ]

    with connection.cursor() as cursor:
        # 获取已存在的表名
        if connection.vendor == "sqlite":
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            cursor.execute("PRAGMA foreign_keys = OFF")
        else:
            existing_tables = None

        def safe_delete(table):
            if existing_tables is not None and table not in existing_tables:
                return
            try:
                cursor.execute(f'DELETE FROM "{table}"')  # nosec B608
            except Exception:
                pass

        for model_label in clear_order:
            if model_label in models_in_backup:
                app_label, model_name = model_label.split(".")
                safe_delete(f"{app_label}_{model_name}")

        for builtin in ["admin.logentry", "sessions.session", "auth.group"]:
            if builtin in models_in_backup:
                app_label, model_name = builtin.split(".")
                safe_delete(f"{app_label}_{model_name}")

        if connection.vendor == "sqlite":
            cursor.execute("PRAGMA foreign_keys = ON")

    # 写入临时文件并 loaddata
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
        tmp_path = f.name

    # 临时禁用 User post_save 信号，避免 loaddata 触发自动创建 Profile 导致冲突
    import apps.accounts.models as accounts_models

    accounts_models._restoring_backup = True
    try:
        call_command("loaddata", tmp_path, verbosity=0)
    finally:
        accounts_models._restoring_backup = False
        import os

        os.unlink(tmp_path)
