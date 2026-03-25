# 异常处理分层收敛（阶段 24：指标 JSON 一键导出）

覆盖文件：
- `moderation/templates/moderation/dashboard.html`

## 目标

支持在审核面板一键导出当前指标快照，便于留档、复盘、跨团队同步。

## 实现

1. 面板头部新增按钮：`导出JSON`
2. 成功刷新后缓存最近一次指标数据（`lastMetricsPayload`）
3. 点击导出时生成下载文件：
   - 文件名：`moderation-metrics-{ISO时间戳}.json`
   - 内容包含：
     - `exported_at`
     - `page`
     - `data`（metrics API 原始返回）
4. 无可导出数据时给出 toast 提示（先等待一次成功刷新）

## 说明

- 纯前端导出，不新增后端接口。
- 不影响审核主流程。