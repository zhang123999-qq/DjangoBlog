# 测试稳定性修复批次-2（2026-03-25）

## 目标

在默认跳过遗留/E2E 后，补充可执行的后端 smoke 测试，确保 pytest 默认运行有“有效通过”结果。

## 改动

1. 新增后端 smoke 用例
- 文件：`tests/test_smoke_backend.py`
- 用例：
  - `test_home_page_ok`
  - `test_blog_list_ok`
  - `test_api_schema_ok`

2. 调整 E2E 跳过判定
- 文件：`tests/conftest.py`
- 仅当用例依赖 `page/context/browser/playwright` fixture 时，默认标记并跳过

## 验证

- `uv run pytest -q tests/test_smoke_backend.py --maxfail=1` -> `3 passed`
- `uv run pytest -q --maxfail=1` -> `3 passed, 80 skipped`

## 说明

- 当前 skipped 主要是 Playwright/live-server 与遗留脚本测试；主链路已可稳定执行并给出通过结果。