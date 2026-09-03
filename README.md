# DjangoBlog

> **博客 + 论坛 + 工具箱 + API** —— 一个面向生产部署的 Django 综合站点

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2%20LTS-green)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](https://www.docker.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-black)](LICENSE)

[快速开始](docs/QUICKSTART.md) · [架构](docs/ARCHITECTURE.md) · [API 文档](docs/API.md) · [部署](docs/CI_DEPLOY.md) · [运维](docs/OPERATIONS.md) · [更新日志](CHANGELOG.md)

</div>

---

## ✨ 核心特性

| 模块 | 功能 |
|------|------|
| 📰 **博客系统** | 文章、分类、标签、评论、点赞、Slug 路由、阅读量统计 |
| 💬 **社区论坛** | 主题、回复、附件、订阅、互动 |
| 🧰 **工具箱** | 68 个在线工具（编码转换、文本处理、加解密、图像） |
| 🔌 **REST API** | 60+ 端点，DRF + OpenAPI 文档 |
| 🔔 **实时通知** | WebSocket 推送（Channels + Redis）|
| 🔍 **全文搜索** | Meilisearch/Elasticsearch（可选）|
| 🛡️ **安全增强** | Axes 登录防护、限流、CSRF、XSS、CSP、内容审核 |
| 🚀 **生产部署** | 5 容器 Docker Compose + Nginx + Gunicorn + CI/CD |
| 🧪 **质量保障** | 45 测试通过、mypy/flake8/bandit/pre-commit |
| 💾 **数据备份** | 定时 mysqldump + 验证 + 恢复脚本 |

---

## 🏗 技术栈

| 层 | 技术 |
|---|---|
| **后端** | Python 3.13 + Django 4.2 LTS + DRF 3.14 + Channels 4.0 |
| **数据** | MySQL 8.0 + Redis 7 + Meilisearch 1.0 |
| **异步** | Celery 5+ |
| **部署** | Docker Compose + Nginx + Gunicorn (gthread) |
| **CI/CD** | GitHub Actions（CI + 自动部署 + 回滚）|
| **质量** | pytest + mypy + flake8 + black + bandit + pre-commit |

---

## 🚀 30 秒快速开始

### Docker 部署（推荐）

```bash
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog
sudo bash deploy/auto-deploy.sh
sudo bash deploy/install_nginx.sh
```

**搞定** ✅ 访问 `http://your-domain`

### 本地开发

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements/development.lock
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

详细：[docs/QUICKSTART.md](docs/QUICKSTART.md)

---

## 📁 项目结构

```
DjangoBlog/
├── apps/                # 7 个业务应用
│   ├── accounts/        # 用户系统
│   ├── blog/            # 博客核心
│   ├── forum/           # 论坛
│   ├── core/            # 公共工具
│   ├── notifications/   # 实时通知
│   ├── tools/           # 工具箱
│   └── api/             # REST API
├── moderation/          # 内容审核
├── config/              # Django 配置（4 套环境）
├── deploy/              # Docker 部署 + 运维脚本
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── auto-deploy.sh   # 一键部署
│   ├── health.sh        # 健康检查
│   ├── backup.sh        # 备份
│   └── install_nginx.sh # Nginx 配置安装
├── requirements/        # 分层依赖
├── docs/                # 项目文档
├── templates/           # Django 模板
├── static/              # 静态资源
└── tests/               # 测试
```

详细：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 📊 项目状态

| 指标 | 数值 |
|---|---|
| **代码量** | ~33,800 行 Python |
| **文件数** | 463 个（276 Python）|
| **API 端点** | 60+ |
| **在线工具** | 68 个 |
| **测试** | 45 通过 |
| **提交** | 297+ |
| **代码质量** | 9.5/10 |
| **生产就绪** | ✅ |

---

## 📚 文档

| 文档 | 内容 |
|---|---|
| [QUICKSTART.md](docs/QUICKSTART.md) | 5 分钟上手（本地 / Docker / 生产）|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构总览、模块设计、数据流 |
| [API.md](docs/API.md) | REST API 完整文档 |
| [CI_DEPLOY.md](docs/CI_DEPLOY.md) | CI/CD 自动部署 |
| [OPERATIONS.md](docs/OPERATIONS.md) | 日常运维速查 |
| [CHANGELOG.md](CHANGELOG.md) | 更新日志 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| [SECURITY.md](SECURITY.md) | 安全政策 |

---

## 🛡️ 安全

- ✅ 通过深度安全审计
- ✅ 非 root 容器运行
- ✅ 端口仅绑定 127.0.0.1
- ✅ 自动密钥生成
- ✅ 依赖定期更新（Dependabot）
- 🔒 如发现安全问题，请查看 [SECURITY.md](SECURITY.md)

---

## 🤝 贡献

欢迎 PR！流程：[CONTRIBUTING.md](CONTRIBUTING.md)

提交前请跑：
```bash
pre-commit run --all-files
pytest
```

---

## 📄 许可证

[MIT License](LICENSE)

---

## 🌟 Star History

如果这个项目对你有帮助，欢迎点 ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=zhang123999-qq/DjangoBlog&type=Date)](https://star-history.com/#zhang123999-qq/DjangoBlog)
