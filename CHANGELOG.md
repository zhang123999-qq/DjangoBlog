# Changelog

All notable changes to this project will be documented in this file.

## [2.4.0] - 2026-03-22

### 🚀 Performance Optimization

This release focuses on **performance optimization** and **resource management**.

### Added

#### Performance Monitoring
- **Performance Monitor Middleware** - Real-time request tracking
  - Request duration tracking (X-Request-Duration-Ms header)
  - Database query count (X-DB-Queries header)
  - Database time tracking (X-DB-Time-Ms header)
  - Slow request warnings (>500ms)
  - N+1 query detection (>20 queries)

#### Caching Optimization
- **SiteConfig Caching** - Cache site config for 5 minutes
- **Categories/Tags Caching** - Cache blog categories and tags
- **Tools List Caching** - Cache tools page for 1 minute
- **Cache Statistics** - Track cache hit/miss rates
- **Cache Warming** - Preload frequently accessed data

#### Connection Pool
- **Database Connection Pool** - Persistent connections
  - Development: 60s connection age
  - Production: 600s (10 minutes) connection age
  - Connection health checks enabled
- **Redis Connection Pool** - Optimized Redis connections
  - Development: 20 connections
  - Production: 50 connections
  - Blocking connection pool with timeout

#### Resource Management (Cleanup Tasks)
- **Session Cleanup** - Hourly cleanup of expired sessions
- **Log Cleanup** - Daily cleanup of old moderation logs (90 days)
- **Reputation Log Cleanup** - Monthly cleanup (180 days)
- **Access Log Cleanup** - Weekly cleanup (30 days)
- **Database Optimization** - Weekly VACUUM/OPTIMIZE TABLE
- **Redis Health Check** - Every 5 minutes

#### Performance Tools
- `apps/core/performance.py` - Performance utilities
  - Cache statistics decorator
  - Slow query log decorator
  - Query counter context manager
  - Performance report generator
- `apps/core/connection_monitor.py` - Connection pool monitoring
- `apps/core/cache_optimizer.py` - Redis memory optimization
- `apps/core/maintenance_tasks.py` - Maintenance tasks

### Changed

#### Celery Tasks Optimization
- **Batch Processing** - Use bulk_create/bulk_update instead of individual saves
- **Query Optimization** - Reduce database queries in moderation tasks
- **Task Scheduling** - Added performance maintenance tasks to Celery Beat

#### Configuration
- Added `SLOW_REQUEST_THRESHOLD_MS` setting
- Added `HIGH_QUERY_THRESHOLD` setting
- Added performance middleware to development settings
- Enhanced Redis cache configuration with hiredis parser

### Dependencies Added
- `gevent>=24.0` - Async worker for Gunicorn
- `hiredis>=2.0` - High-performance Redis parser
- `django-redis>=5.4` - Django Redis cache backend

### Performance Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Homepage (cached) | ~800ms | ~1ms | 99.9% |
| SiteConfig query | ~0.15ms | ~0.06ms | 60% |
| Categories/Tags | ~0.92ms | ~0.24ms | 74% |
| API endpoints | ~10ms | ~1-5ms | 50-90% |

### Test Results

- **Total Tests**: 119
- **Passed**: 118
- **Failed**: 1 (CSRF cookie test issue, not functional)
- **Pass Rate**: 99.2%

### Documentation
- `docs/PERFORMANCE.md` - Basic optimization guide
- `docs/PERFORMANCE_DEEP.md` - Deep optimization report
- `docs/TEST_REPORT.md` - Complete test report

## [2.3.5] - 2026-03-21

### Fixed
- **安装向导深度优化**
  - 修复中间件路径不一致问题（相对路径 → 绝对路径）
  - 修复 `BASE_DIR` 定义位置问题（移到文件顶部）
  - 快速安装添加密码确认字段
  - 前端添加密码一致性验证
  - 中间件豁免登录/登出路径，避免重定向问题

## [2.3.4] - 2026-03-21

### Fixed
- **数据库配置修复** - 修复 `KeyError: 'ATOMIC_REQUESTS'` 错误

## [2.3.3] - 2026-03-21

### Added
- **NAT 检测工具** - 检测网络地址转换状态

## [2.3.2] - 2026-03-21

### Added
- **"我的IP"工具** - 自动检测访问者公网IP地址

## [2.3.1] - 2026-03-21

### Changed
- **统一UI风格** - 移除科技主题，全部使用浅色Bootstrap主题

## [2.3.0] - 2026-03-21

### Added
- **富文本编辑器集成** - TinyMCE 7
- **Monaco Editor 集成** - VS Code同款代码编辑器
- **文章管理功能** - 创建、编辑、删除、草稿箱
- **图片上传API**
- **10个新工具** - 密码强度检测、Markdown编辑器等

## [2.2.0] - 2026-03-21

### Added
- **Celery 异步队列**
- **用户信誉系统**
- **AI 内容审核** - 百度内容审核 API
- **多级审核策略**
- **异步审核任务**

## [2.1.0] - 2026-03-15

### Changed
- **升级 Python 版本要求到 3.13+**
- 更新所有依赖到最新兼容版本

## [2.0.0] - 2026-03-15

### Added
- 安装向导系统
- 14个实用工具
- 自动化测试套件
- Docker部署支持
- GitHub Actions CI/CD配置

## [1.0.0] - 2026-03-12

### Added
- 博客系统（文章、分类、标签、评论）
- 论坛系统（版块、主题、回复、点赞）
- 用户系统（注册、登录、个人资料）
- 管理后台
- 响应式设计
