#!/bin/bash
# DjangoBlog 停止脚本
# 使用方法: ./scripts/stop_server.sh

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ -f logs/gunicorn.pid ]; then
    kill $(cat logs/gunicorn.pid) 2>/dev/null
    echo "Gunicorn stopped"
    rm -f logs/gunicorn.pid
else
    pkill -f gunicorn 2>/dev/null
    echo "Gunicorn stopped (by process name)"
fi

# 清理日志文件（可选）
# rm -f logs/access.log logs/error.log
