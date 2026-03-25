# 异常处理分层收敛（阶段 9：Moderation 前端 SDK）

覆盖文件：
- `static/js/moderation-api-client.js`（新增）
- `moderation/templates/moderation/dashboard.html`
- `apps/api/moderation_views.py`（小修，兼容 request.data）

## 目标

把 moderation API 的错误码能力延伸到前端，形成完整链路：

后端错误码 → 前端 SDK 映射 → 审核 UI 精准提示

## 本次实现

1. 新增前端 SDK `ModerationApiClient`
   - `approve(contentType, contentId)`
   - `reject(contentType, contentId, reviewNote)`
   - `getErrorMessage(err)`
   - 内置错误码映射（权限不足、内容不存在、类型错误、审核操作失败）

2. 审核面板接入 SDK
   - Dashboard 的通过/拒绝按钮增加 `data-*` 属性
   - 有 JS 时走 API，无 JS 时仍走原链接（渐进增强）
   - 操作后自动刷新，失败展示错误码映射文案

3. 请求体兼容增强
   - `request.data` 读取改为 `hasattr(request.data, 'get')`

## 收益

- 审核页面用户体验更顺滑（无需跳转到拒绝页）
- 错误提示更准确可理解
- API 文档、后端返回、前端提示三端一致
