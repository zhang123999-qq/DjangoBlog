# 测试稳定性修复批次-4（2026-03-25）

## 目标

继续从 legacy 场景提炼可运行断言，新增 12 条后端回归用例。

## 新增文件

- `tests/test_core_backend_suite_ext.py`

## 覆盖点（12）

- admin URL 可达
- API posts/categories/tags 可达
- API docs/redoc 在 DEBUG 条件下可见性符合预期
- 首页性能头可见
- CSRF 中间件已启用
- 数据库连接可用与 `SELECT 1`
- User 模型可用
- 关键路由组可访问（home/blog/forum/tools/login/register/api）

## 验证

- `uv run pytest -q tests/test_core_backend_suite_ext.py --maxfail=1` -> `12 passed`
- `uv run pytest -q --maxfail=1` -> `25 passed, 80 skipped, 1 warning`

## 结果

默认可跑并通过的后端回归集显著增加，legacy/e2e 继续保留为显式开关执行。