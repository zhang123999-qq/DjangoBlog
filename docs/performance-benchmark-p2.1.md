# P2.1 压测与索引效果验证模板

目标：量化 P2 组合索引上线前后的收益，避免“感觉变快”。

---

## 1. 测试前提

- 环境一致（同一台机器、同一配置）
- 关闭非必要后台任务
- 测试数据量尽量接近生产
- 每组至少跑 3 次取中位数

建议记录：
- TTFB / 平均响应 / P95 / P99
- RPS（Requests/sec）
- 错误率（非 2xx）
- MySQL 慢查询数量

---

## 2. 基准路由（建议）

### 页面路由
- `/`
- `/blog/`
- `/blog/category/<slug>/`
- `/forum/board/<board_slug>/`
- `/forum/board/<board_slug>/topic/<topic_id>/`

### API 路由
- `/api/posts/`
- `/api/posts/<id>/comments/`
- `/api/topics/`
- `/api/topics/<id>/replies/`

---

## 3. 压测命令（wrk）

> 安装：`wrk`（Linux/macOS）

### 3.1 基础压测
```bash
wrk -t4 -c100 -d30s --latency http://127.0.0.1:8000/blog/
wrk -t4 -c100 -d30s --latency http://127.0.0.1:8000/forum/board/general/
wrk -t4 -c100 -d30s --latency http://127.0.0.1:8000/api/topics/
```

### 3.2 冷缓存 / 热缓存
```bash
# 冷缓存：重启服务后首轮
wrk -t4 -c80 -d20s --latency http://127.0.0.1:8000/

# 热缓存：连续再跑 2 轮
wrk -t4 -c80 -d20s --latency http://127.0.0.1:8000/
wrk -t4 -c80 -d20s --latency http://127.0.0.1:8000/
```

---

## 4. 压测命令（ab，可选）

```bash
ab -n 5000 -c 100 http://127.0.0.1:8000/blog/
ab -n 5000 -c 100 http://127.0.0.1:8000/api/topics/
```

---

## 5. MySQL EXPLAIN 验证（关键）

在 MySQL 执行：

```sql
-- Forum 列表
EXPLAIN SELECT id, title, is_pinned, last_reply_at, created_at
FROM forum_topic
WHERE board_id = ? AND review_status = 'approved'
ORDER BY is_pinned DESC, last_reply_at DESC, created_at DESC
LIMIT 20;

-- Topic 回复
EXPLAIN SELECT id, topic_id, created_at
FROM forum_reply
WHERE topic_id = ? AND review_status = 'approved' AND is_deleted = 0
ORDER BY created_at ASC;

-- Blog 列表
EXPLAIN SELECT id, title, published_at
FROM blog_post
WHERE status = 'published'
ORDER BY published_at DESC, created_at DESC
LIMIT 10;

-- Blog 分类页
EXPLAIN SELECT id, title, published_at
FROM blog_post
WHERE status = 'published' AND category_id = ?
ORDER BY published_at DESC
LIMIT 10;

-- Post 评论
EXPLAIN SELECT id, post_id, created_at
FROM blog_comment
WHERE post_id = ? AND review_status = 'approved'
ORDER BY created_at ASC;
```

关注点：
- `key` 是否命中新索引
- `rows` 是否显著下降
- `Extra` 是否减少 `Using filesort` / `Using temporary`

---

## 6. 结果记录表（复制填写）

| 路由 | 指标 | 迁移前 | 迁移后 | 变化 |
|---|---:|---:|---:|---:|
| /blog/ | RPS |  |  |  |
| /blog/ | P95(ms) |  |  |  |
| /forum/board/{slug}/ | RPS |  |  |  |
| /forum/board/{slug}/ | P95(ms) |  |  |  |
| /api/topics/ | RPS |  |  |  |
| /api/topics/ | P95(ms) |  |  |  |
| /api/topics/{id}/replies/ | RPS |  |  |  |
| /api/topics/{id}/replies/ | P95(ms) |  |  |  |

---

## 7. 建议阈值（参考）

- RPS 提升 >= 15%：有效
- P95 下降 >= 20%：显著有效
- 慢查询（>1s）下降 >= 30%：数据库侧明显优化

---

## 8. 回归检查

完成迁移后务必验证：
- 功能正确性（分页、排序、过滤）
- 写入性能无明显异常（索引增加会轻微影响写入）
- 错误日志无新增异常
