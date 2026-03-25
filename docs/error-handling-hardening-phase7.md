# 异常处理分层收敛（阶段 7：Moderation API 错误码化）

覆盖文件：
- `apps/core/error_codes.py`
- `moderation/views.py`
- `moderation/urls.py`

## 目标

把审核操作（approve/reject）也纳入统一错误码体系，便于：
- 前端按错误码处理提示
- 自动化测试按错误码断言
- 告警按错误码聚合

## 新增错误码

- `MODERATION_INVALID_CONTENT_TYPE`
- `MODERATION_CONTENT_NOT_FOUND`
- `MODERATION_APPROVE_FAILED`
- `MODERATION_REJECT_FAILED`

## 新增接口

- `POST /moderation/api/approve/<content_type>/<content_id>/`
- `POST /moderation/api/reject/<content_type>/<content_id>/`

返回示例：

### 失败
```json
{
  "error_code": "MODERATION_CONTENT_NOT_FOUND",
  "error": "审核对象不存在",
  "message": "审核对象不存在"
}
```

### 成功
```json
{
  "success": true,
  "status": "approved",
  "id": 123
}
```

## 备注

原页面模式（dashboard + approve/reject 跳转）保持兼容，新增 API 模式用于异步前端或后台工具调用。
