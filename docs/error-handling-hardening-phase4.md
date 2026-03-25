# 异常处理分层收敛（阶段 4：统一错误码）

覆盖文件：
- `apps/core/error_codes.py`（新增）
- `apps/core/upload_views.py`
- `apps/core/cache_optimizer.py`
- `moderation/ai_service.py`

## 目标

将任务层、服务层、API 层的错误表达统一为“错误码 + 默认文案”，
让前端、日志、告警规则能够基于同一语义处理。

## 关键改动

1. 新增 `ErrorCodes` 常量与默认文案映射
2. 新增 `api_error_payload(...)` 标准错误响应结构
3. 上传 API 全面切换到统一错误码返回
4. 缓存优化器错误码改为常量引用（消除硬编码字符串）
5. AI 审核服务错误详情增加 `code` 字段

## 标准错误结构

```json
{
  "error_code": "UPLOAD_NO_FILE",
  "error": "没有上传文件",
  "message": "没有上传文件"
}
```

## 收益

- 前端可按 `error_code` 精确分支处理
- 告警平台可按错误码聚合
- 日志、接口、文档三端语义统一
