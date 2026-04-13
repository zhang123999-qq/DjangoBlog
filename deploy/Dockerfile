# DjangoBlog production Dockerfile
# 多阶段构建：builder 编译依赖 → final 仅运行时
# 优化：清华 apt/pip 源加速构建

FROM docker.1ms.run/library/python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# 替换 apt 源：删除 deb822 格式，改清华源（传统 sources.list 格式最稳定）
# 注意：suites 和 components 用空格分隔，不能用斜杠
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && rm -f /etc/apt/sources.list.d/debian-security.sources \
    && { \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main"; \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main"; \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main"; \
    } > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        pkg-config \
        libffi-dev \
        libjpeg-dev \
        libpng-dev \
        zlib1g-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /root/.config/pip \
    && printf '[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple\ntrusted-host = pypi.tuna.tsinghua.edu.cn\n' > /root/.config/pip/pip.conf

# Install Python dependencies
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir \
    --timeout 120 \
    --retries 5 \
    -r /app/requirements/production.txt

# ---- Final stage ----
FROM docker.1ms.run/library/python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# 运行时依赖（同清华源）
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && rm -f /etc/apt/sources.list.d/debian-security.sources \
    && { \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main"; \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main"; \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main"; \
    } > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
        libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY --chown=root:root manage.py /app/manage.py
COPY --chown=root:root apps/ /app/apps/
COPY --chown=root:root config/ /app/config/
COPY --chown=root:root moderation/ /app/moderation/
COPY --chown=root:root templates/ /app/templates/
COPY --chown=root:root static/ /app/static/
COPY --chown=root:root requirements/ /app/requirements/
COPY --chown=root:root deploy/gunicorn.conf.py /app/deploy/gunicorn.conf.py

# Setup directories
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chmod 777 /app/staticfiles /app/media /app/logs

# 构建时执行 collectstatic，生成 WhiteNoise 清单
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=build-placeholder-key-for-collectstatic \
    python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

# 默认运行 Gunicorn（celery/migrate 会覆盖此命令）
CMD ["gunicorn", "config.wsgi:application", "--config", "deploy/gunicorn.conf.py"]
