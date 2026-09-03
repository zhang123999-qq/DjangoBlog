# 🏗 DjangoBlog 架构总览

> 一份替代旧 12 份模块文档的**精简架构说明**（替代：模块01-12 系列）

---

## 📐 项目定位

**DjangoBlog** —— 一个面向生产部署的 Django 综合站点，**博客 + 论坛 + 工具箱 + API** 四位一体。

| 维度 | 数值 |
|---|---|
| 版本 | 2.4.0 |
| Django | 4.2 LTS |
| Python | 3.13 |
| 代码量 | ~33,800 行（276 Python 文件）|
| 工具数 | 68 个在线工具 |
| API 端点 | ~60 个 URL |
| 提交数 | 297+ |
| 容器数 | 5（web + db + redis + celery_worker + celery_beat）|

---

## 🏛 整体架构

```
┌──────────────────────────────────────────────┐
│            宿主机 (Host)                      │
│   ┌────────┐    ┌────────────┐              │
│   │ Nginx  │───→│   Docker   │              │
│   │ :80/443│    │  Compose   │              │
│   └────────┘    └──────┬─────┘              │
│   + Cron 备份           ↓                     │
└─────────────────────────┼─────────────────────┘
                          ↓
┌──────────────────────────────────────────────┐
│    Docker Network: djangoblog                │
│  ┌────┐  ┌────┐  ┌────┐  ┌────┐  ┌────┐   │
│  │ db │  │redis│ │ web│  │celery│ beat│   │
│  │Mysql│ │ 7  │  │:8000│ │worker│     │   │
│  └────┘  └────┘  └────┘  └────┘  └────┘   │
│   :3306    :6379  Gunicorn                   │
└──────────────────────────────────────────────┘
```

---

## 📦 应用模块（7 个 app）

| App | 职责 | Model 数 | 关键文件 |
|---|---|---|---|
| **accounts** | 用户系统（注册/登录/资料/权限）| 2 | models / forms / views / signals |
| **blog** | 博客核心（文章/分类/标签/评论/点赞）| 5 | models / views / tasks / templatetags |
| **forum** | 论坛（主题/回复/互动）| 5 | models / views |
| **core** | 公共工具（slug 生成、healthz、缓存）| 1 | utils / views / db_backends |
| **notifications** | 实时通知（WebSocket 推送）| 1 | consumers / tasks |
| **tools** | 工具箱（68 个工具，编码/文本/加解密/图像）| 1 | tool_modules/ / views |
| **api** | REST API 入口（DRF + OpenAPI）| 0 | serializers / views / urls |

**独立模块**：
- **moderation** —— 内容审核（AI 审核 + 人工复核 + 百度 API）

### Model 总览

- `accounts`: User（自定义扩展）、UserProfile
- `blog`: Category、Tag、Post、Comment、Like
- `forum`: Category、Topic、Reply、Attachment、Subscription
- `core`: SiteSettings
- `notifications`: Notification
- `tools`: ToolUsage
- `moderation`: ContentReport、ModerationLog、ReviewQueue

---

## 🔄 数据流

### 请求流（Nginx → Django）

```
用户 → Nginx (80/443) → web:8000 (Gunicorn + gthread)
                          ↓
                    Django URL Router
                          ↓
              ┌───────────┼───────────┐
              ↓           ↓           ↓
         accounts/blog  forum    tools/api
              ↓
         ORM → MySQL
              ↓
         Cache (Redis) / Celery Task
```

### 后台任务流

```
触发（评论发布/审核/邮件等）
  ↓
Celery Task (apps/blog/tasks.py, moderation/tasks.py)
  ↓
Celery Worker (concurrency=4, prefork)
  ↓
Redis Broker / Result Backend
```

### 实时通知流

```
事件发生（评论、回复、@提及等）
  ↓
notifications.signals
  ↓
Django Channels (WebSocket)
  ↓
浏览器实时推送
```

---

## 🔌 关键中间件

| 组件 | 用途 |
|---|---|
| **django-axes** | 登录失败限流（防爆破）|
| **django-compressor** | 模板压缩（CSS/JS 合并压缩）|
| **whitenoise** | 静态文件服务 |
| **celery + redis** | 异步任务 |
| **channels** | WebSocket 实时通信 |
| **drf-spectacular** | OpenAPI 文档生成 |

---

## 🔐 安全层

| 措施 | 实现 |
|---|---|
| 登录防护 | django-axes（5 次失败锁 IP）|
| CSRF | Django 内置 + Trusted Origins |
| XSS | Django 模板自动转义 + CSP 头 |
| SQL 注入 | Django ORM 参数化查询 |
| 密码学 | argon2 / bcrypt |
| 限流 | django-ratelimit |
| 内容审核 | 百度 AI + 人工 + 自动三级 |
| 部署安全 | non-root 用户、secrets 注入、TLS |

---

## ⚙️ 配置层

```
config/
├── settings/
│   ├── base.py          # 基础配置
│   ├── development.py   # 开发环境
│   ├── production.py    # 生产环境
│   └── test.py          # 测试环境
├── urls.py              # 根路由
├── wsgi.py              # WSGI 入口
└── celery.py            # Celery 入口
```

**多环境管理**：
- 通过 `DJANGO_SETTINGS_MODULE` 环境变量切换
- 生产环境用 `config.settings.production`
- 敏感信息全部走环境变量（不落代码）

---

## 🧪 质量保障

| 工具 | 作用 |
|---|---|
| **pytest** | 测试框架（25 个 test_*.py，45 通过）|
| **mypy** | 静态类型检查 |
| **flake8** | 代码风格 |
| **black** | 代码格式化 |
| **bandit** | 安全扫描 |
| **pre-commit** | Git 钩子（提交前自动跑）|
| **GitHub Actions** | CI/CD 自动化 |

---

## 📈 性能优化

| 优化点 | 实现 |
|---|---|
| **数据库** | 索引、select_related、prefetch_related、F() 原子操作 |
| **缓存** | Redis（页面/会话/计数）|
| **静态资源** | WhiteNoise 压缩 + CDN 友好 |
| **Gunicorn** | gthread 模式（4 worker × 4 thread）|
| **异步** | Celery（邮件、统计、清理）|
| **压缩** | django-compressor |
| **图片** | WebP 自动转换（optimize_static.sh）|

---

## 🚀 部署架构

详见 [CI_DEPLOY.md](CI_DEPLOY.md) 和 [QUICKSTART.md](QUICKSTART.md)

```
开发 → CI 测试 → push to main → 自动部署 → 健康检查 → 上线
                                                   ↓
                                              失败 → 自动回滚
```

---

## 📊 项目指标

| 指标 | 数值 |
|---|---|
| API 端点 | 60 个 URL |
| 在线工具 | 68 个 |
| 测试用例 | 45 个通过 |
| 代码质量 | 9.5/10（自评）|
| 安全审计 | 已通过 |
| 部署就绪 | ✅ |

---

## 🔗 相关文档

- [README.md](../README.md) - 项目主页
- [QUICKSTART.md](QUICKSTART.md) - 5 分钟上手
- [API.md](API.md) - API 文档
- [CI_DEPLOY.md](CI_DEPLOY.md) - CI/CD 部署
- [OPERATIONS.md](OPERATIONS.md) - 日常运维

---

*本架构文档替代旧的 12 份模块文档。如需更深入了解某个模块，请直接看对应 `apps/<module>/` 下的代码 + 测试。*
