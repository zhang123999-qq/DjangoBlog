# 异常处理分层收敛（阶段 15：Moderation API 可观测性增强）

覆盖文件：
- `apps/api/moderation_views.py`

## 目标

在阶段 14 的限流/并发保护基础上，补齐可观测性，支持快速定位：
- 谁在高频触发
- 哪个时段被打满
- 成功/失败与耗时分布

## 本次增强

1. 新增轻量分钟桶计数器（基于 cache）
   - `requests_total`
   - `rate_limited`
   - `concurrency_limited`
   - `approve_success` / `approve_failed`
   - `reject_success` / `reject_failed`
   - `permission_denied` / `invalid_content_type` / `content_not_found`

2. 用户维度热点统计
   - key: `moderation:metric:user:{user_id}:{YYYYmmddHHMM}`

3. 并发峰值统计
   - 全局分钟峰值：`moderation:metric:peak_concurrency:{bucket}`
   - 用户分钟峰值：`moderation:metric:peak_concurrency:user:{user_id}:{bucket}`

4. 结构化日志
   - 限流命中：`moderation_api_rate_limited`
   - 并发命中：`moderation_api_concurrency_limited`
   - 处理完成：`moderation_approve_done` / `moderation_reject_done`（含 elapsed_ms）
   - 异常：`moderation_approve_failed` / `moderation_reject_failed`

## 说明

- 该方案为“低侵入、无新依赖”版本，先满足线上诊断诉求。
- 后续可升级为 Prometheus/Sentry 自定义指标上报。