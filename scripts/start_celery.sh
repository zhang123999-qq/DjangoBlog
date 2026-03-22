#!/bin/bash
# DjangoBlog Celery 启动脚本 (Linux/macOS)
# 使用方法:
#   ./start_celery.sh worker   - 启动 Worker
#   ./start_celery.sh beat     - 启动 Beat (定时任务)
#   ./start_celery.sh flower   - 启动 Flower (监控界面)
#   ./start_celery.sh all      - 启动全部

set -e

# 设置环境
export DJANGO_SETTINGS_MODULE=config.settings.development

case "${1:-}" in
    worker)
        echo "Starting Celery Worker..."
        celery -A config worker -l info
        ;;
    beat)
        echo "Starting Celery Beat..."
        celery -A config beat -l info
        ;;
    flower)
        echo "Starting Flower..."
        celery -A config flower --port=5555
        ;;
    all)
        echo "Starting all Celery services..."
        celery -A config multi start worker beat flower \
            -l info \
            --pidfile=/var/run/celery/%n.pid \
            --logfile=/var/log/celery/%n.log
        echo "All services started!"
        echo "Flower UI: http://localhost:5555"
        ;;
    stop)
        echo "Stopping all Celery services..."
        celery -A config multi stopwait worker beat flower \
            --pidfile=/var/run/celery/%n.pid
        ;;
    restart)
        echo "Restarting all Celery services..."
        celery -A config multi restart worker beat flower \
            -l info \
            --pidfile=/var/run/celery/%n.pid \
            --logfile=/var/log/celery/%n.log
        ;;
    *)
        echo "Usage: $0 {worker|beat|flower|all|stop|restart}"
        echo ""
        echo "Commands:"
        echo "  worker  - Start Celery Worker (process tasks)"
        echo "  beat    - Start Celery Beat (scheduled tasks)"
        echo "  flower  - Start Flower (monitoring UI at http://localhost:5555)"
        echo "  all     - Start all services"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo ""
        echo "Prerequisites:"
        echo "  1. Redis must be running on localhost:6379"
        echo "  2. Run: pip install celery redis flower"
        exit 1
        ;;
esac
