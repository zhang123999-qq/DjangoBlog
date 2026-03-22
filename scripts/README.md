# Scripts 脚本目录

本目录包含 DjangoBlog 项目的启动、管理和维护脚本。

---

## 📁 文件列表

| 文件 | 类型 | 用途 |
|------|------|------|
| `run.py` | Python | 完整部署脚本（推荐） |
| `start.py` | Python | 简单启动脚本 |
| `manage_project.py` | Python | 项目管理工具 |
| `migrate_to_mysql.py` | Python | 数据库迁移脚本 |
| `init_default_data.py` | Python | 初始化默认数据 ⭐新增 |
| `start_celery.bat` | Batch | Windows Celery 启动 |
| `start_celery.sh` | Shell | Linux/Mac Celery 启动 |
| `start_server.sh` | Shell | 服务器启动 |
| `stop_server.sh` | Shell | 服务器停止 |

---

## 🚀 快速使用

```bash
# 进入项目根目录
cd /path/to/DjangoBlog

# 推荐方式：使用 run.py
python scripts/run.py

# 简单启动
python scripts/start.py

# 项目管理
python scripts/manage_project.py [命令]
```

---

## 📖 详细说明

### 1. run.py - 完整部署脚本 ⭐推荐

**功能最全的启动脚本**，支持交互式安装、环境检查、依赖安装、数据库迁移等。

```bash
# 交互式安装（推荐新手）
python scripts/run.py

# 开发环境快速安装
python scripts/run.py --dev

# 生产环境安装
python scripts/run.py --prod

# 仅检查环境
python scripts/run.py --check

# 显示帮助
python scripts/run.py --help
```

**主要功能：**
- ✅ 自动检测 Python 版本
- ✅ 创建虚拟环境
- ✅ 安装依赖（支持 uv 加速）
- ✅ 生成 .env 配置文件
- ✅ 执行数据库迁移
- ✅ 收集静态文件
- ✅ 创建管理员账户
- ✅ 启动开发服务器
- ✅ 支持局域网访问

**适用场景：**
- 首次部署项目
- 需要完整环境配置
- 不熟悉 Django 命令的用户

---

### 2. start.py - 简单启动脚本

**轻量级启动脚本**，快速启动开发服务器。

```bash
# 基本启动（localhost:8000）
python scripts/start.py

# 指定端口
python scripts/start.py --port 3000

# 局域网访问
python scripts/start.py --lan

# 后台运行
python scripts/start.py --daemon
```

**主要功能：**
- ✅ 自动检测虚拟环境
- ✅ 快速启动服务器
- ✅ 支持局域网访问
- ✅ 支持后台运行

**适用场景：**
- 环境已配置完成
- 只需要启动服务器
- 快速开发调试

---

### 3. manage_project.py - 项目管理工具

**多功能项目管理脚本**，提供清理、测试、格式化等常用操作。

```bash
# 显示帮助
python scripts/manage_project.py help

# 清理缓存和临时文件
python scripts/manage_project.py clean

# 运行测试
python scripts/manage_project.py test

# 运行安全测试
python scripts/manage_project.py test-security

# 代码检查
python scripts/manage_project.py lint

# 格式化代码
python scripts/manage_project.py format

# 数据库迁移
python scripts/manage_project.py migrate

# 启动开发服务器
python scripts/manage_project.py run

# 收集静态文件
python scripts/manage_project.py collectstatic
```

**可用命令：**

| 命令 | 功能 |
|------|------|
| `clean` | 清理 `__pycache__`、`.pyc`、`.pytest_cache`、`tmp/` |
| `test` | 运行测试套件，生成 HTML 报告 |
| `test-security` | 运行安全测试 |
| `lint` | Flake8 代码检查 + Black 格式检查 |
| `format` | Black + isort 格式化代码 |
| `migrate` | 执行 `makemigrations` + `migrate` |
| `run` | 启动开发服务器 (0.0.0.0:8000) |
| `collectstatic` | 收集静态文件 |

**适用场景：**
- 日常开发和维护
- 代码质量检查
- 清理临时文件

---

### 4. migrate_to_mysql.py - 数据库迁移脚本

**SQLite → MySQL 数据迁移工具**，将现有数据迁移到 MySQL。

```bash
# 执行迁移（需要先配置 MySQL）
python scripts/migrate_to_mysql.py
```

**迁移内容：**
- 用户和用户资料
- 博客分类、标签、文章、评论
- 论坛版块、主题、回复
- 其他所有数据表

**前置条件：**
1. 安装并启动 MySQL
2. 创建目标数据库
3. 配置 `.env` 中的 MySQL 连接信息

**适用场景：**
- 从 SQLite 升级到 MySQL
- 生产环境部署
- 数据库迁移

---

### 5. init_default_data.py - 初始化默认数据 ⭐新增

**初始化论坛板块、博客分类和标签**，快速填充默认数据。

```bash
# 执行初始化
python scripts/init_default_data.py
```

**创建内容：**

| 类型 | 数量 | 内容 |
|------|------|------|
| 论坛板块 | 8个 | 技术交流、问题求助、资源分享、灌水闲聊、Python编程、Web开发、人工智能、数据库 |
| 博客分类 | 6个 | 技术笔记、项目实战、工具推荐、生活随笔、编程学习、源码解析 |
| 博客标签 | 6个 | Python、Django、JavaScript、前端开发、后端开发、网络安全 |

**特点：**
- 自动检测已存在数据，不会重复创建
- 显示新建数量和总计数量
- 支持多次运行

**适用场景：**
- 新项目初始化
- 重置默认数据
- 演示环境搭建

---

### 5. start_celery.bat - Windows Celery 启动

**Windows 系统 Celery 启动脚本**，启动异步任务队列。

```batch
# 双击运行或在命令行执行
scripts\start_celery.bat
```

**启动内容：**
- Celery Worker（任务执行器）
- Celery Beat（定时任务调度器）
- Flower（任务监控界面，可选）

**适用场景：**
- 需要异步任务处理
- 定时任务调度
- Windows 开发环境

---

### 6. start_celery.sh - Linux/Mac Celery 启动

**Linux/Mac 系统 Celery 启动脚本**。

```bash
# 添加执行权限
chmod +x scripts/start_celery.sh

# 执行
./scripts/start_celery.sh
```

**功能与 Windows 版本相同。**

---

### 7. start_server.sh - 服务器启动脚本

**生产服务器启动脚本**，使用 Gunicorn 启动。

```bash
# 添加执行权限
chmod +x scripts/start_server.sh

# 启动服务器
./scripts/start_server.sh
```

**启动内容：**
- Gunicorn WSGI 服务器
- 自动检测可用端口
- 后台运行

**适用场景：**
- 生产环境部署
- Linux 服务器

---

### 8. stop_server.sh - 服务器停止脚本

**停止 Gunicorn 服务器**。

```bash
# 停止服务器
./scripts/stop_server.sh
```

**功能：**
- 查找并停止 Gunicorn 进程
- 清理 PID 文件

---

## 🔧 使用建议

### 首次部署
```bash
# 推荐使用 run.py
python scripts/run.py
```

### 日常开发
```bash
# 快速启动
python scripts/start.py

# 或使用 manage.py
python manage.py runserver
```

### 代码维护
```bash
# 清理缓存
python scripts/manage_project.py clean

# 格式化代码
python scripts/manage_project.py format

# 运行测试
python scripts/manage_project.py test
```

### 生产部署
```bash
# 数据库迁移到 MySQL
python scripts/migrate_to_mysql.py

# 启动 Celery
./scripts/start_celery.sh

# 启动服务器
./scripts/start_server.sh
```

---

## 📌 注意事项

1. **运行位置**：所有脚本都应在项目根目录下运行
2. **虚拟环境**：建议在虚拟环境中执行
3. **权限问题**：Linux/Mac 下的 `.sh` 文件需要执行权限 (`chmod +x`)
4. **Windows 编码**：脚本已处理 Windows 终端编码问题

---

## 🆘 故障排除

### 问题：`python: can't open file 'scripts/run.py'`
**解决**：确保在项目根目录下执行命令。

### 问题：`Permission denied`
**解决**：Linux/Mac 下添加执行权限：
```bash
chmod +x scripts/*.sh
```

### 问题：Windows 终端乱码
**解决**：脚本已自动处理，如仍有问题，手动执行：
```batch
chcp 65001
```

---

*最后更新: 2026-03-22*
