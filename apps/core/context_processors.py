from .models import SiteConfig


def site_config(request):
    """提供 site_config 给全局模板"""
    return {
        'site_config': SiteConfig.get_solo()
    }
