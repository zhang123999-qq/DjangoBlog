"""WSGI config for project."""

import os

from django.core.wsgi import get_wsgi_application

# 将 production 改为 development
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_wsgi_application()
