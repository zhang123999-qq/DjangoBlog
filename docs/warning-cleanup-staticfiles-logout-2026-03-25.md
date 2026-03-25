# 告警清理：STATICFILES_STORAGE 弃用 + Logout GET 弃用

## 目标

清理两项框架升级告警：
1. `STATICFILES_STORAGE` 弃用（Django 5.1 方向）
2. `Logout via GET` 弃用（Django 5.0 方向）

## 改动

1. `config/settings/development.py`
- 从 `STATICFILES_STORAGE` 迁移到 `STORAGES['staticfiles']`

2. `config/settings/production.py`
- 从 `STATICFILES_STORAGE` 迁移到 `STORAGES['staticfiles']`
- 保留 WhiteNoise 的 `CompressedManifestStaticFilesStorage`

3. `apps/accounts/views.py`
- 新增 `logout_view`：仅允许 `POST`，GET 返回 405

4. `apps/accounts/urls.py`
- `accounts/logout/` 路由改为指向 `views.logout_view`

5. `templates/includes/navbar.html`
- 退出登录由链接改为 `POST form + CSRF`

## 验证

- `uv run pytest -q --maxfail=1` -> `52 passed, 80 skipped`
- 不再出现两项历史 warning
- 生产环境：`uv run python manage.py check --deploy` -> `0 issues`（在安全变量注入下）