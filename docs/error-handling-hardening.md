# 异常处理分层收敛（阶段 1）

本次先对审核主链路进行异常处理强化，目标：

1. 减少裸 `except Exception as e` 直接暴露内部信息
2. 统一用户侧错误文案，详细信息只进日志
3. 保留可观测性（`logger.exception`）
4. 通过 `lru_cache` 避免每次重复初始化审核服务

## 改动文件

- `moderation/ai_service.py`

## 关键变更

- 所有审核失败改为统一返回：`审核服务暂时不可用，请稍后重试`
- `logger.error(...)` 升级为 `logger.exception(...)`，保留完整堆栈
- 对第三方返回值增加类型校验（防止非 dict 异常返回）
- `get_moderation_service()` 增加 `@lru_cache(maxsize=1)`

## 下一阶段建议

- `moderation/tasks.py`：拆分数据库异常 / 网络异常 / 逻辑异常
- `apps/core/maintenance_tasks.py`：批处理任务增加分阶段结果上报
- 给关键异常加统一错误码（便于前端与告警平台联动）
