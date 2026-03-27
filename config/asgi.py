"""ASGI config for project."""

import os

from django.core.asgi import get_asgi_application

# Keep ASGI default aligned with production runtime (can be overridden by env)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_asgi_application()
