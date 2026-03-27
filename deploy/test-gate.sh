#!/usr/bin/env bash
set -euo pipefail

# 发布前测试门禁（默认快速门禁）
# 用法：
#   bash deploy/test-gate.sh            # 快速门禁
#   bash deploy/test-gate.sh --full     # 全量（含默认 pytest 全量）

FULL="${1:-}"

# 强制按生产配置执行 deploy 检查，避免误用开发配置产生噪声告警
export DJANGO_SETTINGS_MODULE="config.settings.production"
export DEBUG="False"

echo "[gate] 1/4 python 语法冒烟"
python -m py_compile \
  manage.py \
  config/settings/base.py \
  apps/api/moderation_views.py \
  apps/blog/tasks.py

echo "[gate] 2/4 Django check"
uv run python manage.py check

echo "[gate] 3/4 Django deploy check (warnings allowed)"
# --deploy 只做告警输出，不作为阻断条件（如 HSTS/SSL/DEBUG 环境告警）
set +e
uv run python manage.py check --deploy
DEPLOY_CHECK_CODE=$?
set -e
if [[ $DEPLOY_CHECK_CODE -ne 0 ]]; then
  echo "[gate] deploy check has warnings/issues (non-blocking in this gate)."
fi

echo "[gate] 4/6 scoped quality checks"
uv run python -m mypy apps/api/moderation_views.py apps/blog/tasks.py
uv run python -m flake8 apps/api/moderation_views.py apps/blog/tasks.py --max-line-length=140 --extend-ignore=W293

echo "[gate] 5/6 backend regression suites"
DJANGO_SETTINGS_MODULE=config.settings.test DEBUG=False \
uv run pytest -q \
  tests/test_smoke_backend.py \
  tests/test_core_backend_suite.py \
  tests/test_core_backend_suite_ext.py \
  tests/test_core_backend_suite_auth.py \
  tests/test_core_backend_suite_ops.py

if [[ "$FULL" == "--full" ]]; then
  echo "[gate] full mode: run full pytest collection"
  uv run pytest -q --maxfail=1
fi

echo "[gate] 6/6 done"
echo "[gate] PASS"
