# DjangoBlog 更新日志

所有重要的更改都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 新增
- **公安联网备案号功能**：
  - `SiteConfig` 新增 `site_gongan_beian` 字段 + 自动补全格式
  - Admin 添加"一键生成"按钮 + 公安备案链接自动生成
  - 页脚（footer.html）同步展示公安联网备案信息
- **模板 URL 规范化**：所有硬编码链接改为 `{% url %}` 模板标签
  - navbar.html、home.html、footer.html、admin/index.html
- **HTTP 请求工具 SSRF 防护**：新增内网 IP 检测，覆盖全部私有地址段
- **端口扫描工具安全加固**：限制扫描范围，防止滥用

### 修复
- **moderation 数据库迁移缺失**：`is_primary` 字段未生成迁移文件，已修复
- **navbar.html 语法错误**：`</a>` 标签未正确闭合，导致 HTML 渲染异常
- **论坛浏览量递增方式优化**：从 `F()` 表达式 + `refresh_from_db` 改为纯整数递增

### 安全改进
- **生产环境 Cookie 安全**：`SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` 默认改为 True
- **ALLOWED_HOSTS 不再自动添加通配符**：即使 DEBUG=True 也不再允许 `*`
- **CDN 脚本跨域防护**：Monaco Editor 和 TinyMCE 添加 `crossOrigin="anonymous"`
- **Clipboard API 升级**：优先使用 `navigator.clipboard.writeText`，回退方案完善
- **Robots.txt 优化**：sitemap 从绝对 URL 改为相对路径

### 优化
- **脚本清理工具增强**：排除 `.venv`、`.git` 等目录，支持 allure/htmlcov 报告清理
- **migrate_to_mysql.py 适配**：使用 ORM 动态获取真实表名，适配自定义 User 模型
- **start.py 增强**：支持 uv 管理的 Python 环境检测

---

## [2.3.3] - 2026-04-02

### 新增
- **API 文档**：新增 `docs/API.md`，涵盖 21 个接口完整文档
  - 博客 API：分类、标签、文章、评论
  - 论坛 API：版块、主题、回复
  - 上传 API：图片、文件、异步状态
  - 审核 API：指标、通过、拒绝
  - 包含 curl 示例、字段说明、错误码参考、FAQ

### 优化
- **Admin 查询优化**：
  - 添加 `list_select_related` 减少数据库查询
  - 添加 `raw_id_fields` 优化大数据量选择

---

## [2.3.1] - 2026-04-01

### 新增
- **一键自动部署**：新增 `deploy/auto-deploy.sh` 脚本
  - 自动生成 `.env` 配置文件（含随机 SECRET_KEY）
  - 配置 Docker 镜像加速（国内环境自动启用）
  - 预拉取基础镜像、构建应用镜像
  - 启动所有服务、自动执行数据库迁移
  - 交互式创建管理员账户

### 修复
- **Docker 部署高危问题修复**：
  - `SECURE_SSL_REDIRECT` / `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` 默认改为 False
  - 重命名 `SecurityMiddleware` → `SecurityMonitorMiddleware` 解决中间件重名
  - 修复 Dockerfile 中 collectstatic 目录权限问题

### 变更
- **部署目录清理**：移除 19 个与 Docker 无关的测试/性能/本地工具脚本
- **依赖优化**：添加阿里云 pip 镜像加速

### 测试
- 测试基线：`uv run pytest -q`（79 passed / 80 skipped）

---

## [2.3.0] - 2026-03-31

### 新增
- **审核系统**：独立 `moderation` 应用
  - 支持评论、主题、回复的审核流程
  - 百度内容审核 API 集成（可选）
  - 审核 API 带限流和并发保护

- **安全增强**：
  - 安全响应头中间件（CSP、X-Frame-Options 等）
  - 登录防护（django-axes 集成）
  - 上传文件安全扫描（ClamAV 可选）

- **Admin 模块化重构**：
  - 原 `apps/core/admin.py`（550+ 行）拆分为 10 个独立文件
  - 自定义仪表盘首页（统计数据 + 图表）

### 优化
- **查询性能优化**：
  - 博客列表页：添加 `select_related` 和 `prefetch_related`
  - 论坛列表页：优化 N+1 查询问题
  - 缓存策略：Redis 缓存热点数据

### 测试
- 新增回归测试基线

---

## [2.2.0] - 2026-03-15

### 新增
- **工具箱模块**：72+ 实用工具
  - 编码转换：Base64、URL编码、Unicode 等
  - 文本处理：格式化、统计、转换
  - 加解密：MD5、SHA、AES 等
  - 图像工具：图片压缩、格式转换

- **API 层**：Django REST Framework 集成
  - 博客 API：文章、分类、标签、评论
  - 论坛 API：版块、主题、回复
  - OpenAPI 文档支持（drf-spectacular）

---

## [2.1.0] - 2026-02-01

### 新增
- **论坛系统**：
  - 版块管理
  - 主题发布、回复
  - 置顶、锁定功能

- **用户系统增强**：
  - 用户资料页
  - 头像上传
  - 个人文章/主题列表

### 修复
- 修复评论嵌套显示问题
- 修复 Slug 重复导致的 404

---

## [2.0.0] - 2026-01-01

### 重大变更
- **项目重构**：从单体应用重构为模块化架构
  - `apps/accounts/` - 用户认证
  - `apps/blog/` - 博客系统
  - `apps/forum/` - 论坛系统
  - `apps/tools/` - 工具箱
  - `apps/api/` - API 层
  - `apps/core/` - 公共能力

### 新增
- Docker Compose 生产部署方案
- 分层配置（base/development/production/test）
- 分层依赖管理（requirements/base.txt 等）

### 移除
- 旧的配置方式
- 不再使用的依赖

---

## [1.0.0] - 2025-06-01

### 新增
- 基础博客功能
  - 文章发布、编辑、删除
  - 分类、标签管理
  - 评论系统
- 用户认证系统
- Django Admin 后台管理
- 基础模板和样式

---

## 版本说明

- **主版本号（Major）**：不兼容的 API 更改
- **次版本号（Minor）**：向后兼容的功能新增
- **修订号（Patch）**：向后兼容的问题修复

---

*更新时间: 2026-04-02*
