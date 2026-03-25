# 异常处理分层收敛（阶段 3）

覆盖文件：
- `apps/core/cache_optimizer.py`
- `moderation/services.py`

## 改动要点

### 1) cache_optimizer 统一错误结构
- 增加 `_log_cache_error(...)` 统一日志入口
- 增加 `_error_payload(...)` 统一错误返回格式（含 `error_code`）
- 关键方法（内存信息、键分析、清理）在失败时返回结构化错误，而不是空字典

### 2) moderation/services 分层异常处理
- 增加 `_log_service_error(...)`
- `approve/reject/auto_approve` 加事务包裹，日志与状态更新原子化
- `create_moderation_reminder` 使用 `get_or_create` 避免并发重复
- `smart_moderate_instance` 的拒绝流程加事务保护
- `ai_batch_moderate` 分离数据库异常和通用异常日志

## 收益
- 错误返回一致，便于前端与任务链路统一处理
- 审核状态与日志写入更一致，降低并发下半成功风险
- 故障定位更快（日志含操作名 + 关键上下文）
