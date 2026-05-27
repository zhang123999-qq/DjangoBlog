#!/bin/sh
set -e

# 修复 volume 目录权限（旧部署可能以 root 创建 volume，owner 是 root）
for dir in /app/staticfiles /app/media /app/logs /app/beat_schedule; do
    if [ -d "$dir" ]; then
        chown -R djangoblog:djangoblog "$dir" 2>/dev/null || true
    fi
done

# 数据库就绪重试（MySQL 可能已接受 TCP 但尚未完成初始化）
echo "[entrypoint] Running migrations..."
MAX_RETRIES=30
RETRY_INTERVAL=2
i=0
while [ $i -lt $MAX_RETRIES ]; do
    if python manage.py migrate --noinput 2>&1; then
        break
    fi
    i=$((i + 1))
    echo "[entrypoint] Database not ready, retrying... ($i/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done
if [ $i -ge $MAX_RETRIES ]; then
    echo "[entrypoint] ERROR: Database migration failed after $MAX_RETRIES attempts" >&2
    exit 1
fi

# collectstatic 是幂等的，直接执行即可
echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput

# 仅在构建阶段未执行 compress 时才运行（检查 manifest 文件是否存在）
if [ ! -f "/app/staticfiles/CACHE/manifest.json" ]; then
    echo "[entrypoint] Compressing templates..."
    python manage.py compress --force || echo "[entrypoint] WARNING: compress failed, continuing..." >&2
else
    echo "[entrypoint] Compressed files already exist, skipping compress."
fi

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
