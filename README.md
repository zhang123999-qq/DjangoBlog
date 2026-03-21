# DjangoBlog v2.2.0

🚀 一个基于 Django 4.2 LTS 的现代化博客论坛系统，集成 60+ 在线工具，支持智能内容审核

[![Django](https://img.shields.io/badge/Django-4.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Celery](https://img.shields.io/badge/Celery-5.4-orange.svg)](https://docs.celeryq.dev/)

## ✨ 功能特性

### 📝 博客系统
- 文章发布、编辑、删除
- Markdown 支持
- 分类和标签管理
- 文章搜索
- 点赞和评论

### 💬 论坛系统
- 多版块讨论区
- 话题创建和回复
- 用户互动
- 智能内容审核

### 🛡️ 智能审核系统（NEW!）
- **用户信誉系统** - 基于行为的智能分级
- **AI 内容审核** - 百度内容审核 API 集成
- **多级审核策略** - 高信誉自动发布，低信誉强制人工审核
- **敏感词检测** - 支持分类、缓存
- **图片审核** - AI 图片违规检测
- **异步处理** - Celery 异步队列，不阻塞请求

### 🔧 在线工具栏（60+ 工具）
- **加密解密**: AES、RSA、Base64、MD5、SHA、HMAC
- **编码转换**: URL编码、Unicode、HTML实体
- **文本处理**: 字数统计、大小写转换、中文繁简转换
- **生成工具**: UUID、密码、二维码、条形码
- **数据转换**: JSON格式化、CSV/JSON互转
- **时间工具**: 时间戳转换、时差计算
- **图片工具**: 图片Base64、EXIF信息
- **网络工具**: IP查询、端口扫描、HTTP请求
- **更多工具**: BMI计算器、正则测试、JSONPath...

### 👤 用户系统
- 用户注册/登录
- 第三方登录（可扩展）
- 个人资料管理
- 头像上传
- 信誉积分

### 🔒 安全特性
- CSRF 防护
- XSS 过滤
- SQL 注入防护
- 密码强度验证
- 登录频率限制
- 敏感词过滤

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **后端框架** | Django 4.2 LTS |
| **异步队列** | Celery 5.4 |
| **消息队列** | Redis |
| **数据库** | SQLite / MySQL |
| **缓存** | Redis |
| **API** | Django REST Framework |
| **前端** | Bootstrap 5.3 |
| **图标** | Bootstrap Icons |
| **富文本** | CKEditor |
| **AI 审核** | 百度内容审核 API |

## 📦 快速开始

### 环境要求

- Python 3.10+
- Redis (可选，用于缓存)

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 创建虚拟环境
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
uv pip install -r requirements/development.txt

# 数据库迁移
python manage.py migrate

# 创建管理员
python manage.py createsuperuser

# 启动服务
python manage.py runserver
```

访问 http://127.0.0.1:8000 即可看到网站

## 📁 项目结构

```
DjangoBlog/
├── apps/                   # Django 应用
│   ├── accounts/          # 用户账户
│   ├── api/               # REST API
│   ├── blog/              # 博客功能
│   ├── core/              # 核心功能
│   ├── forum/             # 论坛功能
│   ├── install/           # 安装向导
│   └── tools/             # 工具栏
├── config/                # 配置文件
├── static/                # 静态文件
├── templates/             # 模板文件
├── tests/                 # 测试文件
└── requirements/          # 依赖管理
```

详细结构请查看 [项目结构文档](docs/PROJECT_STRUCTURE.md)

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行安全测试
pytest tests/test_security.py -v

# 生成 HTML 报告
pytest tests/ -v --html=tests/report.html --self-contained-html
```

## 🚀 部署

### Docker 部署

```bash
docker-compose up -d
```

### 传统部署

```bash
# 安装生产依赖
uv pip install -r requirements/production.txt

# 收集静态文件
python manage.py collectstatic --noinput

# 使用 Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

详细部署说明请查看 [部署文档](DEPLOYMENT.md)

## 🔧 项目管理

```bash
# 查看帮助
python manage_project.py help

# 清理缓存
python manage_project.py clean

# 代码检查
python manage_project.py lint

# 格式化代码
python manage_project.py format
```

## 📄 配置说明

### 环境变量

复制 `.env.example` 为 `.env` 并修改：

```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379/0
```

详细配置请查看 [配置文档](docs/CONFIGURATION.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

请查看 [贡献指南](CONTRIBUTING.md)

## 📜 更新日志

查看 [更新日志](CHANGELOG.md)

## 📜 许可证

[MIT License](LICENSE)

## 👨‍💻 作者

- GitHub: [@zhang123999-qq](https://github.com/zhang123999-qq)

---

⭐ 如果这个项目对你有帮助，欢迎 Star！
