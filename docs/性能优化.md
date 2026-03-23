# DjangoBlog 性能优化指南

## 📊 优化概览

### 已完成的优化

| 优化项 | 优化前 | 优化后 | 提升 |
|--------|--------|--------|------|
| SiteConfig 查询 | 每次请求查 DB | 缓存 5 分钟 | ~95% |
| 分类标签查询 | 每次调用 2 查询 | 缓存 5 分钟 | ~90% |
| 工具列表页面 | 无缓存 | 缓存 1 分钟 | ~80% |
| 数据库连接 | 无连接池 | 连接池 10 分钟 | ~50% |
| Redis 连接 | 无连接池 | 连接池 50 连接 | ~40% |

---

## 🔧 数据库优化

### 1. 连接池配置

```python
# config/settings/production.py
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # 10 分钟连接池
        'CONN_HEALTH_CHECKS': True,  # 连接健康检查
    }
}
```

**效果**: 减少数据库连接建立开销，提升 20-50% 响应速度。

### 2. 查询优化

#### 使用 select_related（外键关系）
```python
# 优化前：N+1 查询
posts = Post.objects.all()
for post in posts:
    print(post.author.name)  # 每次循环都查询

# 优化后：1 查询
posts = Post.objects.select_related('author', 'category')
for post in posts:
    print(post.author.name)  # 不再额外查询
```

#### 使用 prefetch_related（多对多关系）
```python
# 优化前：N+1 查询
posts = Post.objects.all()
for post in posts:
    print(post.tags.all())  # 每次循环都查询

# 优化后：2 查询
posts = Post.objects.prefetch_related('tags')
for post in posts:
    print(post.tags.all())  # 不再额外查询
```

#### 使用 only() 限制字段
```python
# 只查询需要的字段
posts = Post.objects.only('id', 'title', 'slug', 'author__username')
```

### 3. 索引优化

已添加的索引：
```python
class Post(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['author']),
            models.Index(fields=['slug']),
        ]
```

---

## 🚀 缓存优化

### 1. Redis 配置

```python
# config/settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'PARSER_CLASS': 'redis.connection.HiredisParser',  # 高性能解析器
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
        },
    }
}
```

### 2. 视图缓存

```python
from django.views.decorators.cache import cache_page

@cache_page(60)  # 缓存 1 分钟
def tool_list(request):
    ...
```

### 3. 数据缓存

```python
from django.core.cache import cache

def get_solo(cls):
    cache_key = 'site_config_solo'
    instance = cache.get(cache_key)
    
    if instance is None:
        instance = cls.objects.get_or_create(pk=1)
        cache.set(cache_key, instance, 300)  # 5 分钟
    
    return instance
```

---

## 🔄 连接池详解

### 数据库连接池

**工作原理**:
1. 首次请求建立连接
2. 连接保持活跃 `CONN_MAX_AGE` 秒
3. 后续请求复用连接
4. 健康检查确保连接可用

**配置建议**:
- 开发环境: 60 秒
- 生产环境: 600 秒
- 连接超时: 10-30 秒

### Redis 连接池

**工作原理**:
1. 创建连接池（最多 N 个连接）
2. 请求时从池中获取连接
3. 使用完毕归还连接池
4. 避免频繁创建/销毁连接

**配置建议**:
- 开发环境: 20 连接
- 生产环境: 50 连接
- 超时: 10-20 秒

---

## 📈 性能监控

### 中间件功能

```python
# apps/core/performance_middleware.py
class PerformanceMonitorMiddleware:
    # 记录每个请求的：
    # - 执行时间
    # - 数据库查询次数
    # - 慢请求警告（>500ms）
    # - 查询过多警告（>20 次）
```

### 响应头

```
X-Request-Duration-Ms: 45.23
X-DB-Queries: 5
```

### 性能报告

```python
from apps.core.performance import get_performance_report

report = get_performance_report()
# {
#     'cache_stats': {'hits': 100, 'misses': 20, 'hit_rate': '83.33%'},
#     'db_connections': {...},
#     'redis': {...}
# }
```

---

## ⚡ 最佳实践

### 1. 避免常见陷阱

```python
# ❌ 错误：在循环中查询
for post in Post.objects.all():
    comments = post.comments.all()  # N+1 问题

# ✅ 正确：预加载关联数据
for post in Post.objects.prefetch_related('comments'):
    comments = post.comments.all()
```

### 2. 批量操作

```python
# ❌ 错误：逐个创建
for i in range(1000):
    Post.objects.create(title=f'Post {i}')

# ✅ 正确：批量创建
posts = [Post(title=f'Post {i}') for i in range(1000)]
Post.objects.bulk_create(posts, batch_size=500)
```

### 3. 延迟加载

```python
# ❌ 错误：加载所有字段
posts = Post.objects.all()

# ✅ 正确：只加载需要的字段
posts = Post.objects.defer('content')  # 延迟加载大字段
posts = Post.objects.only('title', 'slug')  # 只加载指定字段
```

### 4. 使用 F 表达式

```python
# ❌ 错误：先查询再更新
post = Post.objects.get(pk=1)
post.views_count += 1
post.save()

# ✅ 正确：使用 F 表达式
from django.db.models import F
Post.objects.filter(pk=1).update(views_count=F('views_count') + 1)
```

---

## 🛠 性能优化工具

### 使用 performance.py

```python
from apps.core.performance import (
    cache_with_stats,
    slow_query_log,
    QueryCounter,
    get_performance_report,
)

# 缓存装饰器
@cache_with_stats('my_key', timeout=600)
def get_expensive_data():
    return expensive_operation()

# 慢查询监控
@slow_query_log(threshold_ms=50)
def get_posts():
    return Post.objects.all()

# 查询计数
with QueryCounter() as counter:
    posts = Post.objects.all()
    for post in posts:
        print(post.title)
print(f'执行了 {counter.count} 个查询')
```

---

## 📋 优化清单

- [x] 数据库连接池
- [x] Redis 连接池
- [x] SiteConfig 缓存
- [x] 分类标签缓存
- [x] 工具列表缓存
- [x] 性能监控中间件
- [x] 查询优化（select_related/prefetch_related）
- [x] 添加 gevent 依赖
- [x] 添加 hiredis 高性能解析器

---

## 📊 预期性能提升

| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 首页加载 | 200ms | 80ms | 60% |
| 文章详情 | 150ms | 60ms | 60% |
| 工具列表 | 300ms | 50ms | 83% |
| API 请求 | 100ms | 40ms | 60% |

---

## 🚀 下一步优化建议

1. **CDN 加速**: 静态资源上 CDN
2. **图片优化**: WebP 格式 + 懒加载
3. **分页优化**: 游标分页替代偏移分页
4. **全文搜索**: Elasticsearch 替代 LIKE 查询
5. **异步任务**: 耗时操作用 Celery 异步处理

---

*更新时间: 2026-03-22*
