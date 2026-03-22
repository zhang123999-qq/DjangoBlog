#!/bin/bash
# DjangoBlog 生产环境启动脚本
# 使用方法: ./scripts/start_server.sh

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 停止旧进程
pkill -f gunicorn 2>/dev/null
sleep 2

# 创建日志目录
mkdir -p logs

# 启动 Gunicorn
nohup gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --pid logs/gunicorn.pid \
    > logs/startup.log 2>&1 &

echo "Gunicorn started on 0.0.0.0:8000"
echo "PID: $(cat logs/gunicorn.pid 2>/dev/null || echo 'N/A')"
echo "Logs: $PROJECT_DIR/logs/"
