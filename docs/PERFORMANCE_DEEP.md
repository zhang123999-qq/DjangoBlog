# DjangoBlog 深度性能优化报告

## 📊 性能瓶颈分析

### 1. 数据库层面

#### 问题：
- 多个模型缺少索引
- 连接池配置不完善
- 查询未优化

#### 解决方案：
| 模型 | 优化前 | 优化后 |
|------|--------|--------|
| User | 0 索引 | username, email 索引 |
| Category | 0 索引 | slug 索引 |
| Tag | 0 索引 | slug 索引 |
| Board | 0 索引 | slug 索引 |
| SensitiveWord | 0 索引 | word, is_active 索引 |

### 2. 缓存层面

#### 问题：
- SiteConfig 每次请求查数据库
- 分类/标签查询无缓存
- 工具列表主动禁用缓存

#### 解决方案：
```python
# SiteConfig 缓存
@classmethod
def get_solo(cls):
    cache_key = 'site_config_solo'
    instance = cache.get(cache_key)
    if instance is None:
        instance, _ = cls.objects.get_or_create(pk=1)
        cache.set(cache_key, instance, 300)  # 5 分钟
    return instance

# 分类标签缓存
def get_categories_and_tags():
    cache_key = 'blog_categories_tags'
    result = cache.get(cache_key)
    if result is None:
        result = (list(categories), list(tags))
        cache.set(cache_key, result, 300)
    return result
```

### 3. Celery 任务层面

#### 问题：
- `check_pending_moderation` 逐个创建提醒
- `auto_approve_old_pending` 逐个更新状态

#### 解决方案：
```python
# 批量创建提醒
reminders_to_create = []
for target_type, target_id in pending_items:
    reminders_to_create.append(ModerationReminder(...))

ModerationReminder.objects.bulk_create(
    reminders_to_create,
    ignore_conflicts=True
)

# 批量更新状态
Comment.objects.bulk_update(
    to_approve,
    ['review_status', 'review_note'],
    batch_size=100
)
```

---

## 🔧 回收机制

### 1. Session 清理

```python
@shared_task
def cleanup_expired_sessions():
    """每小时清理过期 Session"""
    expired_count = Session.objects.filter(
        expire_date__lt=timezone.now()
    ).delete()[0]
    return expired_count
```

### 2. 日志清理

| 日志类型 | 保留时间 | 清理频率 |
|----------|----------|----------|
| 审核日志 | 90 天 | 每天 |
| 信誉日志 | 180 天 | 每月 |
| 访问日志 | 30 天 | 每周 |

### 3. 缓存清理

```python
class CacheInvalidator:
    KEY_MAPPING = {
        'post': ['blog_categories', 'blog_tags'],
        'comment': ['site_statistics'],
        'sensitive_word': ['sensitive_words'],
    }
    
    @classmethod
    def invalidate(cls, model_name):
        keys_to_delete = cls.KEY_MAPPING.get(model_name, [])
        for key in keys_to_delete:
            cache.delete(key)
```

### 4. 数据库连接回收

```python
class ConnectionPoolMonitor:
    def recycle_stale_connections(self):
        """回收过期连接"""
        for alias in connections:
            conn = connections[alias]
            conn.close_if_unusable_or_obsolete()
```

### 5. Redis 内存回收

```python
class RedisMemoryOptimizer:
    @classmethod
    def get_optimization_suggestions(cls):
        """获取优化建议"""
        suggestions = []
        
        # 检查内存使用
        if used_memory_mb > 500:
            suggestions.append({
                'level': 'warning',
                'message': 'Redis 内存使用较高'
            })
        
        # 检查 TTL 分布
        if no_expiry > 100:
            suggestions.append({
                'level': 'info',
                'message': '有键没有设置过期时间'
            })
```

---

## ⏰ 定时任务配置

```python
CELERY_BEAT_SCHEDULE = {
    # 每 1 小时清理过期 Session
    'cleanup-expired-sessions': {
        'task': 'apps.core.maintenance_tasks.cleanup_expired_sessions',
        'schedule': 3600.0,
    },
    # 每 6 小时缓存预热
    'warmup-cache': {
        'task': 'apps.core.maintenance_tasks.warmup_cache',
        'schedule': 21600.0,
    },
    # 每天清理旧日志
    'cleanup-moderation-logs': {
        'task': 'apps.core.maintenance_tasks.cleanup_old_moderation_logs',
        'schedule': 86400.0,
    },
    # 每周优化数据库
    'optimize-database': {
        'task': 'apps.core.maintenance_tasks.optimize_database',
        'schedule': 604800.0,
    },
    # 每 5 分钟检查 Redis
    'check-redis-health': {
        'task': 'apps.core.maintenance_tasks.check_redis_health',
        'schedule': 300.0,
    },
}
```

---

## 📈 连接池配置

### 数据库连接池

```python
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # 10 分钟连接池
        'CONN_HEALTH_CHECKS': True,  # 连接健康检查
        'OPTIONS': {
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30,
        }
    }
}
```

### Redis 连接池

```python
CACHES = {
    'default': {
        'OPTIONS': {
            'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,  # 最大连接数
                'timeout': 20,  # 连接超时
            },
        }
    }
}
```

---

## 🛠 性能监控

### 响应头信息

```
X-Request-Duration-Ms: 45.23
X-DB-Queries: 5
X-DB-Time-Ms: 12.50
```

### 慢请求警告

```
[WARNING] 慢请求警告: /api/posts/ 耗时 520.00ms, 25 个数据库查询
[WARNING] 查询过多警告: /api/posts/ 执行了 25 个数据库查询, 可能存在 N+1 问题
```

### 性能报告 API

```python
from apps.core.performance import get_performance_report
from apps.core.cache_optimizer import get_cache_report
from apps.core.connection_monitor import get_health_status

# 性能报告
report = get_performance_report()
# {
#     'cache_stats': {'hits': 100, 'misses': 20, 'hit_rate': '83.33%'},
#     'db_connections': {...}
# }

# 缓存报告
cache_report = get_cache_report()
# {
#     'memory': {...},
#     'keys': 1234,
#     'suggestions': [...]
# }

# 健康状态
health = get_health_status()
# {
#     'database': True,
#     'redis': True,
#     'status': 'healthy'
# }
```

---

## 📋 优化清单

### 已完成 ✅

- [x] SiteConfig 缓存优化
- [x] 分类标签缓存优化
- [x] 工具列表缓存优化
- [x] 数据库连接池配置
- [x] Redis 连接池配置
- [x] 性能监控中间件
- [x] Celery 任务批量优化
- [x] Session 清理机制
- [x] 日志清理机制
- [x] 缓存预热机制
- [x] 连接池监控
- [x] Redis 内存优化器
- [x] 数据库索引优化迁移

### 待完成 ⏳

- [ ] 执行数据库迁移添加索引
- [ ] 配置 Redis 内存限制
- [ ] 添加 APM 监控（如 Sentry）
- [ ] 配置 CDN 加速
- [ ] 图片优化和懒加载

---

## 🚀 部署建议

### 生产环境检查清单

1. **数据库**
   - [ ] MySQL 连接池已配置
   - [ ] 索引已创建
   - [ ] 定期备份已配置

2. **Redis**
   - [ ] 内存限制已设置（建议 1GB）
   - [ ] 淘汰策略已配置（allkeys-lru）
   - [ ] 持久化已配置（AOF）

3. **Celery**
   - [ ] Worker 已启动
   - [ ] Beat 定时任务已启动
   - [ ] 监控（Flower）已配置

4. **监控**
   - [ ] 日志收集已配置
   - [ ] 性能监控已启用
   - [ ] 告警已配置

---

*更新时间: 2026-03-22*
*版本: v2.3.0*
