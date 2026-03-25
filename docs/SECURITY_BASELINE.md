# DjangoBlog 安全基线（生产）

> 目标：把“默认安全”写清楚，避免部署遗漏。

## 1) Django/HTTP 安全
- `DEBUG=False`
- `ALLOWED_HOSTS` 明确域名白名单（禁止 `*`）
- `SECURE_SSL_REDIRECT=True`（有反代时配合 `SECURE_PROXY_SSL_HEADER`）
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SESSION_COOKIE_HTTPONLY=True`
- `CSRF_TRUSTED_ORIGINS` 精确配置
- `X_FRAME_OPTIONS=DENY`
- `SECURE_HSTS_SECONDS` > 0（逐步放量）

## 2) 密钥与凭据
- `SECRET_KEY` 使用高强度随机值
- `.env` 不入库
- 数据库/Redis 账号最小权限
- 第三方 API Key（百度审核等）定期轮换

## 3) 登录与滥用防护
- 启用 `django-axes`（失败阈值、锁定时间）
- 评论/点赞/API 加速率限制
- 关键接口加审计日志（IP、UA、用户ID）

## 4) 依赖与供应链
- 固定依赖版本（`uv.lock`）
- 每周检查高危漏洞（pip-audit/safety）
- 生产镜像最小化，禁用不必要工具

## 5) 运维与监控
- 开启错误告警（Sentry）
- Nginx/Gunicorn 超时与连接限制
- 定期备份数据库，演练恢复流程

## 6) 发布前必查
- 参照 `docs/RELEASE_CHECKLIST.md` 全量打勾
