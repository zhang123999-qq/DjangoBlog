# DjangoBlog 更新日志

所有重要的更改记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 🔧 依赖与构建
- 新增 `requirements/development.lock`，CI 开发测试环境改为使用锁文件安装。
- 刷新 `base.lock` / `production.lock` / `uv.lock`，修正 `django-filter` 锁定版本与 Django 4.2 LTS 的兼容约束。
- Docker 构建改为安装 `requirements/production.lock`，提升生产镜像依赖可复现性。
- CI 依赖检查任务改为使用 `uv pip compile` 维护现有 `requirements/*.txt/*.lock` 结构。

### 📝 文档更新
- 更新 README 与部署文档，说明 `*.txt` 为依赖入口、`*.lock` 为 CI/Docker/生产部署锁文件。
- 更新 Dockerfile 文档，记录 Debian apt 源按基础镜像版本自动匹配。

### 🚀 新功能预览
- WebSocket 实时通知系统完善
- 全文搜索性能优化

---

## [2.4.1] - 2026-04-15

### 🔒 安全修复
- **文件上传安全加固**：为所有文件上传字段添加扩展名验证和大小限制
  - 创建统一验证器模块 `apps/core/validators.py`
  - 修复 `Profile.avatar` 和 `SiteConfig.logo` 模型字段
  - 修复 7 个工具模块的表单字段
- **安全验证**：通过深度安全审计，所有 P0 问题已修复

### 🔧 代码质量提升
- **静态分析工具**：安装 pylint、flake8、bandit、mypy、black、autopep8
- **代码格式化**：使用 black 统一代码格式，处理 189 个文件
- **代码风格修复**：修复 3907 个代码风格问题（100% 解决）
- **函数重构**：重构两个最长函数，提高可维护性
  - `http_request_tool.py`: 118 行 → 5 个函数
  - `image_format_convert_tool.py`: 115 行 → 5 个函数

### 📊 质量审计
- **综合审计评分**：8.7/10（生产就绪）
- **功能测试**：89.2% 页面正常（33/37）
- **API 测试**：核心 API 全部正常
- **代码统计**：265 个 Python 文件，32,781 行代码

### 📝 文档更新
- **合并审计报告**：创建统一的 `docs/PROJECT_AUDIT_2026.md`
- **删除冗余文档**：清理重复的审计报告文件
- **更新项目文档**：更新 README、CHANGELOG 等核心文档

---

## [2.4.0] - 2026-04-06

### 🎉 重大更新

#### P0 级改进：代码质量保障
- **pre-commit 钩子**：新增 `.pre-commit-config.yaml`，集成 black、isort、flake8、mypy、bandit
- **测试覆盖率提升**：从 89 个测试增加到 **185 个测试**，100% 通过
- **Makefile 构建**：新增 Makefile 简化常用命令

#### P1 级改进：架构优化
- **统一 API 响应格式**：新增 `apps/api/response.py`，所有 API 返回统一格式
  ```json
  {"code": 200, "success": true, "message": "...", "data": {...}}
  ```
- **日志敏感数据过滤**：新增 `apps/core/log_filters.py`，自动脱敏密码、令牌、密钥
- **CI/CD 流水线**：
  - 新增 `.github/workflows/publish.yml`：多版本测试（Python 3.11/3.12/3.13，SQLite/MySQL）
  - 新增 `.github/workflows/scheduled.yml`：定时依赖安全检查
  - 新增 `.github/dependabot.yml`：依赖自动更新

#### P2 级改进：功能增强
- **浏览量计数系统**：新增 `apps/core/views_counter.py`
  - 内存缓冲 + Redis + 批量数据库写入
  - 自动防刷机制（IP + User-Agent 指纹）
  - 中间件自动记录（`ViewsCounterMiddleware`）
- **全文搜索**：新增 `apps/core/search.py`
  - Meilisearch 优先（毫秒级响应）
  - Elasticsearch 回退支持
  - 自动索引同步
- **WebSocket 实时通知**：新增 `apps/notifications/` 完整应用
  - 实时通知推送
  - 未读消息计数
  - 通知类型分类
  - API 接口：获取列表、标记已读、批量操作

### 🔧 优化改进
- **API 异常处理增强**：修复 Http404 异常处理，返回统一格式
- **API 路由修复**：CategoryViewSet、TagViewSet 支持 slug 查找
- **文章评论接口修复**：comments action 参数修复
- **测试环境优化**：TESTING 标志跳过验证码验证
- **正则表达式修复**：修复 docstring 中的转义序列警告

### 📝 文档更新
- **README.md**：更新测试数量、新增功能说明
- **API.md**：添加通知 API 文档
- **CONTRIBUTING.md**：添加 pre-commit 使用说明
- **SECURITY.md**：更新安全特性列表

### 🧪 测试
- 测试数量：185 passed / 0 failed
- 新增 `apps/notifications/tests/`
- 新增 `apps/core/tests/test_views_counter.py`
- 新增 `apps/core/tests/test_search.py`

---

## [2.3.4] - 2026-04-04

### 🔒 安全修复
- **生产环境安全 Cookie 联动 HTTPS**：`SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` / `SECURE_HSTS_SECONDS` 现与 `USE_X_FORWARDED_PROTO` 联动，避免纯 HTTP 部署时登录和 CSRF 全部失效（此前默认 True 导致无 HTTPS 时 cookie 无法写入）
- **验证码密码学安全**：`apps/accounts/captcha.py` 从 `random` 模块升级为 `secrets` 模块（密码学安全随机数），验证码长度从 4 位提升至 6 位（1万 → 100万种组合），干扰线/噪点位置同步使用 `secrets.randbelow` 生成
- **nginx 安全头补充**：新增 X-Frame-Options、X-Content-Type-Options、X-XSS-Protection、Referrer-Policy、Content-Security-Policy、Permissions-Policy 共 6 个安全头

### 🐛 Bug 修复
- **中文 Slug 生成修复**：`Category` 和 `Post` 的 `save()` 方法改用 `generate_slug()` 替代 Django 内置 `slugify()`，修复中文标题/分类名生成空 slug 导致 URL 路由 404 的问题（`slugify("中文")` 返回空字符串）
- **API 文章详情 404**：`PostViewSet.lookup_field` 从默认 `pk`（整数）改为 `slug`（字符串），匹配前端按 slug 查找文章的请求
- **API 分类筛选 400**：新增 `PostFilter` 自定义过滤器，支持 `category=<slug>` 和 `tags=<slug>` 筛选（原 `filterset_fields` 只接受整数 ID）
- **Swagger/ReDoc 测试 404**：API 文档端点改为无条件注册，不再因测试环境 `DEBUG=False` 而返回 404

### 🧪 测试
- **forum 测试覆盖**：新增 `apps/forum/tests/test_models.py`，24 个测试用例覆盖 Board/Topic/Reply/ReplyLike 全部模型（此前 forum 模块零测试）
- **测试基线提升**：`89 passed / 0 failed`（此前 83 passed / 6 failed）

### 📝 文档
- **`.env.example` 升级为生产模板**：新增邮件配置、HTTPS 安全配置、监控配置（Sentry/Prometheus），所有敏感项改为 `<占位符>` 格式
- **`.env` 开发配置优化**：添加部署注意事项说明、SECRET_KEY 安全提示
- **`requirements/*.txt` 添加 .lock 文件使用说明**：明确生产部署应使用 `.lock` 文件

---

## [2.3.3] - 2026-04-02

### 新增
- **API 文档**：新增 `docs/API.md`，涵盖 21 个接口完整文档，包含 curl 示例、字段说明、错误码参考、FAQ
- **公安联网备案号功能**：
  - `SiteConfig` 新增 `site_gongan_beian` 字段 + 自动补全格式
  - Admin 添加"一键生成"按钮 + 公安备案链接自动生成
  - 页脚（footer.html）同步展示公安联网备案信息
- **一键自动部署**：新增 `deploy/auto-deploy.sh` 脚本（自动生成 `.env`、Docker 镜像加速、交互式创建管理员）

### 修复
- **moderation 数据库迁移缺失**：`is_primary` 字段未生成迁移文件，已修复
- **navbar.html 语法错误**：`</a>` 标签未正确闭合，导致 HTML 渲染异常
- **论坛浏览量递增方式优化**：从 `F()` 表达式 + `refresh_from_db` 改为纯整数递增
- **Docker 部署高危问题**：`SECURE_SSL_REDIRECT` / `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` 默认改为 False；重命名 `SecurityMiddleware` → `SecurityMonitorMiddleware` 解决中间件重名

### 优化
- **Admin 查询优化**：`list_select_related` + `raw_id_fields` 优化大数据量查询
- **模板 URL 规范化**：所有硬编码链接改为 `{% url %}` 模板标签
- **HTTP 请求工具 SSRF 防护**：内网 IP 检测覆盖全部私有地址段
- **端口扫描工具安全加固**：限制扫描范围

### 变更
- **ALLOWED_HOSTS 不再自动添加通配符**：DEBUG=True 也不再允许 `*`
- **CDN 脚本跨域防护**：Monaco Editor 和 TinyMCE 添加 `crossOrigin="anonymous"`
- **Clipboard API 升级**：优先使用 `navigator.clipboard.writeText`
- **Robots.txt 优化**：sitemap 从绝对 URL 改为相对路径
- **部署目录清理**：移除 19 个与 Docker 无关的脚本

---

## [2.3.1] - 2026-04-01

### 新增
- **一键自动部署**：`deploy/auto-deploy.sh`（配置生成 + 镜像加速 + 数据库迁移 + 交互式创建管理员）

### 修复
- **Docker 部署高危问题**：安全配置默认值修正
- **中间件命名冲突**：`SecurityMiddleware` → `SecurityMonitorMiddleware`
- **Dockerfile collectstatic 目录权限**

### 变更
- **依赖优化**：添加阿里云 pip 镜像加速
- **部署目录清理**

### 测试
- 测试基线：79 passed / 80 skipped

---

## [2.3.0] - 2026-03-31

### 新增
- **审核系统**：独立 `moderation` 应用（评论/主题/回复审核流程 + 百度内容审核 API 集成 + 审核 API 带限流保护）
- **安全增强**：安全响应头中间件、登录防护（django-axes）、上传文件安全扫描（ClamAV 可选）
- **Admin 模块化重构**：`apps/core/admin.py`（550+ 行）拆分为 10 个独立文件，自定义仪表盘首页

### 优化
- **查询性能**：博客/论坛列表页 `select_related` + `prefetch_related`，Redis 缓存热点数据
- **脚本清理工具增强**：排除 `.venv`、`.git` 等目录
- **migrate_to_mysql.py 适配**：ORM 动态获取真实表名

---

## [2.2.0] - 2026-03-15

### 新增
- **工具箱模块**：72+ 实用工具（编码转换、文本处理、加解密、图像类等）
- **API 层**：DRF 集成 + OpenAPI 文档（drf-spectacular）

---

## [2.1.0] - 2026-02-01

### 新增
- **论坛系统**：版块管理、主题发布/回复、置顶/锁定
- **用户系统增强**：用户资料页、头像上传、个人文章/主题列表

### 修复
- 评论嵌套显示问题
- Slug 重复导致 404

---

## [2.0.0] - 2026-01-01

### 重大变更
- **项目重构**：从单体应用重构为模块化架构（accounts/blog/forum/tools/api/core）
- **Docker Compose 生产部署方案**
- **分层配置**（base/development/production/test）
- **分层依赖管理**（requirements/base.txt 等）

---

## [1.0.0] - 2025-06-01

### 新增
- 基础博客功能（文章、分类、标签、评论）
- 用户认证系统
- Django Admin 后台管理
- 基础模板和样式
