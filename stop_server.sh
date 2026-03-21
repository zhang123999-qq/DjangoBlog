#!/bin/bash
# DjangoBlog 停止脚本

cd /www/wwwroot/DjangoBlog

if [ -f logs/gunicorn.pid ]; then
    kill $(cat logs/gunicorn.pid) 2>/dev/null
    echo "Gunicorn stopped"
    rm -f logs/gunicorn.pid
else
    pkill -f gunicorn
    echo "Gunicorn stopped (by process name)"
fi
