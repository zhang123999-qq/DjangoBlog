# 异常处理分层收敛（阶段 21：自动刷新开关与频率控制）

覆盖文件：
- `moderation/templates/moderation/dashboard.html`

## 目标

为审核指标面板增加自动刷新控制，避免固定频率造成噪音或资源浪费。

## 实现

1. 新增自动刷新开关（switch）
2. 新增刷新间隔选择（15s / 30s / 60s）
3. 新增持久化配置：
   - `moderation.metrics.autoRefresh.v1`
   - `moderation.metrics.refreshInterval.v1`
4. 页面加载时恢复用户上次选择
5. 切换开关/频率时自动重建定时器（`restartMetricsTimer`）

## 说明

- 仍保留手动触发刷新（窗口切换会立即拉取）。
- 关闭自动刷新时不再周期请求 metrics API。