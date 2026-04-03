#!/usr/bin/env bash
set -euo pipefail

# DjangoBlog 一键启动 (优化版)
# 兼容新架构: migrate 作为独立容器，web 依赖它

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/docker-compose.yml"
ENV_FILE="$ROOT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "[ERROR] 缺少 $ENV_FILE"
  echo "请先执行: cp .env.example .env 并填写配置"
  exit 1
fi

cd "$ROOT_DIR"

echo "[1/4] 启动 MySQL + Redis"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d db redis

echo "[2/4] 等待 MySQL 就绪..."
timeout 60 bash -c '
  until docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db mysqladmin ping -h localhost 2>/dev/null; do
    sleep 2
  done
'

echo "[3/4] 运行迁移 (独立容器)"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm migrate

echo "[4/4] 启动全部服务 (web/celery/nginx)"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d

echo ""
echo "完成 ✅"
echo "Web:   http://localhost:8000"
echo "Nginx: http://localhost"
echo ""
echo "创建管理员:"
echo "  docker compose exec web python manage.py createsuperuser"
echo ""
echo "健康检查:"
echo "  bash deploy/health.sh check"
