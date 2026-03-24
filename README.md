<div align="center">

# Django Blog

**现代化 Django 4.2 博客论坛系统**

集成智能审核 · 85+ 在线工具 · 富文本编辑器

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-green?logo=django)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)
[![Version](https://img.shields.io/badge/Version-2.3.1-orange)](./docs/更新日志.md)

</div>

---

## ✨ 核心特性

| 模块 | 功能 |
|------|------|
| 📝 **博客系统** | Markdown 支持、分类标签、评论互动、草稿箱 |
| 💬 **论坛系统** | 话题讨论、版块管理、点赞收藏 |
| 🛠️ **在线工具** | 85+ 实用工具（JSON 格式化、IP 检测、NAT 检测等） |
| 👤 **用户系统** | 注册登录、个人中心、社交功能 |
| 🤖 **智能审核** | AI 内容审核（百度 API）、用户信誉系统 |
| 🔌 **REST API** | 完整 API 接口，支持 Token 认证 |

## 🚀 性能优化（v2.3.1）

| 优化项 | 收益 | 说明 |
|--------|------|------|
| 浏览量 Redis 化 | DB 写入 **-80%** | Redis 计数 + 5 分钟同步 |
| N+1 查询修复 | 查询 **-70%** | select_related + prefetch_related |
| 工具懒加载 | 性能 **+90%** | 缓存 1 小时，按需加载 |
| 速率限制 | 防滥用 | 评论 10/min，点赞 30/min |
| Sentry APM | 异常监控 | 实时错误追踪 |
| 健康检查 | K8s 就绪 | healthz/readiness/liveness 端点 |

## 🛡️ 安全加固

- **CSP 安全头** - Content Security Policy 防止 XSS
- **HSTS** - Strict Transport Security 强制 HTTPS
- **Cookie 安全** - Secure + HttpOnly + SameSite
- **CSRF 保护** - 跨站请求伪造防护
- **速率限制** - 防止暴力破解和垃圾内容

## 📋 环境要求

| 组件 | 版本 |
|------|------|
| Python | 3.10+ |
| Django | 4.2 LTS |
| Redis | 5.0+ |
| 数据库 | MySQL 8.0+ / PostgreSQL 12+ / SQLite 3 |

## 🔧 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog
```

### 2. 安装依赖

```bash
# 推荐：使用 uv
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 3. 配置环境

```bash
cp .env.example .env
# 编辑 .env 配置数据库、Redis、密钥等
```

### 4. 初始化

```bash
uv run python manage.py migrate          # 数据库迁移
uv run python manage.py createsuperuser  # 创建管理员
uv run python manage.py collectstatic    # 收集静态文件
```

### 5. 启动服务

```bash
# 开发环境
uv run python manage.py runserver

# 生产环境
uv run gunicorn config.wsgi:application

# Celery Worker
celery -A config worker -l info

# Celery Beat（定时任务）
celery -A config beat -l info
```

## 📁 目录结构

```
DjangoBlog/
├── apps/           # 应用模块
│   ├── accounts/   # 用户认证
│   ├── blog/       # 博客系统
│   ├── forum/      # 论坛系统
│   ├── tools/      # 在线工具（85+）
│   ├── api/        # REST API
│   ├── moderation/ # 内容审核
│   └── core/       # 核心功能
├── config/         # 配置文件
├── templates/      # 模板文件
├── static/         # 静态文件
├── docs/           # 项目文档
└── scripts/        # 脚本文件
```

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEBUG` | 调试模式 | `True` |
| `SECRET_KEY` | Django 密钥 | *(必填)* |
| `ALLOWED_HOSTS` | 允许的主机 | `localhost,127.0.0.1` |
| `DATABASE_URL` | 数据库 URL | SQLite |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `SENTRY_DSN` | Sentry 监控 | *(可选)* |
| `CSP_ENABLED` | CSP 安全头 | `True` |

### Celery 定时任务

| 任务 | 频率 | 说明 |
|------|------|------|
| `sync_views_to_db` | 5 分钟 | 同步浏览量到数据库 |
| `update_hot_posts` | 1 小时 | 更新热门文章 |
| `cleanup_expired_sessions` | 1 小时 | 清理过期 Session |
| `warmup_cache` | 6 小时 | 缓存预热 |
| `check_redis_health` | 5 分钟 | Redis 健康检查 |

## 📊 健康检查端点

| 端点 | 用途 | 响应 |
|------|------|------|
| `/healthz/` | 综合检查 | DB + Cache 状态 |
| `/readiness/` | 就绪检查 | K8s 流量路由 |
| `/liveness/` | 存活检查 | K8s 进程健康 |

## 🔗 访问地址

| 功能 | 地址 |
|------|------|
| 首页 | http://localhost:8000/ |
| 博客 | http://localhost:8000/blog/ |
| 论坛 | http://localhost:8000/forum/ |
| 工具 | http://localhost:8000/tools/ |
| API | http://localhost:8000/api/ |
| 后台 | http://localhost:8000/admin/ |

## 📈 更新日志

- **v2.3.1** (2026-03-24) - 性能优化 + 安全加固
- **v2.3.0** (2026-03-22) - 性能监控 + 资源管理
- **v2.2.0** (2026-03-21) - Celery + AI 审核

详见 [更新日志](./docs/更新日志.md)

## 📜 License

[MIT License](./LICENSE)

## 🤝 贡献

欢迎 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

<div align="center">

**版本** 2.3.1 · **更新** 2026-03-24

Made with ❤️ by [zhang123999-qq](https://github.com/zhang123999-qq)

</div>
