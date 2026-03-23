# DjangoBlog 异步审核系统文档

## 概述

本次升级实现了以下功能：

1. **Celery 异步队列** - 处理耗时任务
2. **用户信誉系统** - 基于行为的智能分级
3. **AI 内容审核** - 百度内容审核 API 集成
4. **多级审核策略** - 根据用户信誉自动决策
5. **图片审核支持** - AI 图片违规检测

## 架构

```
用户提交内容
    ↓
┌─────────────────────────────────────┐
│        审核策略引擎                   │
│  (moderation/strategy.py)           │
├─────────────────────────────────────┤
│  1. 获取用户信誉等级                  │
│  2. 高信誉 → 自动发布                │
│  3. 低信誉 → 强制人工审核             │
│  4. 普通用户 → 敏感词 + AI 双重检测   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│        Celery 异步队列               │
│  (moderation/tasks.py)              │
├─────────────────────────────────────┤
│  - async_moderate_text()            │
│  - async_moderate_image()           │
│  - check_pending_moderation()       │
│  - auto_approve_old_pending()       │
│  - update_reputation_clean_days()   │
└─────────────────────────────────────┘
```

## 安装

### 1. 安装依赖

```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# 安装新依赖
pip install celery redis baidu-aip flower
```

### 2. 启动 Redis

**Windows:**
```bash
# 方式1: 使用 WSL
wsl
redis-server

# 方式2: 使用 Docker
docker run -d -p 6379:6379 redis
```

**Linux/macOS:**
```bash
redis-server
```

### 3. 数据库迁移

```bash
python manage.py makemigrations moderation
python manage.py migrate
```

### 4. 启动 Celery

**Windows:**
```bash
# 启动 Worker
start_celery.bat worker

# 启动 Beat (定时任务)
start_celery.bat beat

# 启动 Flower (监控界面)
start_celery.bat flower

# 或一次性启动全部
start_celery.bat all
```

**Linux/macOS:**
```bash
chmod +x start_celery.sh
./start_celery.sh all
```

## 配置

### 环境变量 (.env)

```env
# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 百度内容审核 API
BAIDU_APP_ID=your_app_id
BAIDU_API_KEY=your_api_key
BAIDU_SECRET_KEY=your_secret_key

# 审核模式: auto / manual / hybrid
MODERATION_MODE=hybrid
MODERATION_AI_THRESHOLD=0.8
```

### 百度内容审核 API

1. 访问 [百度 AI 开放平台](https://ai.baidu.com/)
2. 创建应用，获取 APP_ID、API_KEY、SECRET_KEY
3. 免费额度：每天 10000 次

## 使用

### 审核内容

```python
from moderation.strategy import get_moderation_strategy
from moderation.tasks import async_moderate_text

# 同步审核（适用于简单场景）
strategy = get_moderation_strategy()
result = strategy.moderate_content(user, content)
# result = {
#     'status': 'approved' / 'rejected' / 'pending',
#     'strategy': 'auto_publish' / 'ai_rejected' / etc,
#     'message': '审核意见说明',
# }

# 异步审核（推荐，不阻塞请求）
async_moderate_text.delay('comment', comment.id, comment.content, user.id)
```

### 审核图片

```python
from moderation.tasks import async_moderate_image

# 异步图片审核
async_moderate_image.delay(
    content_type='comment',
    content_id=comment.id,
    image_path='/path/to/image.jpg',
    user_id=user.id
)
```

### 用户信誉

```python
from moderation.reputation import UserReputation

# 获取用户信誉
reputation = UserReputation.get_or_create_for_user(user)

# 查看信誉等级
print(reputation.level)  # 'trusted' / 'normal' / 'low'
print(reputation.score)  # 0-100

# 调整信誉分
reputation.update_score(5, '内容通过审核')
reputation.update_score(-5, '内容被拒绝')
```

## 定时任务

| 任务 | 频率 | 说明 |
|-----|------|------|
| check_pending_moderation | 每 6 小时 | 检查待审核内容，生成提醒 |
| auto_approve_old_pending | 每天 2:00 | 自动通过 24 小时无敏感词的内容 |
| update_reputation_clean_days | 每天 3:00 | 更新用户连续无违规天数 |

## 监控

### Flower 监控界面

访问 http://localhost:5555 查看：
- 任务队列状态
- Worker 状态
- 任务执行历史
- 实时监控

### 日志

```bash
# 查看 Celery 日志
tail -f logs/celery.log

# 查看审核日志（Django Admin）
访问 /admin/moderation/moderationlog/
```

## 管理后台

访问 `/admin/moderation/`：

- **敏感词管理** - 添加/编辑/删除敏感词
- **用户信誉管理** - 查看用户信誉分，手动调整
- **审核日志** - 查看所有审核记录
- **审核提醒** - 查看待处理的提醒

## 信誉规则

| 行为 | 分数变化 |
|-----|---------|
| 内容通过审核 | +1 |
| 内容被拒绝 | -5 |
| 被举报 | -10 |
| 连续 7 天无违规 | +5 |

### 信誉等级

| 等级 | 分数范围 | 审核策略 |
|-----|---------|---------|
| 高信誉 | 80-100 | 自动发布，无需审核 |
| 正常 | 30-79 | 敏感词 + AI 检测 |
| 低信誉 | 0-29 | 强制人工审核 |

## 开发环境 vs 生产环境

### 开发环境

- 使用 MockModerationService（模拟审核）
- SQLite 数据库
- 本地 Redis

### 生产环境

- 使用百度 AI 审核
- MySQL 数据库
- Redis 集群
- Supervisor 管理 Celery 进程

## 故障排查

### Celery 无法连接 Redis

```bash
# 检查 Redis 是否运行
redis-cli ping
# 应返回 PONG

# 检查端口
netstat -an | grep 6379
```

### 任务不执行

```bash
# 检查 Worker 是否运行
celery -A config inspect active

# 检查队列
celery -A config inspect reserved
```

### AI 审核失败

1. 检查百度 AI 配置是否正确
2. 检查网络连接
3. 查看日志：`logs/django.log`

## 升级说明

### 数据库变更

新增表：
- `moderation_userreputation` - 用户信誉
- `moderation_reputationlog` - 信誉日志

### 代码变更

新增文件：
- `config/celery.py` - Celery 配置
- `moderation/reputation.py` - 用户信誉模型
- `moderation/ai_service.py` - AI 审核服务
- `moderation/strategy.py` - 审核策略引擎
- `moderation/tasks.py` - Celery 异步任务

修改文件：
- `pyproject.toml` - 添加新依赖
- `config/settings/base.py` - 添加 Celery 配置
- `moderation/models.py` - 导出新模型
- `moderation/admin.py` - 注册新模型

---

**版本**: v2.2.0
**更新时间**: 2026-03-21
