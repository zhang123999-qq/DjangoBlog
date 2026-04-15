"""
Django 内置模型 Admin
"""

from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from .admin_site import admin_site

# 注册 Django 内置模型到自定义 admin_site
admin_site.register(Group)
admin_site.register(Site)
