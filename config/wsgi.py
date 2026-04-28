"""WSGI config for project."""

import os

from django.core.wsgi import get_wsgi_application

# Default to production settings for WSGI deployments.
# Local development can still override this with DJANGO_SETTINGS_MODULE.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
