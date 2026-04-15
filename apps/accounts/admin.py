"""
用户管理 - 已迁移到 apps/core/admin.py
统一使用自定义 admin_site 避免冲突

迁移原因：
- Django 要求模型只能注册到一个 admin site
- apps/core/admin.py 使用自定义 DjangoBlogAdminSite
- 避免多个 admin.py 重复注册导致冲突
"""
