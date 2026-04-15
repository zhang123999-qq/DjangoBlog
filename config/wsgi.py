"""WSGI config for project."""

import os

from django.core.wsgi import get_wsgi_application

# Default to production settings in WSGI runtime (can still be overridden by env)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
