# DjangoBlog 项目笔记（工程总览）

> 最后更新：2026-03-25

## 1. 项目定位
- 类型：Django 4.2 博客 + 论坛 + 工具平台
- 目标：提供可上线、可运营、可扩展的内容社区系统
- 关键能力：内容发布、互动、审核、REST API、工具集成

## 2. 当前技术栈
- Python 3.10+
- Django 4.2 LTS
- Redis + Celery（异步任务/缓存）
- MySQL（生产建议）/ SQLite（开发默认）
- Sentry（可选）

## 3. 架构速览
- `apps/`：业务域（accounts/blog/forum/tools/api/core）
- `config/settings/`：base/development/production 分层配置
- `templates/ + static/`：前端模板与静态资源
- `tests/`：测试目录（含功能与安全相关测试）

## 4. 已确认亮点
- 工程结构较清晰，模块边界明确
- 安全意识较强：CSP、安全头、反爆破、速率限制思路
- 文档与配置样例较完整（`.env.example`）
- 有性能优化叙事（Redis 计数、查询优化等）

## 5. 风险与待改进（按优先级）
### P0（优先处理）
1. `DEBUG=True` 场景自动加入 `ALLOWED_HOSTS='*'` 的策略需更稳妥（避免误入高风险环境）
2. 生产安全默认值建议更保守（SSL 重定向、Secure Cookie、CSRF Cookie）
3. 补充 CI（Lint + Test + Security scan）

### P1（重要）
1. 配置与文档一致性核对（生产部署参数、环境变量说明）
2. 统一日志规范：关键行为、异常、审计字段（用户ID、IP、请求ID）
3. 将性能优化结论落到可复现基准脚本

### P2（优化）
1. 增加架构图（请求链路、任务链路）
2. 增加 API 使用示例与错误码手册

## 6. 运行/发布检查入口
- 部署前请先过：`docs/RELEASE_CHECKLIST.md`
- 安全基线参考：`docs/SECURITY_BASELINE.md`
- 关键决策记录：`docs/DECISIONS.md`

## 7. 下一步计划（建议）
- 一周内：先完成 P0（安全默认值 + CI）
- 两周内：补充性能基准与故障复盘模板
- 一个月内：完善 API/架构文档，形成可对外展示的工程案例
