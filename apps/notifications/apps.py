"""
通知应用配置
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = '通知管理'

    def ready(self):
        """应用启动时的初始化"""
        # 导入信号处理
        try:
            import apps.notifications.signals  # noqa
        except ImportError:
            pass
