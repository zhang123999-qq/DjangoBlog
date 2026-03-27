#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/docker-compose.yml"
ENV_FILE="$ROOT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "[ERROR] 缺少 $ENV_FILE"
  echo "请先执行: cp deploy/.env.docker.example .env 并填写真实配置"
  exit 1
fi

cd "$ROOT_DIR"

echo "[1/4] 启动容器"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d

echo "[2/4] 等待 Web 容器就绪"
sleep 5

echo "[3/4] 执行数据库迁移"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec web python manage.py migrate

echo "[4/4] 跳过 collectstatic（已在镜像构建阶段完成）"

echo "完成 ✅"
echo "访问: http://localhost:8000/"
echo "如需创建管理员: docker compose --env-file .env -f deploy/docker-compose.yml exec web python manage.py createsuperuser"
