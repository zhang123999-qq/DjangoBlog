# Stage B（P1）质量门禁分层与依赖路径收敛

## 目标

- 降低历史类型债务对发布的阻断影响
- 统一 CI 安装路径，减少 pyproject / requirements 双轨漂移

## 本次改动

1. CI 依赖安装路径收敛
- 文件：`.github/workflows/ci.yml`
- 从 `uv pip install -r requirements/development.txt` 改为：
  - `uv sync --extra dev`

2. CI 新增 scoped 质量门禁（发布关键路径）
- mypy：`apps/api/moderation_views.py`, `apps/blog/tasks.py`
- flake8：`apps/api/moderation_views.py`, `apps/blog/tasks.py`

3. 发布门禁脚本同步
- 文件：`deploy/test-gate.sh`, `deploy/test-gate.bat`
- 新增步骤：scoped mypy + scoped flake8

4. 元数据一致性修正
- 文件：`setup.cfg`
- 版本改为 `2.3.1`
- `python_requires` 改为 `>=3.10`（对齐 pyproject）

5. 文档更新
- 文件：`docs/release-gate-matrix-2026-03-25.md`
- 将 scoped mypy/flake8 纳入“必过”

## 验证建议

- `uv sync --extra dev`
- `uv run python -m mypy apps/api/moderation_views.py apps/blog/tasks.py`
- `uv run python -m flake8 apps/api/moderation_views.py apps/blog/tasks.py`
- `deploy\test-gate.bat`（或 `bash deploy/test-gate.sh`）