# DjangoBlog

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Django](https://img.shields.io/badge/Django-4.2%20LTS-green)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1)
![Redis](https://img.shields.io/badge/Redis-7-DC382D)
![License](https://img.shields.io/badge/License-MIT-black)

一个面向生产部署的 Django 综合站点：**博客 + 论坛 + 工具箱 + API**。  
强调「可用性、可维护性、可部署性」，适合个人站点、中小团队内容平台与教学演示。

</div>

---

## ✨ 项目亮点

- 📰 **内容系统**：博客文章、分类、评论、点赞、Slug 路由
- 💬 **社区模块**：论坛主题、回复、互动链路
- 🧰 **工具箱模块**：72 个实用工具（编码转换、文本处理、加解密、图像类等）
- 🔌 **API 能力**：Django REST Framework + OpenAPI 文档支持
- 🛡️ **安全增强**：安全响应头、限流、登录防护（Axes）、基础内容审核机制
- 🚀 **生产部署友好**：Docker Compose / Nginx / Gunicorn / MySQL / Redis
- 🧪 **质量保障**：Django checks、迁移检查、回归测试基线

---

## 🧱 技术栈

### Backend
- Python 3.13
- Django 4.2 LTS
- Django REST Framework
- Celery（异步任务）

### Data & Middleware
- MySQL 8
- Redis 7

### Deploy
- Docker & Docker Compose
- Nginx
- Gunicorn

### Engineering
- pytest
- mypy
- flake8

---

## 📁 项目结构

```text
DjangoBlog/
├─ apps/                    # 业务应用
│  ├─ accounts/             # 用户与认证
│  ├─ blog/                 # 博客
│  ├─ forum/                # 论坛
│  ├─ tools/                # 工具箱
│  ├─ api/                  # API 层
│  └─ core/                 # 公共能力（安全、中间件、工具函数等）
├─ config/                  # Django 配置（settings/urls/wsgi/asgi/celery）
├─ deploy/                  # Dockerfile、compose、nginx、部署脚本
├─ requirements/            # base / development / production 依赖分层
├─ templates/               # 模板
├─ static/                  # 静态资源（源）
├─ docs/                    # 项目文档
└─ tests/                   # 测试用例
```

---

## 🚀 快速开始（Docker，推荐）

> 适合生产/准生产环境验证。

### 1) 准备环境变量

复制并编辑 `.env`（确保是生产配置）：

- `DEBUG=False`
- `ALLOWED_HOSTS` 填真实域名
- `CSRF_TRUSTED_ORIGINS` 填 `https://你的域名`
- 设置强随机 `SECRET_KEY` / DB 密码

### 2) 启动服务

```bash
cd C:\Users\Administrator\.openclaw\workspace\DjangoBlog

docker compose --env-file .env -f deploy/docker-compose.yml config
docker compose --env-file .env -f deploy/docker-compose.yml build --no-cache
docker compose --env-file .env -f deploy/docker-compose.yml up -d
```

### 3) 初始化项目

```bash
docker compose --env-file .env -f deploy/docker-compose.yml exec web python manage.py migrate
docker compose --env-file .env -f deploy/docker-compose.yml exec web python manage.py collectstatic --noinput
docker compose --env-file .env -f deploy/docker-compose.yml exec web python manage.py check --deploy
```

### 4) 运行状态检查

```bash
docker compose --env-file .env -f deploy/docker-compose.yml ps
docker compose --env-file .env -f deploy/docker-compose.yml logs -f --tail=200
```

---

## 🧑‍💻 本地开发（非 Docker）

```bash
uv venv
uv pip install -r requirements/development.txt
python manage.py migrate
python manage.py runserver
```

常用检查：

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q
```

---

## 🔐 安全扫描工具安装

为了让 `deploy/test-gate.(bat|sh)` 的可选安全扫描不再 skip，可先安装工具：

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File deploy\install-security-tools.ps1
# 如需尝试自动安装 gitleaks：
powershell -ExecutionPolicy Bypass -File deploy\install-security-tools.ps1 -WithGitleaks
```

### Linux/macOS

```bash
bash deploy/install-security-tools.sh
# 如需尝试安装 gitleaks：
bash deploy/install-security-tools.sh --with-gitleaks
```

安装后门禁会自动执行：`bandit`、`pip-audit`、`gitleaks`（存在即执行）。

## 🔐 生产部署建议

- 使用 HTTPS 反代（Nginx / Ingress）
- 保持以下安全项开启：
  - `SECURE_SSL_REDIRECT=True`
  - `SESSION_COOKIE_SECURE=True`
  - `CSRF_COOKIE_SECURE=True`
  - `SECURE_HSTS_SECONDS > 0`
- 数据库与 Redis 使用内网访问，限制暴露面
- 发布前固定执行：`python manage.py check --deploy`

---

## 📌 路线图（Roadmap）

- [ ] 完整 CI 工作流（lint + tests + deploy checks）
- [ ] 统一 API 权限策略与审计日志
- [ ] 前端页面体验与主题体系持续优化
- [ ] 监控告警（Prometheus / Sentry）进一步完善

---

## 🤝 贡献指南

欢迎 Issue / PR：

1. Fork 仓库并创建功能分支
2. 提交前执行测试与检查
3. 提交 PR 并说明改动动机与验证结果

---

## ⚡ 压力测试（k6）

已内置 k6 压测脚本：

- `deploy/perf/k6_smoke.js`（轻量压测）
- `deploy/perf/k6_stress.js`（分阶段并发压测）
- `deploy/perf-gate.bat` / `deploy/perf-gate.sh`（一键执行）

### 安装 k6

Windows:

```powershell
winget install k6.k6
```

macOS:

```bash
brew install k6
```

### 运行

```bash
# 默认 smoke
BASE_URL=http://127.0.0.1:8000 bash deploy/perf-gate.sh
# Windows
set BASE_URL=http://127.0.0.1:8000 && deploy\perf-gate.bat

# stress
bash deploy/perf-gate.sh --stress
# Windows
set BASE_URL=http://127.0.0.1:8000 && deploy\perf-gate.bat --stress
```

## 📄 License

MIT
