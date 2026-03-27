# DjangoBlog

一个基于 **Django 4.2 LTS** 的综合站点项目，包含：
- 博客（Blog）
- 论坛（Forum）
- 工具集合（Tools）
- 基础 API（DRF）

---

## 技术栈

- Python 3.13
- Django 4.2
- MySQL 8
- Redis 7
- Nginx
- Docker Compose
- Gunicorn

---

## 快速启动（Docker）

```bash
cd C:\Users\Administrator\.openclaw\workspace\DjangoBlog

docker compose --env-file .env -f deploy/docker-compose.yml config
docker compose --env-file .env -f deploy/docker-compose.yml build --no-cache
docker compose --env-file .env -f deploy/docker-compose.yml up -d

docker compose --env-file .env -f deploy/docker-compose.yml exec web python manage.py migrate
docker compose --env-file .env -f deploy/docker-compose.yml exec web python manage.py collectstatic --noinput
docker compose --env-file .env -f deploy/docker-compose.yml exec web python manage.py check --deploy
```

查看运行状态：

```bash
docker compose --env-file .env -f deploy/docker-compose.yml ps
docker compose --env-file .env -f deploy/docker-compose.yml logs -f --tail=200
```

---

## 生产环境注意事项

1. `.env` 必须使用生产配置：
   - `DEBUG=False`
   - 配置真实 `ALLOWED_HOSTS`
   - 配置真实 `CSRF_TRUSTED_ORIGINS`（https）
2. 请使用强随机 `SECRET_KEY` 与数据库密码
3. 上线前执行 `manage.py check --deploy`

---

## 项目目录（核心）

```text
apps/                # 业务应用（accounts/blog/forum/tools/api/core）
config/              # Django settings / URL / WSGI / ASGI / Celery
deploy/              # Dockerfile、compose、nginx、部署脚本
requirements/        # base / development / production 依赖清单
templates/           # 前端模板
static/              # 静态资源
```

---

## 本地开发（非 Docker）

```bash
uv venv
uv pip install -r requirements/development.txt
python manage.py migrate
python manage.py runserver
```

---

## License

MIT
