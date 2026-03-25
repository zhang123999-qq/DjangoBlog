# 异常处理分层收敛（阶段 22：刷新状态与耗时可见化）

覆盖文件：
- `moderation/templates/moderation/dashboard.html`

## 目标

给指标面板增加“刷新健康状态”反馈，便于快速判断 API 拉取是否正常。

## 实现

1. 新增状态栏：`#m-refresh-status`
   - 初始：`状态：待拉取`
   - 刷新中：`状态：刷新中...`
   - 成功：`状态：成功（xxms）`（绿色）
   - 失败（HTTP）：`状态：失败（HTTP xxx，xxms）`（红色）
   - 失败（异常）：`状态：失败（异常，xxms）`（红色）

2. 使用 `performance.now()` 统计单次刷新耗时

## 说明

- 仅前端观测增强，不改变后端接口行为。