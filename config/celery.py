"""
Celery 配置文件

启动 Celery Worker:
    celery -A config worker -l info

启动 Celery Beat (定时任务):
    celery -A config beat -l info

启动 Flower (监控界面):
    celery -A config flower --port=5555
"""

import logging
import os

from celery import Celery
from django.conf import settings

# 设置默认 Django settings 模块（可被环境变量覆盖）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

logger = logging.getLogger(__name__)

app = Celery("djangoblog")

# 使用 Django settings 中的 CELERY 配置
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现所有应用中的 tasks.py
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """调试任务"""
    logger.debug("Celery debug request: %r", self.request)
