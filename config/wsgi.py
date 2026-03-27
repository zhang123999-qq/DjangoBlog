"""WSGI config for project."""

import os

import pymysql
from django.core.wsgi import get_wsgi_application

# Ensure Django MySQL backend can use PyMySQL under gunicorn/WSGI
pymysql.install_as_MySQLdb()
pymysql.version_info = (2, 2, 0, "final", 0)

# Default to production settings in WSGI runtime (can still be overridden by env)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
