# ⚡ 5 分钟上手 DjangoBlog

> 假设你已经 clone 了项目，最快让 DjangoBlog 跑起来。

---

## 🎯 三种环境

| 环境 | 适用 | 难度 |
|---|---|---|
| **本地开发** | 改代码、调样式、写测试 | ⭐ 简单 |
| **Docker 部署** | 测试、staging、生产 | ⭐⭐ 中等 |
| **生产部署** | 正式上线 + CI/CD | ⭐⭐⭐ 完整 |

---

## 🅰️ 本地开发（5 分钟）

### 1. 创建虚拟环境

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements/development.lock
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少改 SECRET_KEY（用 python -c "import secrets; print(secrets.token_urlsafe(64))"）
```

### 3. 初始化数据库（SQLite 最快）

```bash
# 在 .env 设 DB_ENGINE=django.db.backends.sqlite3
python manage.py migrate
python scripts/init_default_data.py
python manage.py createsuperuser
```

### 4. 启动开发服务器

```bash
python manage.py runserver
# 打开 http://localhost:8000
# Admin: http://localhost:8000/admin/
```

### 5. （可选）启动 Celery + Redis

```bash
# 安装 Redis
brew install redis  # macOS
sudo apt install redis-server  # Ubuntu

# 启动 Redis
redis-server

# 另一个终端，启动 Celery
celery -A config worker -l info
celery -A config beat -l info
```

---

## 🅱️ Docker 一键部署（10 分钟）

### 1. 准备工作

```bash
# 安装 Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog
```

### 2. 一键部署

```bash
sudo bash deploy/auto-deploy.sh
```

按提示输入：
- 域名
- 管理员用户名/邮箱/密码

脚本自动完成：
- ✅ 生成 .env（含随机密钥）
- ✅ 配置 Docker 镜像加速
- ✅ 构建 5 容器镜像
- ✅ 启动 db + redis + web + celery
- ✅ 自动 migrate + collectstatic
- ✅ 创建管理员
- ✅ 健康检查

### 3. 安装 Nginx

```bash
sudo bash deploy/install_nginx.sh
# 或宝塔: sudo bash deploy/install_nginx.sh bt
```

### 4. 访问

```
http://your-domain
http://your-domain/admin/
```

### 5. 查看状态

```bash
bash deploy/health.sh check
bash deploy/health.sh logs
bash deploy/health.sh info
```

---

## 🅲️ 生产 CI/CD 部署（30 分钟）

详见 [CI_DEPLOY.md](CI_DEPLOY.md)

简要流程：
1. 服务器上 clone 项目 + 首次手动部署
2. GitHub 仓库配 6 个 Secrets
3. push 到 main 触发自动部署
4. 失败自动回滚

---

## 🛠 常用命令速查

### Django

```bash
python manage.py makemigrations        # 生成迁移
python manage.py migrate               # 执行迁移
python manage.py createsuperuser       # 创建管理员
python manage.py collectstatic         # 收集静态文件
python manage.py shell                 # 进入 Django Shell
python manage.py test                  # 跑测试
```

### Docker

```bash
# 一键脚本
bash deploy/auto-deploy.sh            # 部署
bash deploy/auto-deploy.sh status     # 状态
bash deploy/auto-deploy.sh update     # 增量更新
bash deploy/auto-deploy.sh restart    # 重启
bash deploy/auto-deploy.sh stop       # 停止

# 原生命令
docker compose -f deploy/docker-compose.yml ps
docker compose -f deploy/docker-compose.yml logs -f web
docker compose -f deploy/docker-compose.yml exec web bash
```

### 备份恢复

```bash
bash deploy/backup.sh                  # 备份
bash deploy/restore.sh --list          # 列出备份
bash deploy/restore.sh --latest        # 恢复最新
bash deploy/health.sh check            # 健康检查
```

### Git

```bash
git status
git add . && git commit -m "..."
git push origin main  # 触发自动部署
```

---

## 📂 关键路径

| 路径 | 内容 |
|---|---|
| `config/settings/` | Django 配置（4 套环境）|
| `apps/` | 7 个业务应用 |
| `moderation/` | 内容审核 |
| `deploy/` | Docker 部署 + 运维脚本 |
| `requirements/` | 分层依赖管理 |
| `docs/` | 文档 |
| `templates/` | Django 模板 |
| `static/` | 静态资源 |

---

## ❓ 遇到问题

| 问题 | 解决 |
|---|---|
| 端口 8000 占用 | 改 `WEB_PORT_EXPOSED` |
| 数据库连不上 | 检查 `.env` 的 `DB_PASSWORD` |
| 静态文件 404 | 跑 `python manage.py collectstatic` |
| Celery 任务不执行 | 检查 Redis + Celery worker 日志 |
| 部署失败 | `bash deploy/health.sh logs` |

---

## 🎓 下一步

- 📖 [ARCHITECTURE.md](ARCHITECTURE.md) - 了解项目结构
- 🔌 [API.md](API.md) - API 文档
- 🚀 [CI_DEPLOY.md](CI_DEPLOY.md) - 部署到生产
- 🛠 [OPERATIONS.md](OPERATIONS.md) - 日常运维
