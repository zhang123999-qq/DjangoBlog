# syntax=docker/dockerfile:1.7
# DjangoBlog production Dockerfile
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# Build dependencies (for potential source builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from production locklist (cache-enabled)
COPY requirements/ /app/requirements/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /app/requirements/production.txt

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# Copy installed packages and entrypoints
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Setup directories BEFORE user switch (root)
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chmod 777 /app/staticfiles /app/media /app/logs \
    && python -c "import django; print('Django OK')"

# Non-root runtime user
RUN useradd -ms /bin/bash djangouser

# Copy project with ownership to avoid expensive chown -R
COPY --chown=djangouser:djangouser manage.py /app/manage.py
COPY --chown=djangouser:djangouser apps/ /app/apps/
COPY --chown=djangouser:djangouser config/ /app/config/
COPY --chown=djangouser:djangouser moderation/ /app/moderation/
COPY --chown=djangouser:djangouser templates/ /app/templates/
COPY --chown=djangouser:djangouser static/ /app/static/
COPY --chown=djangouser:djangouser requirements/ /app/requirements/

# Collect static files as root (axes won't try DB at import time)
# Then chown all to djangouser
RUN python manage.py collectstatic --noinput --ignore=tests \
    && chown -R djangouser:djangouser /app/staticfiles \
    && chown -R djangouser:djangouser /app/media \
    && chown -R djangouser:djangouser /app/logs

USER djangouser

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2"]
