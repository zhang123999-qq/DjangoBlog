# 异常处理分层收敛（阶段 2）

本阶段覆盖：
- `moderation/tasks.py`
- `apps/core/maintenance_tasks.py`

## 目标

1. 对高频任务链路做异常分类（DatabaseError / ImportError / 通用异常）
2. 保持对外返回稳定（不把内部堆栈暴露给调用方）
3. 增强日志可观测性（统一错误日志格式）

## 关键改动

### moderation/tasks.py
- 增加统一日志函数 `_log_task_error(...)`
- `async_moderate_text` / `async_moderate_image` 对数据库异常单独处理并重试
- `get_content_object` 分离数据库异常与未知异常
- `create_moderation_reminder` 增加数据库异常保护
- 日志改为结构化上下文（content_type/content_id/user_id）

### maintenance_tasks.py
- 新增 `_log_task_error(...)` 统一入口
- 各任务从裸 `except Exception` 收敛到 `DatabaseError`/`ImportError` 优先
- `optimize_database` 中 MySQL `OPTIMIZE TABLE` 使用反引号包裹表名
- 全部日志从 f-string 统一为参数化日志

## 预期收益

- 失败任务更容易定位（日志关键字段更完整）
- 避免误把可恢复异常当成不可恢复错误
- 任务链路稳定性更高，重试策略更可控
