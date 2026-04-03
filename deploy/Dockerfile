# DjangoBlog production Dockerfile
# 优化版本：单阶段构建 + 国内镜像加速 + 缓存优化

# 使用国内镜像源拉取基础镜像（国内服务器部署时更快）
FROM docker.1ms.run/library/python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# 预装编译依赖 + pip 配置为清华镜像
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /root/.config/pip \
    && echo '[global]' > /root/.config/pip/pip.conf \
    && echo 'index-url = https://pypi.tuna.tsinghua.edu.cn/simple' >> /root/.config/pip/pip.conf \
    && echo 'trusted-host = pypi.tuna.tsinghua.edu.cn' >> /root/.config/pip/pip.conf

# Install Python dependencies
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir \
    -r /app/requirements/production.txt

# ---- Final stage ----
FROM docker.1ms.run/library/python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# 运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Setup directories
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chmod 777 /app/staticfiles /app/media /app/logs

# Copy project files
COPY --chown=root:root manage.py /app/manage.py
COPY --chown=root:root apps/ /app/apps/
COPY --chown=root:root config/ /app/config/
COPY --chown=root:root moderation/ /app/moderation/
COPY --chown=root:root templates/ /app/templates/
COPY --chown=root:root static/ /app/static/
COPY --chown=root:root requirements/ /app/requirements/

EXPOSE 8000

# 默认运行 Gunicorn（celery/migrate 会覆盖此命令）
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "120"]
