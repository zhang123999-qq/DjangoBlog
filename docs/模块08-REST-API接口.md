# 模块 08 — REST API 接口

> 路径: `apps/api/` | URL前缀: `/api/` | 框架: Django REST Framework

---

## 功能概览

基于 DRF 的 RESTful API，为前后端分离和第三方客户端提供数据接口。包含文章、分类、标、论坛版块、主题、评论等资源的查询接口，集成 OpenAPI 自动文档生成，提供文件上传和审核 API。**所有 ViewSet 均为只读模式**，审核接口使用独立的高防护 API（含限流 + 并发控制）。

---

## 文件清单

| 文件 | 内容 | 说明 |
|------|------|------|
| `views.py` | CategoryViewSet、TagViewSet、PostViewSet、BoardViewSet、TopicViewSet | 5 个 ReadOnlyModelViewSet |
| `search_views.py` | GlobalSearchView、PostSearchView、TopicSearchView、SearchHealthView | 搜索 API 与健康检查 |
| `moderation_views.py` | moderation_metrics_api、moderation_approve_api、moderation_reject_api | 🆕 审核 API（19.6KB，限流+并发防护）|
| `serializers.py` | 10 个序列化器：UserSerializer、CategorySerializer、TagSerializer、PostSerializer、PostListSerializer、CommentSerializer、BoardSerializer、TopicSerializer、TopicListSerializer、ReplySerializer | 序列化层 |
| `urls.py` | 路由配置（DRF Router + 手动路由）| 路由层 |
| `apps.py` | API 应用配置 | 应用注册 |
| `tests/test_endpoints.py` / `tests/test_views.py` | API 端点与视图测试 | 测试模块 |

---

## 路由配置

### ViewSet 路由（DRF Router 自动注册）

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/categories/` | 分类列表（含 `post_count`） | `AllowAny` |
| `GET` | `/api/categories/{slug}/` | 分类详情 | `AllowAny` |
| `GET` | `/api/categories/{slug}/posts/` | 分类下的文章（分页） | `AllowAny` |
| `GET` | `/api/tags/` | 标签列表（含 `post_count`） | `AllowAny` |
| `GET` | `/api/tags/{slug}/` | 标签详情 | `AllowAny` |
| `GET` | `/api/posts/` | 文章列表（仅已发布） | `AllowAny` |
| `GET` | `/api/posts/{slug}/` | 文章详情（slug 查找） | `AllowAny` |
| `GET` | `/api/posts/{slug}/comments/` | 文章评论列表（分页） | `AllowAny` |
| `GET` | `/api/boards/` | 版块列表（含 `topic_count`, `reply_count`） | `AllowAny` |
| `GET` | `/api/boards/{id}/` | 版块详情 | `AllowAny` |
| `GET` | `/api/boards/{id}/topics/` | 版块下的主题（分页） | `AllowAny` |
| `GET` | `/api/topics/` | 主题列表（仅已审核通过） | `IsAuthenticatedOrReadOnly` |
| `GET` | `/api/topics/{id}/` | 主题详情 | `IsAuthenticatedOrReadOnly` |
| `GET` | `/api/topics/{id}/replies/` | 主题回复列表（分页） | `IsAuthenticatedOrReadOnly` |

### 搜索 API 路由

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/search/` | 全局搜索（文章 + 主题） | `AllowAny` |
| `GET` | `/api/search/posts/` | 文章搜索（分页） | `AllowAny` |
| `GET` | `/api/search/topics/` | 主题搜索（分页，仅返回已审核通过主题） | `AllowAny` |
| `GET` | `/api/search/health/` | 搜索后端健康检查 | `AllowAny` |

> **参数校验**: `limit`、`page`、`page_size` 现在都会做正整数校验；非法值会返回 `400 Bad Request`，而不是 `500`。

### 审核 API 路由（手动注册）

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/moderation/metrics/` | 审核统计指标（近 N 分钟） | `IsAuthenticated` + moderator |
| `POST` | `/api/moderation/approve/{type}/{id}/` | 通过审核（API 模式） | `IsAuthenticated` + moderator |
| `POST` | `/api/moderation/reject/{type}/{id}/` | 拒绝审核（可选填备注） | `IsAuthenticated` + moderator |

### OpenAPI 文档路由

| 端点 | 说明 | 可用环境 |
|------|------|----------|
| `/api/schema/` | OpenAPI 3.0 Schema (JSON) | 所有环境 |
| `/api/docs/` | Swagger UI 文档界面 | DEBUG 模式 |
| `/api/redoc/` | ReDoc 文档界面 | DEBUG 模式 |

---

## ViewSet 详解

### PUBLISHED_POST_COUNT_FILTER — 全局已发布文章计数过滤器

```python
PUBLISHED_POST_COUNT_FILTER = (
    Q(posts__status="published")
    & Q(posts__slug__isnull=False)
    & ~Q(posts__slug="")
)
```

> 用于分类和标签的 `post_count` 注，只统计已发布且 slug 有效的文章。

### CategoryViewSet — 分类 API

| 端点 | 说明 |
|------|------|
| `GET /api/categories/` | 分类列表（含 `post_count` 字段，使用 `PUBLISHED_POST_COUNT_FILTER`） |
| `GET /api/categories/{slug}/` | 分类详情 |
| `GET /api/categories/{slug}/posts/` | 分类下文章列表（分页，仅已发布）|

**查询集**:
```python
Category.objects.annotate(
    post_count=Count("posts", filter=PUBLISHED_POST_COUNT_FILTER)
).order_by("name")
```

**自定义 Action — posts**:
```python
Post.objects.filter(category=category, status="published")
    .select_related("author", "category")
    .prefetch_related("tags")
    .order_by("-published_at", "-created_at")
```

**权限**: `AllowAny` | **限流**: `throttle_scope = "api_read"`

### TagViewSet — 标签 API

| 端点 | 说明 |
|------|------|
| `GET /api/tags/` | 标签列表（含 `post_count`）|
| `GET /api/tags/{slug}/` | 标签详情 |

**查询集**:
```python
Tag.objects.annotate(
    post_count=Count("posts", filter=PUBLISHED_POST_COUNT_FILTER)
).order_by("name")
```

**权限**: `AllowAny`

### PostViewSet — 文章 API

| 端点 | 说明 |
|------|------|
| `GET /api/posts/` | 文章列表（仅 `status="published"`）|
| `GET /api/posts/{slug}/` | 文章详情（按 slug 查找，非 pk）|
| `GET /api/posts/{slug}/comments/` | 获取文章评论列表（分页，仅 `review_status="approved"`）|

**查找字段**: `lookup_field = 'slug'`（非默认 pk）

**过滤器**:
| 参数 | 字段 | 说明 |
|------|------|------|
| `?category=xxx` | `category__slug` | 按分类 slug 过滤 |
| `?tags=xxx` | `tags__slug` | 按标签 slug 过滤 |

**搜索字段**: `["title", "content", "summary"]`
**排序字段**: `["published_at", "views_count", "created_at"]`
**默认排序**: `-published_at`（最新发布的在前）

**查询集**:
```python
Post.objects.filter(status="published")
    .select_related("author", "category")
    .prefetch_related("tags")
```

**retrieve 覆盖** — 增加浏览量:
```python
instance.increase_views()
serializer = self.get_serializer(instance)
```

**Serializer 动态切换**:
- `list` → `PostListSerializer`（精简）
- `retrieve` → `PostSerializer`（完整）

**权限**: `AllowAny`

### BoardViewSet — 版块 API

| 端点 | 说明 |
|------|------|
| `GET /api/boards/` | 版块列表（含 `topic_count`, `reply_count`）|
| `GET /api/boards/{id}/` | 版块详情 |
| `GET /api/boards/{id}/topics/` | 版块主题列表（分页，仅 `review_status="approved"`）|

**查询集**:
```python
Board.objects.all().order_by("name")
```

**自定义 Action — topics**:
```python
Topic.objects.filter(board=board, review_status="approved")
    .select_related("author", "board")
    .order_by("-is_pinned", "-last_reply_at", "-created_at")
```

**权限**: `AllowAny` | **限流**: `throttle_scope = "api_read"`

### TopicViewSet — 主题 API

| 端点 | 说明 |
|------|------|
| `GET /api/topics/` | 主题列表（仅 `review_status="approved"`）|
| `GET /api/topics/{id}/` | 主题详情 |
| `GET /api/topics/{id}/replies/` | 主题回复列表（分页，仅 `is_deleted=False`）|

**过滤器**:
| 参数 | 字段 | 说明 |
|------|------|------|
| `?board=N` | `board` | 按版块 ID 过滤 |
| `?author=N` | `author` | 按作者 ID 过滤 |

**搜索字段**: `["title", "content"]`
**排序字段**: `["created_at", "views_count", "reply_count"]`
**默认排序**: `-is_pinned, -created_at`（置顶帖在前，然后按时间倒序）

**查询集**:
```python
Topic.objects.filter(review_status="approved")
    .select_related("author", "board")
```

**retrieve 覆盖** — 增加浏览量:
```python
instance.increase_views()
```

**Serializer 动态切换**:
- `list` → `TopicListSerializer`
- `retrieve` → `TopicSerializer`

**权限**: `IsAuthenticatedOrReadOnly`

---

## 序列化器详解

### UserSerializer — 用户序列化器

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntegerField | 用户 ID |
| username | CharField | 用户名 |
| avatar | CharField | 头像 URL（从 `profile.avatar` 获取）|
| bio | CharField | 个人简介（从 `profile.bio` 获取）|
| website | CharField | 网站（从 `profile.website` 获取）|

> **只读字段**: `id`, `username`
> **隐私说明**: 为避免公开 API 暴露账号邮箱，`UserSerializer` 已移除 `email` 字段。
> **嵌套来源**: `profile` 关联表

### CategorySerializer — 分类序列化器

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntegerField | 分类 ID |
| name | CharField | 分类名称 |
| slug | SlugField | URL 别名 |
| post_count | IntegerField | 已发布文章数（annotate 计算）|
| created_at | DateTimeField | 创建时间 |

### TagSerializer — 标签序列化器

同 CategorySerializer 结构，fields: `id`, `name`, `slug`, `post_count`, `created_at`

### PostSerializer — 文章详情序列化器

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntegerField | 文章 ID |
| title | CharField | 标题 |
| slug | SlugField | URL 别名 |
| summary | TextField | 摘要 |
| content | TextField | 正文内容 |
| status | CharField | 发布状态 |
| views_count | IntegerField | 浏览量 |
| allow_comments | BooleanField | 是否允许评论 |
| published_at | DateTimeField | 发布时间 |
| created_at | DateTimeField | 创建时间 |
| author | UserSerializer | 作者详情（嵌套）|
| category | CategorySerializer | 分类详情（嵌套）|
| tags | TagSerializer(many) | 标签列表（嵌套）|

### PostListSerializer — 文章列表序列化器（精简版）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntegerField | 文章 ID |
| title | CharField | 标题 |
| slug | SlugField | URL 别名 |
| summary | TextField | 摘要 |
| views_count | IntegerField | 浏览量 |
| published_at | DateTimeField | 发布时间 |
| author | CharField | 作者名（`author.username`）|
| category_name | CharField | 分类名（`category.name`）|

> **与 PostSerializer 区别**: 不包含 `content` 字段，author/category 使用简单字符串（非嵌套对象），**减少 payload 大小**。

### CommentSerializer — 评论序列化器

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntegerField | 评论 ID |
| content | TextField | 评论内容 |
| user | UserSerializer | 用户详情（嵌套）|
| name | CharField | 匿名用户名称 |
| like_count | IntegerField | 点赞数 |
| created_at | DateTimeField | 创建时间 |

> **隐私说明**: 匿名评论邮箱仅保存在服务端模型中，公开评论 API 不再返回 `email` 字段。

### BoardSerializer — 版块序列化器

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntegerField | 块 ID |
| name | CharField | 版块名称 |
| slug | SlugField | URL 别名 |
| description | TextField | 版块描述 |
| topic_count | IntegerField | 主题数（annotate 计算）|
| reply_count | IntegerField | 回复数（annotate 计算）|
| created_at | DateTimeField | 创建时间 |

### TopicSerializer — 主题详情序列化器

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntegerField | 主题 ID |
| title | CharField | 标题 |
| content | TextField | 正文内容 |
| views_count | IntegerField | 浏览量 |
| reply_count | IntegerField | 回复数 |
| is_pinned | BooleanField | 是否置顶 |
| is_locked | BooleanField | 是否锁定 |
| created_at | DateTimeField | 创建时间 |
| author | UserSerializer | 作者详情（嵌套）|
| board | BoardSerializer | 版块详情（嵌套）|

### TopicListSerializer — 主题列表序列化器（精简版）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntegerField | 主题 ID |
| title | CharField | 标题 |
| views_count | IntegerField | 浏览量 |
| reply_count | IntegerField | 回复数 |
| is_pinned | BooleanField | 是否置顶 |
| created_at | DateTimeField | 创建时间 |
| author | CharField | 作者名（`author.username`）|
| board_name | CharField | 版块名（`board.name`）|

> **与 TopicSerializer 区别**: 不包含 `content`, `is_locked`，author/board 使用简单字符串。

### ReplySerializer — 回复序列化器

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntegerField | 回复 ID |
| content | TextField | 回复内容 |
| like_count | IntegerField | 点赞数 |
| created_at | DateTimeField | 创建时间 |
| author | UserSerializer | 作者详情（嵌套）|

---

## 审核 API 详解 (moderation_views.py) 🆕

> **19.6KB 的大文件** — 这是 API 模块中最复杂的部分，包含完整的限流 + 并发控制 + 指标监控 + OpenAPI 文档。

### 权限检查

```python
def _is_moderator(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
```

### 📊 moderation_metrics_api — 审核统计指标

**方法**: `GET /api/moderation/metrics/?minutes=10`

**功能**: 获取过去 N 分钟（1-120，默认 10）的审核 API 综合指标。

**返回数据**:
```json
{
    "success": true,
    "window_minutes": 10,
    "totals": {
        "requests_total": 150,
        "rate_limited": 5,
        "concurrency_limited": 2,
        "approve_success": 80,
        "approve_failed": 3,
        "reject_success": 45,
        "reject_failed": 2,
        "permission_denied": 10,
        "invalid_content_type": 2,
        "content_not_found": 1
    },
    "peak_concurrency": 8,
    "series": [
        {"bucket": "202604041830", "requests_total": 15, ...},
        {"bucket": "202604041831", "requests_total": 12, ...}
    ],
    "hotspots": [
        {"user_id": "5", "bucket": "202604041831", "count": 25}
    ],
    "thresholds": {
        "rate_limited": 5,
        "concurrency_limited": 3,
        "fail_rate": 0.2
    }
}
```

**内部实现**:
```
获取 minutes 参数（限制 1-120）
    ↓
遍历 N 个时间桶（每分钟一个）
    ↓
读取 Redis/Django cache 中的指标 key:
    ├── moderation:metric:{metric_name}:{bucket}
    ├── moderation:metric:peak_concurrency:{bucket}
    └── moderation:metric:user:{user_id}:{bucket}
    ↓
计算总和（totals）、时序数据（series）、热点用户（hotspots）
    ↓
读取配置阈值
```

### ✅ moderation_approve_api — 审核通过

**方法**: `POST /api/moderation/approve/{type}/{id}/`

**请求体**: 无（空 JSON 或省略）

**流程**:
```
验证权限（_is_moderator）
    ↓ 失败 → 403 (MODERATION_PERMISSION_DENIED)
检查限流（_check_rate_limit）
    ↓ 超限 → 429 (MODERATION_API_RATE_LIMITED)
获取并发锁（_enter_concurrency_guard）
    ↓ 超限 → 429 (MODERATION_API_CONCURRENCY_LIMITED)
    ↓
获取内容模型（_get_content_model）
    ↓ null → 400 (MODERATION_INVALID_CONTENT_TYPE)
查询内容（.filter(id=...).first()）
    ↓ null → 404 (MODERATION_CONTENT_NOT_FOUND)
    ↓
approve_instance(content, request.user, note="")
    ↓ 成功 → 200 {success: true, status: 'approved', id: xxx}
    ↓ 异常 → 500 (MODERATION_APPROVE_FAILED)
    ↓
释放并发锁（_leave_concurrency_guard）
记录耗时日志
```

### ❌ moderation_reject_api — 审核拒绝

**方法**: `POST /api/moderation/reject/{type}/{id}/`

**请求体**: 可选传 `review_note` 字段
```json
{"review_note": "包含广告内容"}
```

**流程**: 同 approve，调用 `reject_instance(content, request.user, note=review_note)`

### 🛡️ 限流系统

```python
def _check_rate_limit(request):
    limit = MODERATION_API_RATE_LIMIT_PER_MIN  # 默认 120 次/分钟
    user_id = user.id 或 "anon"
    bucket = 当前分钟桶 "YYYYMMDDHHmm"
    key = f"moderation:rate:{user_id}:{bucket}"
    cache.incr(key, 60s TTL)
    count > limit → 限流
```

**特性**:
- **原子操作**: 使用 `cache.incr()` 确保并发安全
- **容错降级**: `ValueError` 时尝试 `cache.add()` → 最后使用 `cache.get() + cache.set()`
- **用户隔离**: 每个用户独立限流

### 🛡️ 并发控制

```python
def _enter_concurrency_guard(request):
    max_conc = MODERATION_API_MAX_CONCURRENCY  # 默认 20
    key = f"moderation:conc:{user_id}"
    cache.incr(key, 120s TTL)
    new_current > max_conc → 并发限制（并回退计数）
    else → 返回 guard_key
```

```python
def _leave_concurrency_guard(key):
    current = cache.get(key, 0)
    if current <= 1:
        cache.delete(key)
    else:
        cache.set(key, current - 1, 120)
```

**特性**:
- **原子操作**: `cache.incr()`
- **finally 保证释放**: 即使异常也释放锁
- **容错降级**: 同限流系统

### 📈 指标收集系统

```python
def _metric_incr(name):
    bucket = 当前分钟桶
    key = f"moderation:metric:{name}:{bucket}"
    cache.set(key, count + delta, 3600s TTL)
```

**收集的指标项**:

| 指标名 | 说明 |
|--------|------|
| `requests_total` | 总请求数 |
| `rate_limited` | 被限流次数 |
| `concurrency_limited` | 被并发限制次数 |
| `approve_success` | 审核通过成功数 |
| `approve_failed` | 审核通过失败数 |
| `reject_success` | 审核拒绝成功数 |
| `reject_failed` | 审核拒绝失败数 |
| `permission_denied` | 权限被拒次数 |
| `invalid_content_type` | 无效类型次数 |
| `content_not_found` | 内容未找到次数 |

**用户热点追踪**:
```python
def _record_user_hotspot(user_id):
    key = f"moderation:metric:user:{user_id}:{bucket}"
```

**峰值并发记录**:
```python
def _record_peak_concurrency(user_id, current):
    # 全局峰值
    key = f"moderation:metric:peak_concurrency:{bucket}"
    # 用户峰值
    key = f"moderation:metric:peak_concurrency:user:{user_id}:{bucket}"
```

### 🔗 OpenAPI 文档集成

所有审核 API 都使用 `@extend_schema` 装饰器，生成完整的 OpenAPI 3.0 规范：

```python
@extend_schema(
    operation_id="api_moderation_approve",
    summary="审核通过（JSON API）",
    tags=["moderation"],
    request=inline_serializer(...),
    responses={
        200: OpenApiResponse(...),
        400: OpenApiResponse(...),
        403: OpenApiResponse(...),
        404: OpenApiResponse(...),
        429: OpenApiResponse(...),
        500: OpenApiResponse(...),
    },
)
```

**内联序列化器**:
- `ApproveRequestSerializer` — 请求体（空）
- `RejectRequestSerializer` — 请求体（`review_note`）
- `ApproveSuccessSerializer` — 成功响应（`success`, `status`, `id`）
- `RejectSuccessSerializer` — 成功响应
- `MetricsSerializer` — 指标响应

---

## 权限设计

| 权限级别 | 端点 |
|----------|------|
| `AllowAny` | 分类、标签、文章、版块列表和详情 |
| `IsAuthenticatedOrReadOnly` | 主题列表及详情（已认证可写）|
| `IsAuthenticated` + moderator | 审核 API（approve/reject/metrics）|

---

## 性能优化

### 查询优化

| 技术 | 应用位置 | 说明 |
|------|----------|------|
| `select_related` | 所有 ViewSet | 预加载ForeignKey（author, category, board）|
| `prefetch_related` | PostViewSet | 预加载 M2M 关系（tags）|
| `annotate` + `Count` | Category/Tag/Board | 在数据库层计算计数，避免 N+1 |
| 不同 Serializer | Post/Topic | 列表使用精简版，详情使用完整版 |

### 只读 API

**所有 5 个 ViewSet 均为 `ReadOnlyModelViewSet`**，仅支持 GET 请求（查询操作）。创建/更新/删除操作通过 Django 表单视图完成。

---

## 配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MODERATION_API_RATE_LIMIT_PER_MIN` | 120 | 审核 API 每用户每分钟最大请求数 |
| `MODERATION_API_MAX_CONCURRENCY` | 20 | 审核 API 每用户最大并发请求数 |
| `MODERATION_UI_ALERT_RATE_LIMITED` | 5 | 限流告警阈值 |
| `MODERATION_UI_ALERT_CONCURRENCY_LIMITED` | 3 | 并发限制告警阈值 |
| `MODERATION_UI_ALERT_FAIL_RATE` | 0.2 | 失败率告警阈值（20%）|

---

## 错误处理

| HTTP 状态 | 错误码 | 说明 |
|-----------|--------|------|
| 400 | `MODERATION_INVALID_CONTENT_TYPE` | 无效的内容类型（非 comment/topic/reply）|
| 403 | `MODERATION_PERMISSION_DENIED` | 权限不足（非 staff/superuser）|
| 404 | `MODERATION_CONTENT_NOT_FOUND` | 内容不存在 |
| 429 | `MODERATION_API_RATE_LIMITED` | 请求频率超限 |
| 429 | `MODERATION_API_CONCURRENCY_LIMITED` | 并发请求超限 |
| 500 | `MODERATION_APPROVE_FAILED` | 通过审核失败 |
| 500 | `MODERATION_REJECT_FAILED` | 拒绝审核失败 |

---

## API 文档

| 端点 | 说明 | 可用环境 |
|------|------|----------|
| `/api/schema/` | OpenAPI 3.0 Schema (JSON) | 所有环境 |
| `/api/docs/` | Swagger UI 文档界面 | DEBUG 模式 |
| `/api/redoc/` | ReDoc 文档界面 | DEBUG 模式 |

---

## 依赖关系

| 依赖 | 来源 | 说明 |
|------|------|------|
| `djangorestframework` | DRF | API 框架 |
| `django-filter` | Django Filter | 过滤后端 |
| `drf-spectacular` | DRF Spectacular | OpenAPI 文档 |
| `blog` | Category, Tag, Post, Comment | 数据模型 |
| `forum` | Board, Topic, Reply | 数据模型 |
| `accounts` | User | 用户模型 |
| `moderation` | approve_instance, reject_instance | 审核服务 |
| `core` | ErrorCodes, api_error_payload | 错误码系统 |

---

## 错误处理

| 场景 | 行为 |
|------|------|
| 内容类型无效 | 400 + `MODERATION_INVALID_CONTENT_TYPE` |
| 内容未找到 | 404 + `MODERATION_CONTENT_NOT_FOUND` |
| 权限不足 | 403 + `MODERATION_PERMISSION_DENIED` |
| 限流触发 | 429 + `MODERATION_API_RATE_LIMITED` |
| 并发超限 | 429 + `MODERATION_API_CONCURRENCY_LIMITED` |
| 审核失败 | 500 + `MODERATION_APPROVE_FAILED`/`MODERATION_REJECT_FAILED` |
| 缓存 incr 失败 | 降级到 add → get+set |

---

*文档版本: v2.0 | 2026-04-04 | 完整度检查通过 ✅ | 覆盖文件: 7 源文件（含 19.6KB moderation_views.py）*
