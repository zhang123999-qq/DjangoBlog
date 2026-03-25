# 异常处理分层收敛（阶段 16：审核保护指标查询接口）

覆盖文件：
- `apps/api/moderation_views.py`
- `apps/api/urls.py`

## 目标

提供可直接调用的管理员诊断接口，查看最近 N 分钟的审核保护指标，减少手工排查缓存 key 的成本。

## 新增接口

- `GET /api/moderation/metrics/?minutes=10`

权限要求：审核员（`is_staff` 或 `is_superuser`）

## 返回内容

- `window_minutes`：统计窗口
- `totals`：窗口内累计计数（请求量、限流命中、并发命中、成功/失败等）
- `peak_concurrency`：窗口内全局并发峰值
- `series`：分钟级时间序列
- `hotspots`：热点用户列表（如缓存后端支持 key 模式匹配）

## OpenAPI

- 已在 `moderation_views.py` 为该接口补充 `extend_schema` 参数与响应定义。

## 注意

- 热点用户依赖缓存后端支持 pattern keys；若不支持，`hotspots` 将为空数组，不影响主流程。