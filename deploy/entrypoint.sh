#!/bin/sh
set -e

# 修复 volume 目录权限（旧部署可能以 root 创建 volume，owner 是 root）
for dir in /app/staticfiles /app/media /app/logs /app/beat_schedule; do
    if [ -d "$dir" ]; then
        chown -R djangoblog:djangoblog "$dir" 2>/dev/null || true
    fi
done

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
# 降权到 djangoblog 用户执行主进程（Gunicorn/Celery）
exec python -c "
import os, sys, pwd
pw = pwd.getpwnam('djangoblog')
os.setgid(pw.pw_gid)
os.setuid(pw.pw_uid)
os.environ['HOME'] = pw.pw_dir
os.execvp(sys.argv[1], sys.argv[1:])
" "$@"
