# 异常处理分层收敛（阶段 10：Moderation UI Toast）

覆盖文件：
- `static/js/ui-toast.js`（新增）
- `moderation/templates/moderation/dashboard.html`

## 目标

把审核操作反馈从阻塞式 `alert` 升级为非阻塞 Toast，减少打断感。

## 本次改动

1. 新增轻量级 Toast 组件
   - `window.UIToast.show(message, type, timeout)`
   - 支持 `success / error / info`

2. 审核面板接入 Toast
   - 审核通过成功：绿色 Toast
   - 审核拒绝成功：绿色 Toast
   - 操作失败：红色 Toast（带错误码映射文案）

3. 页面刷新优化
   - 成功后延迟约 350ms 刷新，用户能看到反馈

## 效果

- 交互更顺滑，不再弹窗打断
- 错误提示更自然，且和错误码体系一致
