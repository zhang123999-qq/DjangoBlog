# 异常处理分层收敛（阶段 14：Moderation API 限速与并发保护）

覆盖文件：
- `apps/api/moderation_views.py`
- `apps/core/error_codes.py`
- `config/settings/base.py`
- `.env.example`
- `.env.production.example`
- `static/js/moderation-api-client.js`

## 目标

给审核 API 增加本地保护层，避免短时间高峰把审核链路打爆。

## 新增配置

```env
MODERATION_API_RATE_LIMIT_PER_MIN=120
MODERATION_API_MAX_CONCURRENCY=20
```

## 保护机制

1. 每用户每分钟限流（rate limit）
2. 每用户并发上限（concurrency guard）
3. 触发时返回 429 + 统一错误码

## 新增错误码

- `MODERATION_API_RATE_LIMITED`
- `MODERATION_API_CONCURRENCY_LIMITED`

## OpenAPI 同步

- moderation approve/reject API 已补 429 响应示例

## 前端同步

- `moderation-api-client.js` 增加上述错误码映射文案
