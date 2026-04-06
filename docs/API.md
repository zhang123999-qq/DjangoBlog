# DjangoBlog API 接口文档

> 版本: 1.4.0
> 基础路径: `/api/`
> 文档更新: 2026-04-06

---

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [认证与授权](#认证与授权)
4. [通用规范](#通用规范)
5. [博客 API](#博客-api)
6. [论坛 API](#论坛-api)
7. [通知 API](#通知-api)
8. [工具 API](#工具-api)
9. [上传 API](#上传-api)
10. [审核 API](#审核-api)
11. [错误码参考](#错误码参考)
12. [限流策略](#限流策略)
13. [常见问题](#常见问题)
14. [在线文档](#在线文档)

---

## 概述

DjangoBlog 提供 RESTful API，支持博客文章、论坛、文件上传、内容审核等功能。

### 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| Django | 4.2 LTS | Web 框架 |
| Django REST Framework | 3.14+ | API 框架 |
| drf-spectacular | 0.27+ | OpenAPI 3.0 文档生成 |
| Redis | 7+ | 缓存 + 限流 |
| Celery | 5+ | 异步任务（可选） |

### API 基础路径

```
https://your-domain.com/api/
```

### 响应格式

所有 API 返回统一的 JSON 格式：

**成功响应**:

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "id": 1,
    "title": "文章标题",
    "content": "文章内容..."
  }
}
```

**错误响应**:

```json
{
  "code": 400,
  "success": false,
  "message": "请求参数错误",
  "data": null
}
```

**分页响应**:

```json
{
  "count": 100,
  "next": "https://example.com/api/posts/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## 快速开始

### 1. 获取文章列表

```bash
curl -X GET "https://your-domain.com/api/posts/" \
  -H "Accept: application/json"
```

### 2. 搜索文章

```bash
curl -X GET "https://your-domain.com/api/posts/?search=django" \
  -H "Accept: application/json"
```

### 3. 获取文章详情

```bash
curl -X GET "https://your-domain.com/api/posts/1/" \
  -H "Accept: application/json"
```

### 4. 上传图片（需认证）

```bash
curl -X POST "https://your-domain.com/api/upload/image/" \
  -H "Authorization: Token your-token-here" \
  -F "file=@/path/to/image.jpg"
```

### 5. 审核操作（需管理员）

```bash
curl -X POST "https://your-domain.com/api/moderation/approve/comment/123/" \
  -H "Authorization: Token admin-token-here" \
  -H "Content-Type: application/json"
```

---

## 认证与授权

### 认证方式

| 方式 | 说明 |
|------|------|
| Session | 登录后 Cookie 认证 |
| Token | Header: `Authorization: Token <token>` |

### 权限级别

| 权限 | 说明 |
|------|------|
| AllowAny | 无需认证 |
| IsAuthenticated | 需要登录 |
| IsAuthenticatedOrReadOnly | 读取无需认证，写入需要登录 |
| IsAdminUser | 仅管理员 |

---

## 通用规范

### 请求头

```
Content-Type: application/json
Accept: application/json
Authorization: Token <token>  # 需要认证的接口
```

### HTTP 方法

| 方法 | 说明 |
|------|------|
| GET | 获取资源 |
| POST | 创建资源 / 执行操作 |
| PUT | 完整更新 |
| PATCH | 部分更新 |
| DELETE | 删除资源 |

### 分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量（最大 100） |

---

## 博客 API

### 分类接口

#### 获取分类列表

```
GET /api/categories/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/categories/" \
  -H "Accept: application/json"
```

**响应示例**:

```json
[
  {
    "id": 1,
    "name": "技术文章",
    "slug": "tech",
    "post_count": 42,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 获取分类详情

```
GET /api/categories/{id}/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/categories/1/" \
  -H "Accept: application/json"
```

**响应示例**:

```json
{
  "id": 1,
  "name": "技术文章",
  "slug": "tech",
  "post_count": 42,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 获取分类下的文章

```
GET /api/categories/{id}/posts/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/categories/1/posts/?page=1&page_size=10" \
  -H "Accept: application/json"
```

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |

**响应示例**:

```json
{
  "count": 42,
  "next": "/api/categories/1/posts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Django 入门教程",
      "slug": "django-tutorial",
      "summary": "本文介绍 Django 基础...",
      "views_count": 1234,
      "published_at": "2024-01-15T10:00:00Z",
      "author": "admin",
      "category_name": "技术文章"
    }
  ]
}
```

---

### 标签接口

#### 获取标签列表

```
GET /api/tags/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/tags/" \
  -H "Accept: application/json"
```

**响应示例**:

```json
[
  {
    "id": 1,
    "name": "Python",
    "slug": "python",
    "post_count": 28,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 获取标签详情

```
GET /api/tags/{id}/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/tags/1/" \
  -H "Accept: application/json"
```

**响应示例**:

```json
{
  "id": 1,
  "name": "Python",
  "slug": "python",
  "post_count": 28,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 文章接口

#### 获取文章列表

```
GET /api/posts/
```

**权限**: AllowAny

**curl 示例**:

```bash
# 基础请求
curl -X GET "https://your-domain.com/api/posts/" \
  -H "Accept: application/json"

# 搜索文章
curl -X GET "https://your-domain.com/api/posts/?search=django" \
  -H "Accept: application/json"

# 按分类筛选
curl -X GET "https://your-domain.com/api/posts/?category=1" \
  -H "Accept: application/json"

# 按标签筛选（多个用逗号分隔）
curl -X GET "https://your-domain.com/api/posts/?tags=1,2,3" \
  -H "Accept: application/json"

# 排序
curl -X GET "https://your-domain.com/api/posts/?ordering=-views_count" \
  -H "Accept: application/json"
```

**查询参数**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| category | int | 分类 ID 筛选 | `category=1` |
| tags | string | 标签 ID 筛选（多个用逗号分隔） | `tags=1,2,3` |
| author | int | 作者 ID 筛选 | `author=1` |
| search | string | 搜索标题/内容/摘要 | `search=django` |
| ordering | string | 排序字段（`-` 表示降序） | `ordering=-views_count` |
| page | int | 页码 | `page=1` |
| page_size | int | 每页数量（默认 20，最大 100） | `page_size=50` |

**排序字段**:

| 字段 | 说明 |
|------|------|
| published_at | 发布时间 |
| -published_at | 发布时间降序 |
| views_count | 浏览量 |
| -views_count | 浏览量降序 |
| created_at | 创建时间 |

**响应示例**:

```json
{
  "count": 100,
  "next": "/api/posts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Django 入门教程",
      "slug": "django-tutorial",
      "summary": "本文介绍 Django 基础...",
      "views_count": 1234,
      "published_at": "2024-01-15T10:00:00Z",
      "author": "admin",
      "category_name": "技术文章"
    }
  ]
}
```

#### 获取文章详情

```
GET /api/posts/{id}/
```

**权限**: AllowAny

**说明**: 访问时自动增加浏览量

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/posts/1/" \
  -H "Accept: application/json"
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 文章 ID |
| title | string | 文章标题 |
| slug | string | URL 别名 |
| summary | string | 摘要 |
| content | string | 正文（Markdown 格式） |
| status | string | 状态：`published`, `draft` |
| views_count | int | 浏览量 |
| allow_comments | bool | 是否允许评论 |
| published_at | datetime | 发布时间（ISO 8601） |
| created_at | datetime | 创建时间（ISO 8601） |
| author | object | 作者信息 |
| category | object | 分类信息 |
| tags | array | 标签列表 |

**响应示例**:

```json
{
  "id": 1,
  "title": "Django 入门教程",
  "slug": "django-tutorial",
  "summary": "本文介绍 Django 基础...",
  "content": "# Django 入门\n\n...",
  "status": "published",
  "views_count": 1235,
  "allow_comments": true,
  "published_at": "2024-01-15T10:00:00Z",
  "created_at": "2024-01-14T08:00:00Z",
  "author": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "avatar": "/media/avatars/admin.jpg",
    "bio": "全栈开发者",
    "website": "https://example.com"
  },
  "category": {
    "id": 1,
    "name": "技术文章",
    "slug": "tech",
    "post_count": 42
  },
  "tags": [
    {
      "id": 1,
      "name": "Python",
      "slug": "python",
      "post_count": 28
    }
  ]
}
```

#### 获取文章评论

```
GET /api/posts/{id}/comments/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/posts/1/comments/" \
  -H "Accept: application/json"
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 评论 ID |
| content | string | 评论内容 |
| user | object | 登录用户信息（已登录用户） |
| name | string | 访客姓名（未登录用户） |
| email | string | 访客邮箱（未登录用户） |
| like_count | int | 点赞数 |
| created_at | datetime | 创建时间 |

**响应示例**:

```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "content": "写得很好！",
      "user": {
        "id": 2,
        "username": "reader",
        "avatar": "/media/avatars/reader.jpg",
        "bio": "",
        "website": ""
      },
      "name": null,
      "email": null,
      "like_count": 5,
      "created_at": "2024-01-16T12:00:00Z"
    }
  ]
}
```

---

## 论坛 API

### 版块接口

#### 获取版块列表

```
GET /api/boards/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/boards/" \
  -H "Accept: application/json"
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 版块 ID |
| name | string | 版块名称 |
| slug | string | URL 别名 |
| description | string | 版块描述 |
| topic_count | int | 主题数量 |
| reply_count | int | 回复数量 |
| created_at | datetime | 创建时间 |

**响应示例**:

```json
[
  {
    "id": 1,
    "name": "技术讨论",
    "slug": "tech",
    "description": "技术相关话题讨论",
    "topic_count": 156,
    "reply_count": 892,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 获取版块详情

```
GET /api/boards/{id}/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/boards/1/" \
  -H "Accept: application/json"
```

**响应示例**:

```json
{
  "id": 1,
  "name": "技术讨论",
  "slug": "tech",
  "description": "技术相关话题讨论",
  "topic_count": 156,
  "reply_count": 892,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 获取版块下的主题

```
GET /api/boards/{id}/topics/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/boards/1/topics/?page=1&page_size=20" \
  -H "Accept: application/json"
```

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |

**响应示例**:

```json
{
  "count": 156,
  "next": "/api/boards/1/topics/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Django 5.0 新特性讨论",
      "views_count": 567,
      "reply_count": 23,
      "is_pinned": true,
      "created_at": "2024-01-10T14:00:00Z",
      "author": "developer",
      "board_name": "技术讨论"
    }
  ]
}
```

---

### 主题接口

#### 获取主题列表

```
GET /api/topics/
```

**权限**: AllowAny

**curl 示例**:

```bash
# 基础请求
curl -X GET "https://your-domain.com/api/topics/" \
  -H "Accept: application/json"

# 按版块筛选
curl -X GET "https://your-domain.com/api/topics/?board=1" \
  -H "Accept: application/json"

# 搜索主题
curl -X GET "https://your-domain.com/api/topics/?search=django" \
  -H "Accept: application/json"
```

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| board | int | 版块 ID 筛选 |
| author | int | 作者 ID 筛选 |
| search | string | 搜索标题/内容 |
| ordering | string | 排序字段 |
| page | int | 页码 |
| page_size | int | 每页数量 |

**排序字段**:

| 字段 | 说明 |
|------|------|
| -is_pinned | 置顶优先（默认） |
| -created_at | 创建时间降序 |
| -views_count | 浏览量降序 |
| -reply_count | 回复数降序 |

#### 获取主题详情

```
GET /api/topics/{id}/
```

**权限**: IsAuthenticatedOrReadOnly

**说明**: 访问时自动增加浏览量

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/topics/1/" \
  -H "Accept: application/json"
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主题 ID |
| title | string | 主题标题 |
| content | string | 主题内容（Markdown 格式） |
| views_count | int | 浏览量 |
| reply_count | int | 回复数 |
| is_pinned | bool | 是否置顶 |
| is_locked | bool | 是否锁定 |
| created_at | datetime | 创建时间 |
| author | object | 作者信息 |
| board | object | 版块信息 |

**响应示例**:

```json
{
  "id": 1,
  "title": "Django 5.0 新特性讨论",
  "content": "大家好，今天我们来讨论...",
  "views_count": 568,
  "reply_count": 23,
  "is_pinned": true,
  "is_locked": false,
  "created_at": "2024-01-10T14:00:00Z",
  "author": {
    "id": 2,
    "username": "developer",
    "avatar": "/media/avatars/developer.jpg",
    "bio": "",
    "website": ""
  },
  "board": {
    "id": 1,
    "name": "技术讨论",
    "slug": "tech",
    "topic_count": 156,
    "reply_count": 892
  }
}
```

#### 获取主题回复

```
GET /api/topics/{id}/replies/
```

**权限**: AllowAny

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/topics/1/replies/" \
  -H "Accept: application/json"
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 回复 ID |
| content | string | 回复内容 |
| like_count | int | 点赞数 |
| created_at | datetime | 创建时间 |
| author | object | 作者信息 |

**响应示例**:

```json
{
  "count": 23,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "content": "我觉得新版本的路由系统很棒！",
      "like_count": 3,
      "created_at": "2024-01-10T15:00:00Z",
      "author": {
        "id": 3,
        "username": "coder",
        "avatar": "/media/avatars/coder.jpg",
        "bio": "",
        "website": ""
      }
    }
  ]
}
```

---

## 通知 API

> **注意**: 通知 API 需要用户认证。

### 获取通知列表

```
GET /api/notifications/
```

**权限**: IsAuthenticated

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/notifications/" \
  -H "Authorization: Token your-token-here" \
  -H "Accept: application/json"
```

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| is_read | bool | 按已读/未读筛选 |
| page | int | 页码 |
| page_size | int | 每页数量 |

**响应示例**:

```json
{
  "count": 25,
  "next": "/api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "新评论通知",
      "content": "用户 admin 评论了你的文章",
      "type": "comment",
      "link": "/blog/post/example-post/",
      "is_read": false,
      "created_at": "2026-04-06T10:00:00Z"
    }
  ]
}
```

### 获取未读通知数量

```
GET /api/notifications/unread_count/
```

**权限**: IsAuthenticated

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/notifications/unread_count/" \
  -H "Authorization: Token your-token-here" \
  -H "Accept: application/json"
```

**响应示例**:

```json
{
  "code": 200,
  "success": true,
  "data": {
    "count": 5
  }
}
```

### 标记单个通知为已读

```
POST /api/notifications/{id}/mark_read/
```

**权限**: IsAuthenticated

**curl 示例**:

```bash
curl -X POST "https://your-domain.com/api/notifications/1/mark_read/" \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json"
```

**响应示例**:

```json
{
  "code": 200,
  "success": true,
  "message": "已标记为已读"
}
```

### 标记所有通知为已读

```
POST /api/notifications/mark_all_read/
```

**权限**: IsAuthenticated

**curl 示例**:

```bash
curl -X POST "https://your-domain.com/api/notifications/mark_all_read/" \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json"
```

**响应示例**:

```json
{
  "code": 200,
  "success": true,
  "message": "已标记 5 条通知为已读"
}
```

### 清除已读通知

```
POST /api/notifications/clear_read/
```

**权限**: IsAuthenticated

**curl 示例**:

```bash
curl -X POST "https://your-domain.com/api/notifications/clear_read/" \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json"
```

**响应示例**:

```json
{
  "code": 200,
  "success": true,
  "message": "已清除 10 条通知"
}
```

### WebSocket 实时通知

**WebSocket 端点**: `ws://your-domain.com/ws/notifications/`

**连接示例**:

```javascript
const socket = new WebSocket('ws://your-domain.com/ws/notifications/');

socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('收到通知:', data);
};

socket.onopen = function() {
  console.log('WebSocket 连接已建立');
};

socket.onclose = function() {
  console.log('WebSocket 连接已关闭');
};
```

**消息格式**:

```json
{
  "type": "notification",
  "data": {
    "id": 1,
    "title": "新评论通知",
    "content": "用户 admin 评论了你的文章",
    "notification_type": "comment",
    "link": "/blog/post/example-post/",
    "created_at": "2026-04-06T10:00:00Z"
  }
}
```

---

## 工具 API

### 获取访问者 IP

```
GET /tools/my-ip/json/
```

**权限**: AllowAny

**说明**: 返回访问者的公网 IP 地址，供 NAT 工具前端使用。

**响应示例**:

```json
{
  "ok": true,
  "ip": "123.45.67.89"
}
```

---

## 上传 API

### 上传图片

```
POST /api/upload/image/
```

**权限**: IsAuthenticated

**限流**: 30次/小时

**请求格式**: `multipart/form-data`

**curl 示例**:

```bash
curl -X POST "https://your-domain.com/api/upload/image/" \
  -H "Authorization: Token your-token-here" \
  -F "file=@/path/to/image.jpg"
```

**参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 |

**文件限制**:

| 限制项 | 值 |
|--------|-----|
| 最大大小 | 5 MB |
| 允许类型 | JPEG, PNG, GIF, WebP |
| 安全检查 | 魔数验证 + ClamAV 扫描（可选） |

**成功响应** (200):

```json
{
  "location": "/media/uploads/images/2024/01/abc123.jpg"
}
```

**错误响应**:

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | UPLOAD_NO_FILE | 未提供文件 |
| 400 | UPLOAD_IMAGE_TOO_LARGE | 图片超过 5MB |
| 400 | UPLOAD_IMAGE_TYPE_NOT_ALLOWED | 不允许的图片类型 |
| 400 | UPLOAD_IMAGE_MAGIC_INVALID | 图片魔数验证失败（可能伪造扩展名） |
| 400 | UPLOAD_SECURITY_SCAN_REJECTED | 安全扫描未通过（病毒检测） |
| 401 | - | 未认证 |
| 500 | UPLOAD_SAVE_FAILED | 保存失败 |

---

### 上传文件

```
POST /api/upload/file/
```

**权限**: IsAuthenticated

**限流**: 30次/小时

**请求格式**: `multipart/form-data`

**curl 示例**:

```bash
# 同步上传
curl -X POST "https://your-domain.com/api/upload/file/" \
  -H "Authorization: Token your-token-here" \
  -F "file=@/path/to/document.pdf"
```

**参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 文件 |

**文件限制**:

| 限制项 | 值 |
|--------|-----|
| 最大大小 | 10 MB |
| 允许扩展名 | pdf, txt, md, csv, json, doc, docx, xls, xlsx, ppt, pptx, zip, 7z, rar, jpg, jpeg, png, gif, webp |
| 禁止扩展名 | exe, dll, bat, cmd, ps1, sh, php, jsp, asp, py, rb, jar 等 |
| 安全检查 | 危险魔数检测 + ClamAV 扫描 |

**同步上传响应** (200):

```json
{
  "location": "/media/uploads/files/2024/01/doc.pdf",
  "filename": "document.pdf",
  "size": 102400
}
```

**异步上传响应** (202):

当服务端启用异步管道（`UPLOAD_ASYNC_PIPELINE_ENABLED=True`）时：

```json
{
  "status": "pending",
  "upload_id": "abc123def456",
  "task_id": "celery-task-id",
  "status_path": "/api/upload/status/abc123def456/"
}
```

---

### 查询上传状态

```
GET /api/upload/status/{upload_id}/
```

**权限**: IsAuthenticated

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/upload/status/abc123def456/" \
  -H "Authorization: Token your-token-here"
```

**响应示例**:

```json
{
  "status": "completed",
  "upload_id": "abc123def456",
  "location": "/media/uploads/files/2024/01/doc.pdf"
}
```

**状态值**:

| 状态 | 说明 |
|------|------|
| pending | 等待处理 |
| scanning | 正在安全扫描 |
| completed | 上传完成 |
| failed | 上传失败（包含 `reason` 字段） |

**失败响应示例**:

```json
{
  "status": "failed",
  "upload_id": "abc123def456",
  "reason": "security_scan_rejected"
}
```

---

## 审核 API

> **注意**: 审核 API 仅限管理员（is_staff=True 或 is_superuser=True）使用。

### 获取审核指标

```
GET /api/moderation/metrics/
```

**权限**: IsAuthenticated (管理员)

**curl 示例**:

```bash
curl -X GET "https://your-domain.com/api/moderation/metrics/?minutes=10" \
  -H "Authorization: Token admin-token-here" \
  -H "Accept: application/json"
```

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| minutes | int | 10 | 统计窗口分钟数（1-120） |

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| success | bool | 请求是否成功 |
| window_minutes | int | 统计窗口 |
| totals | object | 指标汇总 |
| peak_concurrency | int | 峰值并发数 |
| series | array | 时间序列数据 |
| hotspots | array | 热点用户（请求量高的用户） |
| thresholds | object | 告警阈值配置 |

**响应示例**:

```json
{
  "success": true,
  "window_minutes": 10,
  "totals": {
    "requests_total": 1250,
    "approve_success": 320,
    "reject_success": 85,
    "rate_limited": 5,
    "concurrency_limited": 2,
    "approve_failed": 3,
    "reject_failed": 1,
    "permission_denied": 0,
    "invalid_content_type": 0,
    "content_not_found": 2
  },
  "peak_concurrency": 8,
  "series": [
    {
      "bucket": "202401151000",
      "requests_total": 120,
      "approve_success": 32,
      "reject_success": 8,
      "peak_concurrency": 5
    }
  ],
  "hotspots": [
    {
      "user_id": "5",
      "bucket": "202401151005",
      "count": 45
    }
  ],
  "thresholds": {
    "rate_limited": 5,
    "concurrency_limited": 3,
    "fail_rate": 0.2
  }
}
```

---

### 审核通过

```
POST /api/moderation/approve/{content_type}/{content_id}/
```

**权限**: IsAuthenticated (管理员)

**限流**: 120次/分钟，最大并发 20

**路径参数**:

| 参数 | 说明 | 可选值 |
|------|------|--------|
| content_type | 内容类型 | `comment`, `topic`, `reply` |
| content_id | 内容 ID | 整数 |

**curl 示例**:

```bash
# 通过评论
curl -X POST "https://your-domain.com/api/moderation/approve/comment/123/" \
  -H "Authorization: Token admin-token-here" \
  -H "Content-Type: application/json"

# 通过主题
curl -X POST "https://your-domain.com/api/moderation/approve/topic/456/" \
  -H "Authorization: Token admin-token-here" \
  -H "Content-Type: application/json"

# 通过回复
curl -X POST "https://your-domain.com/api/moderation/approve/reply/789/" \
  -H "Authorization: Token admin-token-here" \
  -H "Content-Type: application/json"
```

**成功响应** (200):

```json
{
  "success": true,
  "status": "approved",
  "id": 123
}
```

**错误响应**:

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | MODERATION_INVALID_CONTENT_TYPE | 无效的内容类型 |
| 403 | MODERATION_PERMISSION_DENIED | 权限不足（非管理员） |
| 404 | MODERATION_CONTENT_NOT_FOUND | 内容不存在 |
| 429 | MODERATION_API_RATE_LIMITED | 触发限流（120次/分钟） |
| 429 | MODERATION_API_CONCURRENCY_LIMITED | 触发并发限制（20并发） |
| 500 | MODERATION_APPROVE_FAILED | 审核失败 |

---

### 审核拒绝

```
POST /api/moderation/reject/{content_type}/{content_id}/
```

**权限**: IsAuthenticated (管理员)

**限流**: 120次/分钟，最大并发 20

**路径参数**:

| 参数 | 说明 | 可选值 |
|------|------|--------|
| content_type | 内容类型 | `comment`, `topic`, `reply` |
| content_id | 内容 ID | 整数 |

**curl 示例**:

```bash
# 拒绝评论（带备注）
curl -X POST "https://your-domain.com/api/moderation/reject/comment/123/" \
  -H "Authorization: Token admin-token-here" \
  -H "Content-Type: application/json" \
  -d '{"review_note": "内容违规，不予通过"}'

# 拒绝主题（无备注）
curl -X POST "https://your-domain.com/api/moderation/reject/topic/456/" \
  -H "Authorization: Token admin-token-here" \
  -H "Content-Type: application/json"
```

**请求体** (可选):

```json
{
  "review_note": "内容违规，不予通过"
}
```

**成功响应** (200):

```json
{
  "success": true,
  "status": "rejected",
  "id": 123
}
```

**错误响应**:

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | MODERATION_INVALID_CONTENT_TYPE | 无效的内容类型 |
| 403 | MODERATION_PERMISSION_DENIED | 权限不足（非管理员） |
| 404 | MODERATION_CONTENT_NOT_FOUND | 内容不存在 |
| 429 | MODERATION_API_RATE_LIMITED | 触发限流 |
| 429 | MODERATION_API_CONCURRENCY_LIMITED | 触发并发限制 |
| 500 | MODERATION_REJECT_FAILED | 审核拒绝失败 |

---

## 错误码参考

### 通用错误格式

```json
{
  "error_code": "ERROR_CODE",
  "error": "Error Title",
  "message": "Detailed error message"
}
```

### 上传错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| UPLOAD_NO_FILE | 400 | 未提供文件 |
| UPLOAD_IMAGE_TOO_LARGE | 400 | 图片超过 5MB |
| UPLOAD_FILE_TOO_LARGE | 400 | 文件超过 10MB |
| UPLOAD_IMAGE_TYPE_NOT_ALLOWED | 400 | 不允许的图片类型 |
| UPLOAD_FILE_TYPE_DENIED | 400 | 禁止的文件类型 |
| UPLOAD_FILE_EXT_NOT_ALLOWED | 400 | 不允许的文件扩展名 |
| UPLOAD_IMAGE_MAGIC_INVALID | 400 | 图片魔数验证失败 |
| UPLOAD_FILE_MAGIC_DENIED | 400 | 文件魔数检测到危险内容 |
| UPLOAD_SECURITY_SCAN_REJECTED | 400 | 安全扫描未通过 |
| UPLOAD_SAVE_FAILED | 500 | 保存失败 |
| UPLOAD_TASK_NOT_FOUND | 404 | 上传任务不存在 |

### 审核错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| MODERATION_PERMISSION_DENIED | 403 | 权限不足 |
| MODERATION_INVALID_CONTENT_TYPE | 400 | 无效的内容类型 |
| MODERATION_CONTENT_NOT_FOUND | 404 | 内容不存在 |
| MODERATION_API_RATE_LIMITED | 429 | 触发限流 |
| MODERATION_API_CONCURRENCY_LIMITED | 429 | 触发并发限制 |
| MODERATION_APPROVE_FAILED | 500 | 审核通过失败 |
| MODERATION_REJECT_FAILED | 500 | 审核拒绝失败 |

---

## 限流策略

### 全局限流

| 类型 | 限制 |
|------|------|
| 匿名用户 | 100 次/小时 |
| 认证用户 | 1000 次/小时 |
| 上传接口 | 30 次/小时 |
| API 读取 | 1200 次/小时 |

### 审核接口限流

| 限制类型 | 阈值 |
|----------|------|
| 速率限制 | 120 次/分钟 |
| 并发限制 | 20 个并发请求 |

### 限流响应

```json
{
  "error_code": "throttled",
  "error": "Request was throttled",
  "message": "Expected available in 60 seconds."
}
```

**响应头**:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067200
Retry-After: 60
```

---

## 在线文档

开发环境提供在线 API 文档：

| 文档类型 | 路径 |
|----------|------|
| Swagger UI | `/api/docs/` |
| ReDoc | `/api/redoc/` |
| OpenAPI Schema | `/api/schema/` |

**注意**: 在线文档仅在 `DEBUG=True` 时可用。

---

## 常见问题

### Q1: 如何获取 API Token？

**A**: 目前系统使用 Session 认证，登录后即可访问需要认证的接口。如需 Token 认证，可以：

1. 通过 Django Admin 创建 Token
2. 或调用 `/api-token-auth/` 接口（需配置）

### Q2: 为什么返回 401 Unauthorized？

**A**: 可能原因：
- 未登录或 Token 无效
- Token 格式错误（应为 `Authorization: Token xxx`）
- Session 过期

### Q3: 为什么上传文件返回 400 错误？

**A**: 常见原因：
- 文件大小超过限制（图片 5MB，文件 10MB）
- 文件类型不允许（检查扩展名是否在允许列表）
- 文件魔数验证失败（文件内容与扩展名不匹配）

### Q4: 如何调试 API 请求？

**A**: 
1. 使用浏览器访问 `/api/docs/` 查看 Swagger UI
2. 使用 `curl -v` 查看详细请求/响应
3. 检查响应头中的 `X-RateLimit-*` 信息

### Q5: 分页参数如何使用？

**A**: 
```
GET /api/posts/?page=2&page_size=50
```
- `page`: 页码，从 1 开始
- `page_size`: 每页数量，默认 20，最大 100

### Q6: 如何处理 429 限流错误？

**A**: 
- 检查响应头 `Retry-After` 获取重试时间
- 降低请求频率
- 对于批量操作，考虑增加请求间隔

### Q7: 搜索功能支持哪些字段？

**A**:
| 接口 | 搜索字段 |
|------|----------|
| /api/posts/ | title, content, summary |
| /api/topics/ | title, content |

### Q8: 时间格式是什么？

**A**: 所有时间使用 ISO 8601 格式（UTC）：
```
2024-01-15T10:00:00Z
```

---

## 变更日志

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2024-01-01 | 初始版本 |
| 1.1.0 | 2024-06-01 | 添加审核 API |
| 1.2.0 | 2024-12-01 | 添加异步上传支持 |
| 1.3.0 | 2026-04-02 | 完善文档，添加错误码参考 |
| 1.4.0 | 2026-04-06 | 添加通知 API、统一响应格式 |

---

*文档生成时间: 2026-04-06*
