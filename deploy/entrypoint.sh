#!/bin/sh
set -e

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

# 仅在 staticfiles 为空时执行 collectstatic（volume 挂载首次为空，后续启动已有文件）
if [ -z "$(ls -A /app/staticfiles 2>/dev/null)" ]; then
    echo "[entrypoint] Collecting static files (first run)..."
    python manage.py collectstatic --noinput
fi

echo "[entrypoint] Compressing templates..."
python manage.py compress --force || echo "[entrypoint] WARNING: compress failed, continuing..."

echo "[entrypoint] Starting $*..."
exec "$@"
