# DjangoBlog 更新日志

所有重要的更改记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased] - 2026-04-04

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
