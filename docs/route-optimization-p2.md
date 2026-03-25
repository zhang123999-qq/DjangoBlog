# 路由性能优化 P2（组合索引）

本次 P2 目标：让高频路由查询命中复合索引，降低排序与过滤成本。

## 新增迁移

- `apps/forum/migrations/0004_topic_reply_route_composite_indexes.py`
- `apps/blog/migrations/0007_post_comment_route_composite_indexes.py`

## 新增索引

### Forum

1. `forum_topic_route_list_idx`
- 字段：`(board, review_status, -is_pinned, -last_reply_at, -created_at)`
- 覆盖路由：
  - `/forum/board/<slug:board_slug>/` 主题列表

2. `forum_topic_api_qs_idx`
- 字段：`(review_status, board, -created_at)`
- 覆盖路由：
  - `/api/topics/` 与 `board` 条件过滤

3. `forum_reply_route_idx`
- 字段：`(topic, review_status, is_deleted, created_at)`
- 覆盖路由：
  - `/forum/board/<slug>/topic/<id>/` 回复加载
  - `/api/topics/<id>/replies/`

### Blog

1. `blog_post_route_list_idx`
- 字段：`(status, -published_at, -created_at)`
- 覆盖路由：
  - `/blog/`
  - 首页文章块

2. `blog_post_cate_list_idx`
- 字段：`(status, category, -published_at)`
- 覆盖路由：
  - `/blog/category/<slug>/`

3. `blog_comment_route_idx`
- 字段：`(post, review_status, created_at)`
- 覆盖路由：
  - `/blog/post/<slug>/` 评论区
  - `/api/posts/<id>/comments/`

## 上线步骤

```bash
python manage.py migrate
```

## 验证建议

- 对高频路由执行前后压测（wrk/ab）
- 观察慢查询日志（MySQL `slow_query_log`）
- 对关键 SQL 执行 `EXPLAIN`，确认命中新索引

## 风险说明

- 新增索引会增加写入成本（插入/更新时维护索引）
- 但本项目读多写少，整体收益通常为正
