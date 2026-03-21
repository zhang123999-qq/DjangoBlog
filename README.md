# DjangoBlog v2.3.0

🚀 一个基于 Django 4.2 LTS 的现代化博客论坛系统，集成 **70+ 在线工具**，支持智能内容审核、富文本编辑器

[![Django](https://img.shields.io/badge/Django-4.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)

## ✨ 功能特性

### 📝 博客系统
- 文章发布、编辑、删除
- **TinyMCE 富文本编辑器** - 所见即所得编辑
- Markdown 支持
- 分类和标签管理
- 文章搜索
- 点赞和评论
- 草稿箱管理

### 💬 论坛系统
- 多版块讨论区
- 话题创建和回复
- 用户互动
- 智能内容审核

### 🛡️ 智能审核系统
- **用户信誉系统** - 基于行为的智能分级
- **AI 内容审核** - 百度内容审核 API 集成
- **多级审核策略** - 高信誉自动发布，低信誉强制人工审核
- **敏感词检测** - 支持分类、缓存
- **图片审核** - AI 图片违规检测
- **异步处理** - Celery 异步队列，不阻塞请求

### 🔧 在线工具栏（70+ 工具）

#### 加密解密
AES、RSA、Base64、MD5、SHA、HMAC、DES、摩斯密码

#### 编码转换
URL编码、Unicode、HTML实体、HTML/Markdown互转

#### 文本处理
字数统计、大小写转换、中文繁简转换、文本去重、清除格式

#### 生成工具
UUID、密码（增强版）、二维码、条形码、字符画、.gitignore

#### 数据转换
JSON格式化（Monaco编辑器）、CSV/JSON互转

#### 时间工具
时间戳转换、时差计算

#### 图片工具
图片Base64、图片压缩、图片格式转换、EXIF信息

#### 网络工具
IP查询、端口扫描、HTTP请求

#### 安全工具
密码强度检测、凯撒密码

#### 其他工具
BMI计算器、正则测试、JSONPath、密码强度检测、Markdown编辑器

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
| **图标** | Bootstrap Icons / Font Awesome |
| **富文本** | TinyMCE 7 |
| **代码编辑器** | Monaco Editor |
| **AI 审核** | 百度内容审核 API |

## 📦 快速开始

### 一键安装（推荐）

```bash
# 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 一键安装
python run.py

# 启动服务器
python start.py
```

访问 http://127.0.0.1:8000 即可看到网站

### 环境要求

- Python 3.10+
- pip 或 uv（推荐）

### 手动安装

<details>
<summary>点击展开手动安装步骤</summary>

```bash
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements/development.txt

# 数据库迁移
python manage.py migrate

# 创建管理员
python manage.py createsuperuser

# 启动服务
python manage.py runserver
```

</details>

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
│       └── tool_modules/  # 70+ 工具模块
├── config/                # 配置文件
├── static/                # 静态文件
│   ├── css/              # 样式
│   ├── js/               # JavaScript（含编辑器初始化）
│   ├── img/              # 图片
│   └── vendor/           # 第三方库
├── templates/             # 模板文件
│   ├── admin/            # 管理后台（统一风格）
│   ├── blog/             # 博客模板
│   ├── forum/            # 论坛模板
│   ├── tools/            # 工具模板
│   └── install/          # 安装向导
├── media/                 # 用户上传文件
├── docs/                  # 文档
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

## 🆕 v2.3.0 更新内容

### 新增功能
- ✨ **TinyMCE 富文本编辑器** - 博客文章所见即所得编辑
- ✨ **Monaco Editor** - 代码编辑器，支持语法高亮
- ✨ **10个新工具** - 密码强度检测、Markdown编辑器、图片压缩等
- ✨ **文章管理** - 创建、编辑、删除、草稿箱
- ✨ **图片上传API** - 支持拖拽、粘贴上传

### 界面优化
- 🎨 管理后台风格统一 - 与前端保持一致
- 🎨 安装向导优化 - 更清晰的步骤引导
- 🎨 导航栏优化 - 新增"写文章"快捷入口

### 工具新增（10个）
1. 密码强度检测
2. Markdown编辑器
3. 图片压缩
4. HTML/Markdown互转
5. 文本去重
6. 清除文本格式
7. .gitignore生成器
8. 摩斯密码编解码
9. 字符画生成器
10. 图片格式转换

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

请查看 [贡献指南](CONTRIBUTING.md)

## 📜 更新日志

查看 [更新日志](CHANGELOG.md)

## 📜 许可证

[MIT License](LICENSE)

## 👨‍💻 作者

- GitHub: [@zhang123999-qq](https://github.com/zhang123999-qq)
- Email: 2973084264@qq.com

---

⭐ 如果这个项目对你有帮助，欢迎 Star！
