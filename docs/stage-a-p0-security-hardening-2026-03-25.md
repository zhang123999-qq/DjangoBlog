# Stage A（P0）上线阻塞项修复：生产安全配置强制化

## 目标

优先解决上线阻塞项：生产环境安全配置不完整导致 `check --deploy` 高风险告警。

## 本次改动

1. `config/settings/production.py`
- 引入 `ImproperlyConfigured`，采用 fail-fast
- 强制非空：`ALLOWED_HOSTS`、`CSRF_TRUSTED_ORIGINS`
- 强安全默认：
  - `SECURE_SSL_REDIRECT=True`
  - `SESSION_COOKIE_SECURE=True`
  - `CSRF_COOKIE_SECURE=True`
  - `SECURE_HSTS_SECONDS=31536000`
- 支持代理 HTTPS 头：`SECURE_PROXY_SSL_HEADER`
- `SECRET_KEY` 占位符/空值直接阻断启动
- `DEBUG=True` 在生产配置下直接阻断启动

2. `.env.production.example`
- 补齐并默认开启生产安全项（SSL/HSTS/Cookie/Proxy）

3. `deploy/precheck.sh` + `deploy/precheck.bat`
- 新增 P0 安全项必填校验
- 新增预期值校验：
  - `DEBUG=False`
  - `SECURE_SSL_REDIRECT=True`
  - `SESSION_COOKIE_SECURE=True`
  - `CSRF_COOKIE_SECURE=True`
- 新增 `SECURE_HSTS_SECONDS > 0` 校验

## 验证建议

- `python -m py_compile config/settings/production.py`
- `bash deploy/precheck.sh`（或 `deploy\precheck.bat`）
- 在生产环境变量注入后执行：`uv run python manage.py check --deploy`
