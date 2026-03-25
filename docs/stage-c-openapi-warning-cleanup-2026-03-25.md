# Stage C：check --deploy 警告收敛（OpenAPI）

## 目标

清理 `manage.py check --deploy` 中由 drf-spectacular 产生的 W001/W002 警告，达到可接受发布基线。

## 本次改动

1. `apps/api/moderation_views.py`
- 为 approve/reject/metrics 接口补齐明确 schema：
  - `ApproveRequestSerializer`
  - `RejectRequestSerializer`
  - `ApproveSuccessSerializer`
  - `RejectSuccessSerializer`
  - `MetricsSerializer`
- `@extend_schema` 统一改为 serializer 驱动，避免 fallback 推断失败

2. `apps/core/upload_views.py`
- 为 upload_image/upload_file 显式声明 multipart request schema：
  - `request={'multipart/form-data': UploadImageRequestSerializer}`
  - `request={'multipart/form-data': UploadFileRequestSerializer}`

## 验证

在生产安全环境变量注入下执行：

```powershell
$env:DJANGO_SETTINGS_MODULE='config.settings.production'
$env:SECRET_KEY='prod-very-long-secret-key-abcdefghijklmnopqrstuvwxyz-1234567890'
$env:ALLOWED_HOSTS='example.com'
$env:CSRF_TRUSTED_ORIGINS='https://example.com'
$env:SECURE_SSL_REDIRECT='True'
$env:SESSION_COOKIE_SECURE='True'
$env:CSRF_COOKIE_SECURE='True'
$env:SECURE_HSTS_SECONDS='31536000'
uv run python manage.py check --deploy
```

结果：`System check identified no issues (0 silenced).`