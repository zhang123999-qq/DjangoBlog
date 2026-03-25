# 稳定性修复批次（P0 + P1）

日期：2026-03-25

## 修复范围

### P0
1. 依赖缺失导致 `manage.py check` 无法启动
   - 现象：`ModuleNotFoundError: No module named 'environ'`
   - 处理：统一补齐 `pyproject.toml` 的核心依赖，并 `uv sync`

2. 审核面板脚本早退导致 metrics 不执行
   - 处理：将 dashboard 脚本早退条件改为“仅当既无指标面板、也无审核动作可执行时才退出”

### P1
3. Redis `cache.keys` 风险替换
   - `apps/blog/tasks.py`：改为 `iter_keys`（有则用），避免 KEYS 阻塞
   - `apps/api/moderation_views.py`：热点用户统计改为 `iter_keys`（有则用）

4. CI Node 版本升级
   - `.github/workflows/ci.yml` 中 Node 语法检查步骤由 `20` 升级为 `22`

## 验证

- `python -m py_compile apps/api/moderation_views.py apps/blog/tasks.py config/settings/base.py` ✅
- `uv run python manage.py check` ✅（0 issue）
- `uv run python manage.py check --deploy` ⚠️（剩余部署告警为环境安全项与 OpenAPI 警告，非本批次阻断）

## 说明

- 本批次为本地修复，未推送远端。