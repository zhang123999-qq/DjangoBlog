#!/usr/bin/env bash
set -euo pipefail

# DjangoBlog 停止脚本 (优化版)
# 用法:
#   bash deploy/down.sh          # 普通停止 (保留数据卷)
#   bash deploy/down.sh --purge  # 停止并删除数据卷

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="$ROOT_DIR/.env"
COMPOSE_ARGS=()
if [ -f "$ENV_FILE" ]; then
  COMPOSE_ARGS=(--env-file "$ENV_FILE")
fi

if [ "${1:-}" = "--purge" ]; then
  echo "[MODE] 停止并删除所有容器、网络、数据卷"
  docker compose "${COMPOSE_ARGS[@]}" -f "$ROOT_DIR/deploy/docker-compose.yml" down -v --rmi all
  docker system prune -f
  echo "已清理完成 (包括数据库)"
else
  echo "[MODE] 普通停止 (保留数据卷，数据不丢失)"
  docker compose "${COMPOSE_ARGS[@]}" -f "$ROOT_DIR/deploy/docker-compose.yml" down
  echo "已停止 (下次执行 up.sh 将重新启动)"
fi
