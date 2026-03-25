# 测试稳定性修复批次-3（2026-03-25）

## 目标

在不依赖 live-server 的前提下，补齐一组可持续运行的核心回归用例（10项），降低默认 skipped 占比对信心的影响。

## 新增文件

- `tests/test_core_backend_suite.py`

## 新增用例（10）

1. 首页可访问
2. 登录页可访问
3. 注册页可访问
4. 博客列表可访问
5. 论坛列表可访问
6. 工具列表可访问
7. API Root 可访问
8. API Schema 可访问
9. 安全响应头存在（X-Frame-Options / X-Content-Type-Options）
10. 缓存读写回环

## 验证

- `uv run pytest -q tests/test_core_backend_suite.py --maxfail=1` -> `10 passed`
- `uv run pytest -q --maxfail=1` -> `13 passed, 80 skipped`

## 说明

- skipped 仍主要来自 Playwright/live-server 与遗留脚本测试；但默认链路已有稳定“可通过”核心回归集。