#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
THREADS="${THREADS:-4}"
CONNS="${CONNS:-100}"
DURATION="${DURATION:-30s}"

if ! command -v wrk >/dev/null 2>&1; then
  echo "[ERROR] wrk 未安装，请先安装 wrk"
  exit 1
fi

echo "[INFO] BASE_URL=$BASE_URL THREADS=$THREADS CONNS=$CONNS DURATION=$DURATION"

echo "\n=== / ==="
wrk -t"$THREADS" -c"$CONNS" -d"$DURATION" --latency "$BASE_URL/"

echo "\n=== /blog/ ==="
wrk -t"$THREADS" -c"$CONNS" -d"$DURATION" --latency "$BASE_URL/blog/"

echo "\n=== /api/topics/ ==="
wrk -t"$THREADS" -c"$CONNS" -d"$DURATION" --latency "$BASE_URL/api/topics/"

echo "\n=== /api/posts/ ==="
wrk -t"$THREADS" -c"$CONNS" -d"$DURATION" --latency "$BASE_URL/api/posts/"

echo "\n完成 ✅"
