# 异常处理分层收敛（阶段 19：阈值配置化与后端下发）

覆盖文件：
- `config/settings/base.py`
- `.env.example`
- `.env.production.example`
- `apps/api/moderation_views.py`
- `moderation/templates/moderation/dashboard.html`

## 目标

将 Phase 18 前端硬编码阈值改为可配置阈值，支持不同环境灵活调参。

## 新增配置

```env
MODERATION_UI_ALERT_RATE_LIMITED=5
MODERATION_UI_ALERT_CONCURRENCY_LIMITED=3
MODERATION_UI_ALERT_FAIL_RATE=0.2
```

## 后端改动

- `/api/moderation/metrics/` 返回新增字段：`thresholds`
  - `rate_limited`
  - `concurrency_limited`
  - `fail_rate`
- OpenAPI 响应模型同步补充 `thresholds`

## 前端改动

- 审核中心指标面板改为使用后端下发阈值进行高亮判断
- 面板新增“告警阈值”展示文案

## 效果

- 阈值调整无需改前端代码，只需改环境变量并重启服务。