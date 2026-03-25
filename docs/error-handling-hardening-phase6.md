# 异常处理分层收敛（阶段 6：OpenAPI 错误码示例）

覆盖文件：
- `apps/core/upload_views.py`

## 目标

把后端统一错误码同步到 OpenAPI 文档，形成：
- 后端返回（error_code）
- 前端映射（ERROR_MESSAGE_MAP）
- API 文档示例（OpenAPI examples）

三端一致。

## 实现

1. 为上传相关函数视图增加 `@extend_schema`
2. 定义统一错误响应 schema：

```json
{
  "error_code": "UPLOAD_NO_FILE",
  "error": "没有上传文件",
  "message": "没有上传文件"
}
```

3. 在 400/404/500 响应中加入典型错误码示例：
- `UPLOAD_NO_FILE`
- `UPLOAD_IMAGE_TOO_LARGE`
- `UPLOAD_FILE_TOO_LARGE`
- `UPLOAD_FILE_TYPE_DENIED`
- `UPLOAD_SECURITY_SCAN_REJECTED`
- `UPLOAD_SAVE_FAILED`
- `UPLOAD_TASK_NOT_FOUND`

## 收益

- 前端联调可直接按文档写错误分支
- 测试可基于错误码做自动化断言
- 降低“文档与真实返回不一致”风险
