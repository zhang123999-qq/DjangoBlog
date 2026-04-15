"""上传异步隔离扫描任务（v4）"""

import logging
import socket
import struct
import uuid
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)

CLAMAV_ENABLED = getattr(settings, "UPLOAD_CLAMAV_ENABLED", False)
CLAMAV_HOST = getattr(settings, "UPLOAD_CLAMAV_HOST", "127.0.0.1")
CLAMAV_PORT = getattr(settings, "UPLOAD_CLAMAV_PORT", 3310)
CLAMAV_TIMEOUT = getattr(settings, "UPLOAD_CLAMAV_TIMEOUT", 5)
CLAMAV_FAIL_CLOSED = getattr(settings, "UPLOAD_CLAMAV_FAIL_CLOSED", False)
UPLOAD_STATUS_TTL = getattr(settings, "UPLOAD_STATUS_TTL", 24 * 3600)


def _status_key(upload_id: str) -> str:
    return f"upload:status:{upload_id}"


def _set_status(upload_id: str, payload: dict):
    cache.set(_status_key(upload_id), payload, UPLOAD_STATUS_TTL)


def _clamav_scan_bytes(content: bytes) -> tuple[bool, str]:
    if not CLAMAV_ENABLED:
        return True, "clamav disabled"

    try:
        with socket.create_connection((CLAMAV_HOST, CLAMAV_PORT), timeout=CLAMAV_TIMEOUT) as sock:
            sock.sendall(b"zINSTREAM\0")
            sock.sendall(struct.pack("!I", len(content)))
            sock.sendall(content)
            sock.sendall(struct.pack("!I", 0))
            resp = sock.recv(4096).decode("utf-8", errors="ignore").strip()

        if "OK" in resp:
            return True, resp
        if "FOUND" in resp:
            return False, resp
        raise RuntimeError(f"clamav unexpected response: {resp}")
    except (socket.timeout, socket.error, OSError, RuntimeError, ValueError) as e:
        logger.exception("clamav scan bytes failed")
        if CLAMAV_FAIL_CLOSED:
            return False, f"clamav error (fail-closed): {e}"
        return True, f"clamav error (fail-open): {e}"


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})
def process_quarantined_upload(self, upload_id: str, quarantine_path: str, ext: str, original_name: str):
    """隔离区文件扫描后转正。"""
    _set_status(upload_id, {"status": "scanning", "upload_id": upload_id, "filename": original_name})

    if not default_storage.exists(quarantine_path):
        _set_status(upload_id, {"status": "failed", "upload_id": upload_id, "error": "quarantine file missing"})
        return {"ok": False, "reason": "missing"}

    with default_storage.open(quarantine_path, "rb") as f:
        content = f.read()

    clean, detail = _clamav_scan_bytes(content)
    if not clean:
        logger.warning("quarantine blocked by clamav: %s", detail)
        default_storage.delete(quarantine_path)
        _set_status(upload_id, {"status": "rejected", "upload_id": upload_id, "reason": detail})
        return {"ok": False, "reason": detail}

    today = datetime.now().strftime("%Y/%m")
    final_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    final_path = f"uploads/files/{today}/{final_name}"

    default_storage.save(final_path, ContentFile(content))
    default_storage.delete(quarantine_path)

    location = f"{settings.MEDIA_URL}{final_path}"
    _set_status(
        upload_id,
        {
            "status": "ready",
            "upload_id": upload_id,
            "location": location,
            "filename": original_name,
            "detail": detail,
        },
    )
    return {"ok": True, "location": location}
