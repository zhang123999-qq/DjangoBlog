<div align="center">

# 🌐 DjangoBlog

**基于 Django 4.2 的全功能博客与论坛系统**

[![Django](https://img.shields.io/badge/Django-4.2%20LTS-green?logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/zhang123999-qq/DjangoBlog?style=social)](https://github.com/zhang123999-qq/DjangoBlog/stargazers)

[在线演示](#) | [快速开始](#快速开始) | [功能特性](#功能特性) | [部署指南](#部署指南)

</div>

---

## 📸 项目截图

<!-- 添加截图后取消注释
![Homepage](screenshots/homepage.png)
![Blog](screenshots/blog.png)
![Forum](screenshots/forum.png)
-->

---

## 🎯 项目简介

DjangoBlog 是一个基于 Django 4.2 LTS 的综合性网站项目，集成博客、论坛、工具栏、用户系统于一体。采用模块化设计，代码结构清晰，易于扩展和二次开发。

### ✨ 主要特点

- 🔐 **完整的用户系统** - 注册、登录、个人资料、权限管理
- 📝 **功能丰富的博客** - 文章、分类、标签、评论、浏览统计
- 💬 **互动论坛系统** - 版块、主题、回复、点赞
- 🛠️ **59个实用工具** - 加密解密、编码转换、二维码生成、网络工具、数据处理等
- 🔧 **安装向导** - 可视化安装配置（快速安装/向导安装）
- 📱 **响应式设计** - 完美支持移动端
- 🔒 **安全防护** - Django Axes 防暴力破解
- 🐳 **Docker支持** - 一键部署

---

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Django 4.2 LTS
- MySQL 8.0 (推荐) 或 SQLite

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. 安装依赖
# 方式一：使用 pip（推荐）
pip install -r requirements/production.txt

# 方式二：使用 pyproject.toml
pip install -e .

# 开发模式（包含测试工具）
pip install -e ".[dev]"

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库等信息

# 5. 运行迁移
python manage.py migrate

# 6. 收集静态文件
mkdir staticfiles  # 创建静态文件目录
python manage.py collectstatic --noinput

# 7. 初始化默认数据（可选）
python manage.py init_default_data

# 8. 创建管理员
python manage.py createsuperuser

# 9. 启动服务器
python manage.py runserver
```

访问 http://localhost:8000 查看网站。

---

## 📦 功能模块

### 博客系统

| 功能 | 说明 |
|------|------|
| 文章管理 | 发布、编辑、删除文章 |
| 分类标签 | 文章分类和标签管理 |
| 评论系统 | 用户评论、审核机制 |
| 浏览统计 | 自动统计文章浏览量 |
| SEO优化 | URL Slug、Meta标签 |

### 论坛系统

| 功能 | 说明 |
|------|------|
| 版块管理 | 多版块支持 |
| 主题发布 | 发布、置顶、锁定 |
| 回复系统 | 回复、点赞 |
| 统计功能 | 主题数、回复数统计 |

### 工具栏（59个工具）

| 类别 | 工具 |
|------|------|
| 🔐 加密 | AES、RSA、HMAC、凯撒密码、文本加密 |
| 🔢 编码 | Base64、Unicode、URL编码、HTML实体 |
| 🔢 转换 | 进制转换、颜色转换、数字转换、驼峰命名 |
| 📊 数据 | JSON格式化、JSONPath、CSV转JSON、EXIF读取 |
| 🔒 安全 | 哈希计算、MD5、SHA系列 |
| 🌐 网络 | HTTP请求、端口扫描、IP查询、URL缩短 |
| 📝 文本 | 正则测试、文本统计、文本生成、文本对比、字符串转义 |
| 🎲 生成 | 密码生成、UUID生成、假数据生成、随机数 |
| 📅 时间 | 时间戳转换、Cron解析 |
| 🖼️ 图片 | 二维码生成、二维码解码、图片Base64 |
| 🧩 其他 | 词云生成 |
| URL编码 | URL编码解码 |
| UUID生成器 | 生成UUID v1/v3/v4/v5 |
| 文本生成器 | Lorem Ipsum占位文本生成 |
| 文本对比 | 文本Diff差异对比 |
| 图片Base64 | 图片与Base64互转 |
| 代码格式化 | JSON/CSS/HTML/SQL美化压缩 |
| 进制转换器 | 多进制数字转换 |

---

## 🔌 REST API

项目提供完整的 REST API 接口：

### API 端点

| 端点 | 说明 |
|------|------|
| `GET /api/posts/` | 文章列表 |
| `GET /api/posts/{id}/` | 文章详情 |
| `GET /api/categories/` | 分类列表 |
| `GET /api/tags/` | 标签列表 |
| `GET /api/topics/` | 论坛主题列表 |
| `GET /api/boards/` | 版块列表 |

### API 文档

- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- Schema: `http://localhost:8000/api/schema/`

### 示例请求

```bash
# 获取文章列表
curl http://localhost:8000/api/posts/

# 搜索文章
curl "http://localhost:8000/api/posts/?search=django"

# 按分类筛选
curl http://localhost:8000/api/posts/?category=1
```

---

## 🔍 搜索功能

支持全局搜索博客文章和论坛主题：

```
http://localhost:8000/search/?q=关键词
```

---

## 🐳 Docker 部署

```bash
# 使用 Docker Compose 一键部署
docker-compose up -d
```

服务启动后访问 http://localhost

---

## 📁 项目结构

```
DjangoBlog/
├── apps/                 # 应用模块
│   ├── accounts/         # 用户账户
│   ├── blog/             # 博客功能
│   ├── forum/            # 论坛功能
│   ├── tools/            # 工具栏
│   │   └── tool_modules/ # 工具模块（21个工具）
│   ├── core/             # 核心功能
│   └── install/          # 安装向导
├── config/               # 项目配置
├── templates/            # 模板文件
├── static/               # 静态文件
├── media/                # 媒体文件
├── requirements/         # 依赖文件
│   ├── base.txt          # 基础依赖
│   ├── development.txt   # 开发依赖
│   └── production.txt    # 生产依赖
├── tests/                # 自动化测试
├── Dockerfile            # Docker 配置
└── docker-compose.yml    # Docker Compose 配置
```

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | Django密钥 | - |
| `DEBUG` | 调试模式 | False |
| `ALLOWED_HOSTS` | 允许的主机 | localhost |
| `DB_ENGINE` | 数据库引擎 | sqlite |
| `DB_NAME` | 数据库名 | db.sqlite3 |
| `USE_REDIS` | 使用Redis | False |

详细配置请参考 [.env.example](.env.example)

---

## 🧪 自动化测试

项目包含完整的自动化测试套件：

```bash
# 安装测试依赖
pip install -r tests/requirements.txt

# 安装浏览器
playwright install chromium

# 运行测试
pytest tests/ -v --headless

# 生成HTML报告
pytest tests/ --html=report.html
```

测试覆盖：
- 用户注册测试
- 论坛发帖测试
- 文章发布测试
- 点赞功能测试

---

## 🤝 参与贡献

欢迎参与项目贡献！请查看 [贡献指南](CONTRIBUTING.md)。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [Django](https://www.djangoproject.com/) - Web框架
- [Bootstrap](https://getbootstrap.com/) - 前端框架
- [django-environ](https://github.com/sobolevn/django-environ) - 环境变量管理

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！**

[⬆ 返回顶部](#-djangoblog)

Made with ❤️ by [zhang123999-qq](https://github.com/zhang123999-qq)

</div>
