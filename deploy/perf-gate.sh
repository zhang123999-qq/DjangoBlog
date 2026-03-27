#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---smoke}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

if ! command -v k6 >/dev/null 2>&1; then
  echo "[perf] k6 not found. Please install k6 first."
  echo "[perf] macOS: brew install k6"
  echo "[perf] Linux: https://k6.io/docs/get-started/installation/"
  exit 1
fi

echo "[perf] BASE_URL=${BASE_URL}"

if [[ "$MODE" == "--stress" ]]; then
  echo "[perf] running stress profile..."
  k6 run deploy/perf/k6_stress.js -e BASE_URL="$BASE_URL"
else
  echo "[perf] running smoke profile..."
  k6 run tests/perf/k6_smoke.js -e BASE_URL="$BASE_URL"
fi

echo "[perf] PASS"
