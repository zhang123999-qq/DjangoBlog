# DjangoBlog 项目结构说明

## 目录结构

```
DjangoBlog/
├── apps/                      # Django 应用模块
│   ├── accounts/             # 用户账户管理
│   ├── api/                  # REST API 接口
│   ├── blog/                 # 博客功能
│   ├── core/                 # 核心功能（首页、搜索等）
│   ├── forum/                # 论坛功能
│   ├── install/              # 安装向导
│   └── tools/                # 工具栏（60+ 在线工具）
│       └── tool_modules/     # 工具模块实现
│
├── config/                    # 项目配置
│   ├── settings/             # 配置文件
│   │   ├── base.py          # 基础配置
│   │   ├── development.py   # 开发环境配置
│   │   └── production.py    # 生产环境配置
│   ├── urls.py              # URL 路由
│   ├── wsgi.py              # WSGI 入口
│   └── asgi.py              # ASGI 入口
│
├── deploy/                    # 部署配置
│   ├── nginx.conf.example    # Nginx 配置示例
│   ├── gunicorn.service.example
│   └── supervisor.conf.example
│
├── docs/                      # 文档
│   └── CONFIGURATION.md
│
├── logs/                      # 日志文件
│   └── django.log
│
├── moderation/                # 内容审核系统
│   ├── management/commands/  # 管理命令
│   ├── migrations/           # 数据库迁移
│   └── templates/moderation/
│
├── requirements/              # 依赖管理
│   ├── base.txt              # 基础依赖
│   ├── development.txt       # 开发依赖
│   └── production.txt        # 生产依赖
│
├── static/                    # 静态文件
│   ├── css/                  # 样式文件
│   ├── img/                  # 图片资源
│   │   └── avatars/         # 头像图片
│   ├── js/                   # JavaScript 文件
│   └── vendor/               # 第三方库本地备份
│       ├── bootstrap/
│       └── bootstrap-icons/
│
├── templates/                 # HTML 模板
│   ├── accounts/             # 账户相关模板
│   ├── admin/                # 管理后台模板
│   ├── blog/                 # 博客模板
│   ├── core/                 # 核心功能模板
│   ├── forum/                # 论坛模板
│   ├── includes/             # 公共组件
│   ├── install/              # 安装向导模板
│   ├── search/               # 搜索模板
│   ├── tools/                # 工具栏模板
│   ├── base.html             # 基础模板
│   ├── base_tech.html        # 科技主题基础模板
│   └── home.html             # 首页模板
│
├── tests/                     # 测试文件
│   ├── logs/                 # 测试日志（已忽略）
│   ├── screenshots/          # 测试截图（已忽略）
│   ├── utils/                # 测试工具
│   ├── conftest.py           # Pytest 配置
│   ├── test_article.py
│   ├── test_like.py
│   ├── test_post.py
│   ├── test_register.py
│   └── test_security.py
│
├── .env                       # 环境变量
├── .env.example              # 环境变量示例
├── .gitignore                # Git 忽略规则
├── .python-version           # Python 版本
├── CHANGELOG.md              # 更新日志
├── CONTRIBUTING.md           # 贡献指南
├── DEPLOYMENT.md             # 部署文档
├── docker-compose.yml        # Docker Compose 配置
├── Dockerfile                # Docker 构建文件
├── LICENSE                   # 许可证
├── manage.py                 # Django 管理脚本
├── manage_project.py         # 项目管理脚本
├── migrate_to_mysql.py       # MySQL 迁移脚本
├── nginx.conf                # Nginx 配置
├── pyproject.toml            # 项目配置
├── run_lan.bat               # 局域网运行脚本
├── setup.cfg                 # Setup 配置
└── test_settings.py          # 测试配置
```

## 依赖管理

### 安装依赖

```bash
# 开发环境
uv pip install -r requirements/development.txt

# 生产环境
uv pip install -r requirements/production.txt
```

### 主要依赖分类

| 类别 | 依赖 |
|------|------|
| **Django 核心** | Django 4.2 LTS, django-environ, django-axes |
| **数据库** | mysqlclient, redis, django-redis |
| **API** | djangorestframework, django-filter, drf-spectacular |
| **认证** | django-allauth |
| **富文本** | django-ckeditor |
| **图片处理** | Pillow |
| **Markdown** | markdown, bleach |
| **工具依赖** | qrcode, pycryptodome, cryptography, pyzbar, jsonpath-ng |
| **其他** | django-taggit, django-meta, python-json-logger |

## 项目管理脚本

```bash
# 查看帮助
python manage_project.py help

# 清理缓存
python manage_project.py clean

# 运行测试
python manage_project.py test

# 运行安全测试
python manage_project.py test-security

# 代码检查
python manage_project.py lint

# 格式化代码
python manage_project.py format

# 启动开发服务器
python manage_project.py run

# 数据库迁移
python manage_project.py migrate

# 收集静态文件
python manage_project.py collectstatic
```

## 前端依赖

项目使用 CDN 引用前端库：

- Bootstrap 5.3.3
- Bootstrap Icons 1.11.3
- Google Fonts (Inter)

本地备份存放在 `static/vendor/` 目录。

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行安全测试
pytest tests/test_security.py -v

# 生成 HTML 报告
pytest tests/ -v --html=tests/report.html --self-contained-html
```

## 部署

```bash
# 收集静态文件
python manage.py collectstatic --noinput

# 使用 Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# 使用 Docker
docker-compose up -d
```

## 最近优化（2026-03-21）

1. ✅ 清理了 `__pycache__` 和 `.pyc` 缓存文件
2. ✅ 清理了 `.pytest_cache` 目录
3. ✅ 清理了 `tmp/` 临时文件
4. ✅ 合并了重复的测试依赖（删除 `tests/requirements.txt`）
5. ✅ 更新了 `.gitignore`，排除测试输出和临时文件
6. ✅ 创建了 `.gitkeep` 文件保留测试目录
7. ✅ 创建了 `static/vendor/` 目录用于第三方库本地备份
8. ✅ 创建了 `manage_project.py` 项目管理脚本
9. ✅ 更新了 `requirements/development.txt`，补充缺失的测试依赖
