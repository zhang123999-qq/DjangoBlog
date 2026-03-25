# 测试稳定性修复批次-6（2026-03-25）

## 目标

继续提升默认可跑后端测试覆盖，冲刺 50+ passed，并修复测试暴露出的真实代码缺陷。

## 新增文件

- `tests/test_core_backend_suite_ops.py`（15 条运维/系统行为回归）

## 用例覆盖（摘要）

- healthz/readiness/liveness JSON 行为
- search/contact/settings 路由行为
- 首页缓存写入
- moderation metrics（staff）
- moderation approve/reject 非法类型错误码
- schema/docs/redoc 在 DEBUG 条件下可见性

## 过程中修复的真实问题

- `apps/api/moderation_views.py` 缺少 `logger` 定义，导致接口 finally 阶段 `NameError`
- 已补：`logger = logging.getLogger(__name__)`

## 验证

- `uv run pytest -q tests/test_core_backend_suite_ops.py --maxfail=1` -> `15 passed`
- `uv run pytest -q --maxfail=1` -> `52 passed, 80 skipped, 2 warnings`

## 结果

默认可运行并通过的后端回归已达到 52 条。