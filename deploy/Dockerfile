# DjangoBlog production Dockerfile
# 优化版本：预装编译工具，加速依赖安装

FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# 预装编译依赖（加速 Pillow, cryptography, gevent 等编译）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    pkg-config \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# 使用清华镜像源（更快更稳定）
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 10 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r /app/requirements/production.txt

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# 运行时依赖（图片处理等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Setup directories
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chmod 777 /app/staticfiles /app/media /app/logs \
    && python -c "import django; print('Django OK')"

# Create non-root user
RUN useradd -ms /bin/bash djangouser

# Copy project files
COPY --chown=djangouser:djangouser manage.py /app/manage.py
COPY --chown=djangouser:djangouser apps/ /app/apps/
COPY --chown=djangouser:djangouser config/ /app/config/
COPY --chown=djangouser:djangouser moderation/ /app/moderation/
COPY --chown=djangouser:djangouser templates/ /app/templates/
COPY --chown=djangouser:djangouser static/ /app/static/
COPY --chown=djangouser:djangouser requirements/ /app/requirements/

# Collect static files
RUN python manage.py collectstatic --noinput --ignore=tests \
    && chown -R djangouser:djangouser /app/staticfiles \
    && chown -R djangouser:djangouser /app/media \
    && chown -R djangouser:djangouser /app/logs

USER djangouser

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2"]
