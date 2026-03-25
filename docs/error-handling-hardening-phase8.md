# 异常处理分层收敛（阶段 8：Moderation OpenAPI 化）

覆盖文件：
- `apps/api/moderation_views.py`（新增）
- `apps/api/urls.py`
- `apps/core/error_codes.py`

## 目标

把审核通过/拒绝能力纳入 API 层，并提供 OpenAPI 示例文档，和上传接口保持同一风格：
- 权限校验
- 统一错误码返回
- OpenAPI 响应示例

## 新增 API

- `POST /api/moderation/approve/{content_type}/{content_id}/`
- `POST /api/moderation/reject/{content_type}/{content_id}/`

## 常见错误码

- `MODERATION_PERMISSION_DENIED`
- `MODERATION_INVALID_CONTENT_TYPE`
- `MODERATION_CONTENT_NOT_FOUND`
- `MODERATION_APPROVE_FAILED`
- `MODERATION_REJECT_FAILED`

## 收益

- 前端联调可直接基于 OpenAPI 示例实现分支逻辑
- 审核 API 与上传 API 错误码体系一致
- 便于自动化测试与错误告警聚合
