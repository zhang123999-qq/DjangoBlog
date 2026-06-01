# DjangoBlog production Dockerfile
# 多阶段构建：builder 编译依赖 → final 仅运行时
# 优化：清华 apt/pip 源加速构建

FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# 替换 apt 源：自动匹配基础镜像的 Debian 版本，避免 bookworm/trixie 混装依赖。
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && rm -f /etc/apt/sources.list.d/debian-security.sources \
    && . /etc/os-release \
    && { \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ ${VERSION_CODENAME} main"; \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ ${VERSION_CODENAME}-updates main"; \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security ${VERSION_CODENAME}-security main"; \
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
    -r /app/requirements/production.lock

# ---- Final stage ----
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# 运行时依赖（同清华源，版本与基础镜像一致）
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && rm -f /etc/apt/sources.list.d/debian-security.sources \
    && . /etc/os-release \
    && { \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ ${VERSION_CODENAME} main"; \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ ${VERSION_CODENAME}-updates main"; \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security ${VERSION_CODENAME}-security main"; \
    } > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
        libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户运行应用
RUN groupadd -r djangoblog && useradd -r -g djangoblog -d /app -s /sbin/nologin djangoblog

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY --chown=djangoblog:djangoblog manage.py /app/manage.py
COPY --chown=djangoblog:djangoblog apps/ /app/apps/
COPY --chown=djangoblog:djangoblog config/ /app/config/
COPY --chown=djangoblog:djangoblog moderation/ /app/moderation/
COPY --chown=djangoblog:djangoblog templates/ /app/templates/
COPY --chown=djangoblog:djangoblog static/ /app/static/
COPY --chown=djangoblog:djangoblog requirements/ /app/requirements/
COPY --chown=djangoblog:djangoblog deploy/gunicorn.conf.py /app/deploy/gunicorn.conf.py
COPY --chown=djangoblog:djangoblog deploy/entrypoint.sh /app/deploy/entrypoint.sh

# Setup directories + ensure entrypoint is executable
RUN mkdir -p /app/staticfiles /app/media /app/logs /app/beat_schedule \
    && chown djangoblog:djangoblog /app/staticfiles /app/media /app/logs /app/beat_schedule \
    && chmod +x /app/deploy/entrypoint.sh

# 构建时执行 collectstatic，生成 WhiteNoise 清单
# compress 失败不阻塞构建（运行时 entrypoint.sh 会兜底）
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=build-placeholder-key-for-collectstatic \
    DB_ENGINE=sqlite \
    USE_REDIS=False \
    python manage.py collectstatic --noinput \
    && python manage.py compress --force

EXPOSE 8000

# entrypoint 以 root 运行（修复 volume 权限），然后降权到 djangoblog 执行主进程
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--config", "deploy/gunicorn.conf.py"]
