# 异常处理分层收敛（阶段 5：前端错误码映射）

覆盖文件：
- `static/js/upload-async-client.js`
- `static/js/editor-init.js`
- `static/js/admin-editor.js`

## 目标

让前端基于后端 `error_code` 返回精准提示，而不是统一“上传失败”。

## 关键改动

1. 上传客户端新增 `ERROR_MESSAGE_MAP`
2. 新增 `toUploadError(...)`，将后端错误结构转换为标准 Error（含 `code/status/raw`）
3. 轮询 rejected/failed 状态映射为统一错误码
4. 暴露 `UploadAsyncClient.getErrorMessage(err)` 供 UI 层直接调用
5. 编辑器与管理后台统一改为使用 `getErrorMessage` 展示错误

## 用户体验变化

- 超限提示更准确（5MB / 10MB）
- 文件类型不支持、危险文件头、安全扫描拒绝分别提示
- 任务过期与超时提示可区分

## 结果

实现了“后端错误码 → 前端文案”的一致闭环。
