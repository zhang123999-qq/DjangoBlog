# 异常处理分层收敛（阶段 25：指标 CSV 一键导出）

覆盖文件：
- `moderation/templates/moderation/dashboard.html`

## 目标

支持将审核指标导出为 CSV，方便直接导入表格工具做分析。

## 实现

1. 新增按钮：`导出CSV`
2. 基于 `lastMetricsPayload` 生成 CSV 文本
3. 导出内容分两段：
   - `# summary`：窗口摘要指标
   - `# series`：分钟级时序数据
4. 新增 CSV 转义函数（处理逗号、引号、换行）
5. 无可导出数据时 toast 提示

## 文件命名

- `moderation-metrics-{ISO时间戳}.csv`

## 说明

- 纯前端导出，不新增后端接口。