# 异常处理分层收敛（阶段 18：指标趋势与阈值高亮）

覆盖文件：
- `moderation/templates/moderation/dashboard.html`

## 目标

在 Phase 17 指标面板上增加“趋势可视化 + 异常高亮”，让值班同学一眼识别风险波动。

## 实现

1. 新增趋势图（canvas sparkline）
   - 数据源：`/api/moderation/metrics/?minutes=10` 返回的 `series`
   - 绘制三条线：请求量（蓝）、限流命中（红）、并发命中（橙）

2. 新增阈值高亮（红框）
   - `rate_limited >= 5`
   - `concurrency_limited >= 3`
   - 失败率 `(approve_failed + reject_failed)/max(requests_total,1) >= 20%`

3. 保留 30 秒自动刷新机制

## 说明

- 仅前端展示增强，不影响审核接口主流程。
- 指标接口失败仍静默降级。