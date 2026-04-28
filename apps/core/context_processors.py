from django.db.utils import OperationalError, ProgrammingError
from django.conf import settings


def site_config(request):
    """提供 site_config 给全局模板"""
    try:
        from .models import SiteConfig

        if getattr(settings, "TESTING", False):
            return {"site_config": SiteConfig()}

        return {"site_config": SiteConfig.get_solo()}
    except (OperationalError, ProgrammingError):
        # 数据库表不存在（安装过程中）
        return {"site_config": None}
