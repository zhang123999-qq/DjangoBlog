# 上传安全 v4：异步隔离扫描（Quarantine Pipeline）

## 目标
将通用文件上传改为可选异步流程：
1. 先落地到隔离区 `uploads/quarantine/...`
2. 由 Celery 任务调用 ClamAV 扫描
3. 扫描通过再转存到正式目录 `uploads/files/...`
4. 前端通过状态接口轮询结果

## 开关配置

```env
UPLOAD_ASYNC_PIPELINE_ENABLED=True
UPLOAD_STATUS_TTL=86400

UPLOAD_CLAMAV_ENABLED=True
UPLOAD_CLAMAV_HOST=127.0.0.1
UPLOAD_CLAMAV_PORT=3310
UPLOAD_CLAMAV_TIMEOUT=5
UPLOAD_CLAMAV_FAIL_CLOSED=True
```

## API 行为

- `POST /api/upload/file/`
  - 异步开关关闭：同步返回 `{location, filename, size}`
  - 异步开关开启：返回 `202` + `{status: pending, upload_id, task_id, status_path}`

- `GET /api/upload/status/{upload_id}/`
  - `pending` / `scanning` / `ready` / `rejected` / `failed`

## 返回示例

### 提交（异步）
```json
{
  "status": "pending",
  "upload_id": "8f...",
  "task_id": "c9...",
  "status_path": "/api/upload/status/8f.../"
}
```

### 就绪
```json
{
  "status": "ready",
  "upload_id": "8f...",
  "location": "/media/uploads/files/2026/03/....pdf"
}
```

## 运行要求

- 需要 Celery worker 正常运行
- 需要 Redis 可用（缓存状态存储）
- 建议同时启用 ClamAV
