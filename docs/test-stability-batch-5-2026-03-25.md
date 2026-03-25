# 测试稳定性修复批次-5（2026-03-25）

## 目标

继续扩大“默认可跑且可通过”的后端回归覆盖，聚焦认证与审核接口基础行为。

## 新增文件

- `tests/test_core_backend_suite_auth.py`

## 新增用例（12）

- register/login/logout 基础可访问性
- 用户创建与密码校验
- moderation metrics/approve/reject 未登录访问鉴权
- upload status 受保护或不存在行为
- schema/tools/forum 基础可访问性

## 验证

- `uv run pytest -q tests/test_core_backend_suite_auth.py --maxfail=1` -> `12 passed`
- `uv run pytest -q --maxfail=1` -> `37 passed, 80 skipped, 2 warnings`

## 说明

- warning 主要是 Django 迁移期配置/接口兼容提醒（非阻断）。
- 默认可运行回归集已达到 37 条。