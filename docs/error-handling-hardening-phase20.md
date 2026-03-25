# 异常处理分层收敛（阶段 20：指标窗口切换与持久化）

覆盖文件：
- `moderation/templates/moderation/dashboard.html`

## 目标

支持在审核中心动态切换指标统计窗口（10/30/60 分钟），并持久化选择。

## 实现

1. 面板头部新增窗口选择器
   - 选项：最近 10/30/60 分钟

2. 指标请求改为动态 minutes
   - `/api/moderation/metrics/?minutes=${minutes}`

3. 状态持久化
   - localStorage key: `moderation.metrics.window.v1`
   - URL query: `mwin`
   - 优先级：URL > localStorage > 默认 10

4. 趋势标题动态化
   - 文案显示当前窗口分钟数

## 效果

- 值班时可快速观察短时突发与中期趋势，且刷新页面后保持上次窗口选择。