# scripts 目录代码作用总览

> 文档目的：说明 `scripts/` 目录下每个脚本“是干什么的、什么时候用、主要做了什么、注意事项”。

---

## 目录清单

当前主要脚本：

1. `run.py` —— 自动化安装/初始化脚本（功能最全）
2. `start.py` —— 本地开发服务器快速启动脚本
3. `manage_project.py` —— 项目日常管理命令集（测试、清理、迁移等）
4. `init_default_data.py` —— 初始化默认论坛板块/博客分类/标签
5. `migrate_to_mysql.py` —— SQLite 到 MySQL 的数据迁移脚本

---

## 1) run.py（自动化安装脚本）

### 作用
用于一键执行项目安装流程，适合新机器初始化：
- 环境检测
- 创建虚拟环境
- 安装依赖
- 生成 `.env`
- 数据库迁移
- 收集静态文件
- 创建管理员（交互）
- 生产模式下安装 Gunicorn 并生成启动脚本

### 入口参数
- `python run.py`：默认开发模式安装
- `python run.py --prod`：生产模式安装
- `python run.py --dev`：开发模式安装
- `python run.py --check`：仅做环境检查
- `python run.py --no-input`：非交互模式

### 核心模块
- `TerminalEncoder`：终端编码兼容（尤其 Windows）
- `Logger`：安装日志写入 `logs/install_*.log`
- `SystemDetector`：收集系统信息
- `DjangoBlogSetup`：主安装流程控制类

### 关键方法说明
- `step_check_environment()`：检查 Python / pip / uv / manage.py
- `step_create_venv()`：创建或复用 `.venv`
- `step_install_dependencies()`：安装 development/production 依赖
- `step_setup_env()`：生成基础 `.env`
- `step_migrate()`：执行 `makemigrations` + `migrate`
- `step_collectstatic()`：执行 `collectstatic`
- `step_create_superuser()`：交互创建管理员
- `step_install_gunicorn()`：生产模式安装 gunicorn 相关依赖并生成脚本

### 使用建议
- 新部署机器优先使用它做“基础打底”
- 生产部署建议带 `--prod`
- 首次安装失败时先看 `logs/install_*.log`

### 注意事项
- 会修改本地 `.env`（若不存在）
- 可能触发数据库迁移，请在生产环境谨慎执行

---

## 2) start.py（开发快速启动）

### 作用
快速启动 Django 开发服务器，常用于本地开发联调。

### 入口参数
- `python start.py`：127.0.0.1:8000
- `python start.py --lan`：0.0.0.0，对局域网开放
- `python start.py --port 8080`：自定义端口

### 核心逻辑
- 自动定位虚拟环境 Python（找不到则回退系统 Python）
- 检查端口是否占用
- 输出访问地址和管理后台地址
- 执行 `manage.py runserver`

### 使用建议
- 本地开发优先用 `start.py`
- 演示给同网段设备看页面时用 `--lan`

### 注意事项
- 这是开发服务器，不是生产服务（生产请用 Gunicorn + Nginx）

---

## 3) manage_project.py（项目管理脚本）

### 作用
将常用维护命令集中为一个入口，减少手敲命令成本。

### 入口用法
`python scripts/manage_project.py [命令]`

### 支持命令
- `install-dev`：安装开发依赖
- `install-prod`：安装生产依赖
- `clean`：清理缓存（`__pycache__`、`.pyc`、`.pytest_cache`、`tmp`）
- `test`：执行 `manage.py test`
- `test-security`：执行 `manage.py check --deploy`
- `lint`：运行 flake8
- `format`：运行 black + isort
- `migrate`：执行迁移
- `run`：本地启动
- `run-lan`：局域网启动
- `collectstatic`：收集静态文件

### 关键函数
- `run_command()`：统一执行 shell 命令
- `clean()`：统一清理临时产物
- `test()/lint()/format_code()`：测试与格式化工具封装

### 使用建议
- 日常开发把它当“项目命令总开关”

### 注意事项
- `clean` 会删除缓存与临时目录，执行前确认无临时文件依赖

---

## 4) init_default_data.py（默认数据初始化）

### 作用
初始化站点基础数据，避免后台空白：
- 论坛板块（8个）
- 博客分类（6个）
- 博客标签（6个）

### 执行方式
```bash
python scripts/init_default_data.py
```

### 主要函数
- `init_boards()`：创建默认论坛板块
- `init_categories()`：创建默认博客分类
- `init_tags()`：创建默认博客标签
- `main()`：汇总执行并输出统计

### 实现特点
- 使用 `get_or_create`，可重复执行（幂等）
- 标签创建时对异常做了兜底（按 slug/name 双路径尝试）

### 注意事项
- 默认 settings 是 `config.settings.production`，确保 `.env` 已配置好数据库

---

## 5) migrate_to_mysql.py（SQLite -> MySQL 迁移）

### 作用
将旧 SQLite 数据迁移到 MySQL，包括用户、文章、评论、论坛数据等。

### 迁移对象（按脚本顺序）
1. 用户（`accounts_user`）
2. 用户资料（`accounts_profile`）
3. 博客分类（`blog_category`）
4. 博客标签（`blog_tag`）
5. 文章（`blog_post`）
6. 文章标签关系（`blog_post_tags`）
7. 评论（`blog_comment`）
8. 论坛板块（`forum_board`）
9. 论坛主题（`forum_topic`）
10. 论坛回复（`forum_reply`）

### 执行方式
```bash
python scripts/migrate_to_mysql.py
```

### 关键实现
- 直接读取 `db.sqlite3`
- 使用 Django ORM 的 `update_or_create` 写入目标库
- 保留原记录 ID（便于关系还原）

### 注意事项（重要）
- 执行前务必备份源库和目标库
- 脚本默认 `DJANGO_SETTINGS_MODULE=config.settings.development`，请确认 development 指向的数据库是目标 MySQL
- 大数据量迁移建议先在测试环境演练

---

## 推荐使用顺序（新环境）

1. 运行安装：`python run.py --prod`
2. 执行迁移：`python manage.py migrate`
3. 初始化默认数据：`python scripts/init_default_data.py`
4. 启动验证：`python start.py`（开发）或 gunicorn（生产）

---

## 脚本维护建议

- 新增脚本时，统一放在 `scripts/` 并补充本文档
- 涉及 DB 写入的脚本，必须写明幂等性和回滚方式
- 生产脚本尽量支持 `--dry-run`（后续可增强）

---

## 变更记录

- 2026-03-27：首次整理 scripts 全量代码作用说明。
