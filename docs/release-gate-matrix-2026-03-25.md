# 发布前必过矩阵（2026-03-25）

> 目标：把“可发布”标准收敛为可重复执行的门禁流程。

## A. 必过（阻断发布）

1. Python 语法冒烟
- `python -m py_compile manage.py config/settings/base.py apps/api/moderation_views.py apps/blog/tasks.py`

2. Django 基础检查
- `uv run python manage.py check`

3. 后端核心回归（52+ 的子集可快速稳定执行）
- `uv run pytest -q tests/test_smoke_backend.py tests/test_core_backend_suite.py tests/test_core_backend_suite_ext.py tests/test_core_backend_suite_auth.py tests/test_core_backend_suite_ops.py`

## B. 建议过（默认不阻断）

4. 部署安全检查（环境项告警）
- `uv run python manage.py check --deploy`
- 说明：HSTS/SSL/DEBUG/SECRET_KEY 等告警依赖部署环境变量，建议发布前在目标环境清零告警。

5. 全量 pytest（含 skip 统计）
- `uv run pytest -q --maxfail=1`

## 一键命令

- Linux/macOS：`bash deploy/test-gate.sh`
- Windows：`deploy\test-gate.bat`
- 全量模式：追加 `--full`

## 失败分层处置

- **语法失败**：先修语法/残片，再重跑 gate
- **manage.py check 失败**：优先修 import/URL/配置缺失
- **核心回归失败**：按用例归属修复（core/auth/api/ops）
- **deploy check 告警**：按环境配置整改，不阻断本地开发门禁

## 当前基线（本次会话实测）

- `uv run pytest -q --maxfail=1` => `52 passed, 80 skipped, 2 warnings`
- 说明：skipped 主要来自 E2E/live-server 与 legacy 脚本测试，已通过显式开关隔离。