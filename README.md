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

## 🚀 快速开始

### 一键自动部署（推荐）

> 支持：阿里云、腾讯云、华为云、飞牛 NAS 等主流环境  
> 前置条件：已安装 Docker 和 Docker Compose

```bash
# 1. 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 2. 一键部署
bash deploy/auto-deploy.sh
```

**脚本自动完成：**

| 步骤 | 功能 |
|------|------|
| 1️⃣ | 自动生成 `.env` 配置文件（含随机 SECRET_KEY） |
| 2️⃣ | 配置 Docker 镜像加速（国内环境自动启用） |
| 3️⃣ | 预拉取基础镜像（python、mysql、redis、nginx） |
| 4️⃣ | 构建应用镜像 |
| 5️⃣ | 启动所有服务（Web、MySQL、Redis、Celery、Nginx） |
| 6️⃣ | 自动执行数据库迁移 |
| 7️⃣ | 交互式创建管理员账户 |

**部署完成后：**

- 🌐 网站首页：`http://你的服务器IP`
- 🛠 管理后台：`http://你的服务器IP/admin/`

---

### 手动分步部署

#### 1) 准备环境变量

复制并编辑 `.env`：

```bash
# 参考项目根目录 .env.example
cp .env.example .env
```

必填项：
- `SECRET_KEY`：强随机字符串
- `ALLOWED_HOSTS`：服务器 IP 或域名
- `DEBUG=False`

#### 2) 构建镜像并启动

```bash
docker compose --env-file .env -f deploy/docker-compose.yml build
docker compose --env-file .env -f deploy/docker-compose.yml up -d
```

> ⚠️ 不推荐 `--no-cache`，除非修改了 Python 依赖或基础镜像变更。

#### 3) 数据库迁移

> `collectstatic` 已在 Dockerfile 构建时完成，无需手动执行。

```bash
# 运行一次性迁移容器
docker compose --env-file .env -f deploy/docker-compose.yml up migrate
```

#### 4) 创建管理员账户

```bash
docker compose --env-file .env -f deploy/docker-compose.yml exec web python manage.py createsuperuser
```

#### 5) 检查运行状态

```bash
docker compose --env-file .env -f deploy/docker-compose.yml ps
docker compose --env-file .env -f deploy/docker-compose.yml logs -f --tail=50
```

---

## 🧑‍💻 本地开发（非 Docker）

先在 `.env` 设置：

- `DEPLOY_MODE=host`（让检查跳过 Docker 必选项）
- 确保 `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME` 可真实访问 MySQL

```bash
uv venv
uv pip install -r requirements/development.txt
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

常用检查：

```bash
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest -q
```

---

## 🔐 生产安全配置

### 纯 HTTP 部署（无 SSL 证书）

保持以下配置为 `False`（`.env` 中的默认值）：

```env
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

### HTTPS 部署（有 SSL 证书）

在 Nginx 配置 443 端口并指向证书文件后，在 `.env` 中切换：

```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 通用建议

- 使用 HTTPS 反代（Nginx / Ingress）
- 保持 `SECURE_HSTS_SECONDS > 0`
- 数据库与 Redis 使用内网访问，限制暴露面
- 发布前执行：`docker compose -f deploy/docker-compose.yml exec web python manage.py check --deploy`

---

## 🛑 运维命令速查

```bash
# 启动所有服务
bash deploy/up.sh           # Linux
deploy\up.bat               # Windows（本地开发）

# 停止服务（保留数据卷）
bash deploy/down.sh        # Linux
deploy\down.bat            # Windows（本地开发）

# 彻底清理（包括数据卷）
bash deploy/down.sh --purge

# 查看日志
docker compose -f deploy/docker-compose.yml logs -f --tail=50

# 重启某个服务
docker compose -f deploy/docker-compose.yml restart web

# 进入容器调试
docker compose -f deploy/docker-compose.yml exec web bash
```

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

## 🧹 最近维护（2026-04-01）

- 新增一键自动部署脚本 `deploy/auto-deploy.sh`（自动生成 .env + 拉起服务）
- 清理部署目录：移除 19 个与 Docker 无关的测试/性能/本地工具脚本
- 修复 Docker 部署高危问题：
  - `SECURE_SSL_REDIRECT` / `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` 默认改为 False
  - 重命名 `SecurityMiddleware` → `SecurityMonitorMiddleware` 解决中间件重名
  - 修复 Dockerfile 中 collectstatic 目录权限问题
- 测试基线：`uv run pytest -q`（79 passed / 80 skipped）
- 新增页脚备案号一键脚本：`scripts/set_beian_footer.py`

---

## 📄 License

MIT
