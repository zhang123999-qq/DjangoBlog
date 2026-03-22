# DjangoBlog v2.4.0

🚀 一个基于 Django 4.2 LTS 的现代化博客论坛系统，集成 **72+ 在线工具**，支持智能内容审核、富文本编辑器、**性能优化**

[![Django](https://img.shields.io/badge/Django-4.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![Performance](https://img.shields.io/badge/Response-<1ms-brightgreen.svg)](docs/PERFORMANCE.md)

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

### ⚡ 性能优化（v2.4.0 新增）

#### 缓存优化
- **SiteConfig 缓存** - 减少 95% 数据库查询
- **分类标签缓存** - 每页减少 2 次查询
- **工具列表缓存** - 1 分钟页面缓存
- **缓存预热** - 定时预加载常用数据

#### 连接池
- **数据库连接池** - 10 分钟连接复用
- **Redis 连接池** - 50 连接并发支持
- **健康检查** - 自动回收无效连接

#### 性能监控
- **请求耗时追踪** - X-Request-Duration-Ms 响应头
- **查询计数** - X-DB-Queries 响应头
- **慢请求警告** - 自动检测 >500ms 请求
- **N+1 问题检测** - 自动警告 >20 查询的请求

#### 资源回收
- **Session 清理** - 每小时清理过期会话
- **日志清理** - 定期清理旧日志
- **数据库优化** - 每周 VACUUM/OPTIMIZE
- **Redis 监控** - 5 分钟健康检查

#### 性能数据

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 首页响应 | ~800ms | ~1ms | **99.9%** |
| API 响应 | ~10ms | ~1-5ms | 50-90% |
| 缓存命中 | 0% | 80%+ | - |
| 数据库连接 | 每次新建 | 复用 10min | 50% |

### 🔧 在线工具栏（72+ 工具）

#### 加密解密（8个）
AES、RSA、Base64、MD5、SHA、HMAC、DES、摩斯密码

#### 编码转换（14个）
URL编码、Unicode、HTML实体、进制转换、大小写、拼音等

#### 文本处理（9个）
字数统计、大小写转换、中文繁简转换、文本去重、清除格式

#### 生成工具（11个）
UUID、密码（增强版）、二维码、条形码、字符画、.gitignore

#### 数据格式（7个）
JSON格式化（Monaco编辑器）、CSV/JSON互转、HTML/Markdown

#### 时间日期（3个）
时间戳转换、时差计算、番茄钟

#### 图片工具（5个）
图片Base64、图片压缩、图片格式转换、EXIF信息

#### 网络工具（7个）
IP查询、端口扫描、NAT检测、HTTP请求

#### 安全工具（3个）
密码强度检测、身份证校验、邮箱验证

#### 其他工具（5个）
BMI计算器、正则测试、JSONPath、随机数

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
| **缓存** | Redis (django-redis) |
| **API** | Django REST Framework |
| **前端** | Bootstrap 5.3 |
| **图标** | Bootstrap Icons / Font Awesome |
| **富文本** | TinyMCE 7 |
| **代码编辑器** | Monaco Editor |
| **AI 审核** | 百度内容审核 API |
| **性能监控** | 自研中间件 |

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
- Redis（可选，用于缓存和 Celery）

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
│   │   ├── performance.py       # 性能工具
│   │   ├── performance_middleware.py  # 性能监控
│   │   ├── connection_monitor.py  # 连接池监控
│   │   ├── cache_optimizer.py    # 缓存优化
│   │   └── maintenance_tasks.py  # 维护任务
│   ├── forum/             # 论坛功能
│   ├── install/           # 安装向导
│   └── tools/             # 工具栏
│       └── tool_modules/  # 72+ 工具模块
├── config/                # 配置文件
├── static/                # 静态文件
├── templates/             # 模板文件
├── media/                 # 用户上传文件
├── docs/                  # 文档
│   ├── PERFORMANCE.md          # 性能优化指南
│   ├── PERFORMANCE_DEEP.md     # 深度优化报告
│   └── TEST_REPORT.md          # 测试报告
├── tests/                 # 测试文件
└── requirements/          # 依赖管理
```

## 🧪 测试

```bash
# 运行所有测试
python manage.py test

# 运行完整测试套件
python tests/test_complete.py

# 运行工具测试
python tests/test_tools.py

# 运行负载测试
python tests/test_load.py
```

### 测试结果

| 测试类型 | 测试数 | 通过 | 通过率 |
|----------|--------|------|--------|
| 系统基础 | 10 | 10 | 100% |
| 功能测试 | 11 | 11 | 100% |
| 深度测试 | 7 | 7 | 100% |
| 完整套件 | 52 | 51 | 98.1% |
| 工具测试 | 21 | 21 | 100% |
| 单元测试 | 18 | 18 | 100% |
| **总计** | **119** | **118** | **99.2%** |

## 🚀 部署

### Docker 部署

```bash
docker-compose up -d
```

### 传统部署

```bash
# 安装生产依赖
pip install -r requirements/production.txt

# 收集静态文件
python manage.py collectstatic --noinput

# 使用 Gunicorn
gunicorn config.wsgi:application -c gunicorn.conf.py
```

详细部署说明请查看 [部署文档](DEPLOYMENT.md)

## 📄 配置说明

### 环境变量

复制 `.env.example` 为 `.env` 并修改：

```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379/0

# 性能配置
SLOW_REQUEST_THRESHOLD_MS=500
HIGH_QUERY_THRESHOLD=20
```

详细配置请查看 [配置文档](docs/CONFIGURATION.md)

## 🆕 v2.4.0 更新内容

### 🚀 性能优化
- ⚡ **缓存优化** - SiteConfig、分类标签、工具列表缓存
- ⚡ **连接池** - 数据库和 Redis 连接池
- ⚡ **性能监控** - 请求耗时、查询计数、慢请求警告
- ⚡ **资源回收** - Session 清理、日志清理、数据库优化
- ⚡ **批量处理** - Celery 任务批量优化

### 📊 性能提升
- 首页响应从 ~800ms 降至 ~1ms（**99.9%**）
- API 响应提升 50-90%
- 缓存命中率 80%+

### 📚 文档更新
- [性能优化指南](docs/PERFORMANCE.md)
- [深度优化报告](docs/PERFORMANCE_DEEP.md)
- [测试报告](docs/TEST_REPORT.md)

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
