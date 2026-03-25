#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/docker-compose.yml"
ENV_FILE="$ROOT_DIR/.env"

# 用法:
#   bash deploy/down.sh          # 普通停止（保留数据卷）
#   bash deploy/down.sh --purge  # 停止并删除数据卷
PURGE="${1:-}"

cd "$ROOT_DIR"

COMPOSE_ARGS=( -f "$COMPOSE_FILE" )
if [ -f "$ENV_FILE" ]; then
  COMPOSE_ARGS=( --env-file "$ENV_FILE" -f "$COMPOSE_FILE" )
else
  echo "[WARN] 未找到 $ENV_FILE，将使用默认 compose 环境"
fi

if [ "$PURGE" = "--purge" ]; then
  echo "[MODE] 停止并删除容器/网络/数据卷"
  docker compose "${COMPOSE_ARGS[@]}" down -v
else
  echo "[MODE] 普通停止（保留数据卷）"
  docker compose "${COMPOSE_ARGS[@]}" down
fi

echo "完成 ✅"
