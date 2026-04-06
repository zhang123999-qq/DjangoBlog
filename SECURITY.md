# 安全策略

本文档描述 DjangoBlog 项目的安全策略和漏洞报告流程。

---

## 目录

- [支持的版本](#支持的版本)
- [安全特性](#安全特性)
- [报告漏洞](#报告漏洞)
- [安全最佳实践](#安全最佳实践)

---

## 支持的版本

我们为以下版本提供安全更新：

| 版本 | 支持状态 |
|------|----------|
| 2.3.x | ✅ 支持 |
| 2.2.x | ⚠️ 仅安全修复 |
| < 2.2 | ❌ 不再支持 |

建议所有用户升级到最新版本以获得完整的安全保障。

---

## 安全特性

### 已实现的安全措施

#### 1. 认证与授权

- **用户认证**：Django 内置认证系统
- **密码安全**：使用 PBKDF2 + SHA256 密码哈希
- **登录保护**：django-axes 防暴力破解
#### Session 安全（v2.3.4 修复）
- **Cookie 安全联动**：`SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` 与 HTTPS 状态联动
  - 纯 HTTP 部署 → 自动 False，登录/CSRF 正常工作
  - HTTPS 部署 → 自动 True，防御中间人攻击
- **HSTS 联动**：`SECURE_HSTS_SECONDS` 与 HTTPS 联动，非 HTTPS 时默认 0

#### 2. 跨站防护

- **CSRF 保护**：所有 POST 表单验证 CSRF Token
- **XSS 防护**：模板自动转义、Content-Security-Policy
- **Clickjacking 防护**：X-Frame-Options: DENY

#### 3. 安全响应头

| 响应头 | 值 | 说明 |
|--------|-----|------|
| X-Content-Type-Options | nosniff | 防止 MIME 类型嗅探 |
| X-Frame-Options | DENY | 防止点击劫持 |
| X-XSS-Protection | 1; mode=block | XSS 过滤器 |
| Referrer-Policy | strict-origin-when-cross-origin | 引用策略 |
| Content-Security-Policy | 配置化 | 内容安全策略 |

#### 4. 文件上传安全

- **文件类型限制**：仅允许指定扩展名
- **大小限制**：图片 5MB，文件 10MB
- **魔数验证**：检测文件真实类型
- **病毒扫描**：ClamAV 集成（可选）
- **危险文件拦截**：exe、php、jsp 等禁止上传

#### 5. API 安全

- **限流保护**：匿名 100/h，认证 1000/h
- **并发限制**：审核 API 120/min，20 并发
- **权限控制**：管理员接口需要 is_staff 权限

#### 6. 数据库安全

- **SQL 注入防护**：ORM 参数化查询
- **敏感数据加密**：SECRET_KEY 用于签名
- **连接安全**：建议使用 SSL 连接数据库

#### 7. 内容审核

- **审核模式**：支持自动/手动/混合模式
- **敏感词过滤**：可选百度内容审核 API
- **垃圾内容防护**：审核 API 限流保护

#### 8. 日志安全（v2.4.0 新增）

- **敏感数据过滤**：日志自动脱敏密码、令牌、API 密钥
- **过滤规则**：
  - 密码字段：`password`, `password1`, `password2` → `***FILTERED***`
  - 令牌字段：`token`, `access_token`, `refresh_token`, `api_key`, `secret_key` → `***FILTERED***`
  - 支持自定义过滤规则

---

## 报告漏洞

### 如何报告

如果你发现了安全漏洞，请**不要**通过公开 Issue 报告。

请通过以下方式私下报告：

1. **GitHub Security Advisories**（推荐）
   - 访问：https://github.com/zhang123999-qq/DjangoBlog/security/advisories
   - 点击 "Report a vulnerability"
   - 填写漏洞详情

2. **邮件联系**
   - 发送邮件到项目维护者
   - 标题以 `[SECURITY]` 开头

### 报告内容

请包含以下信息：

- 漏洞类型（XSS、SQL注入、CSRF 等）
- 受影响的版本和组件
- 复现步骤
- 概念验证代码（如有）
- 可能的影响范围

### 响应时间

| 阶段 | 时间 |
|------|------|
| 确认收到报告 | 48 小时内 |
| 初步评估 | 7 天内 |
| 修复发布 | 根据严重程度 14-30 天 |

### 披露政策

- 我们遵循**负责任披露**原则
- 漏洞修复并发布后，会公开致谢（如果你愿意）
- 我们会申请 CVE 编号（如适用）

---

## 安全最佳实践

### 部署建议

#### 1. 环境配置

```env
# 生产环境必须设置
DEBUG=False
SECRET_KEY=<强随机字符串，至少50字符>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 启用安全配置（有 SSL 时）
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# HSTS（可选，推荐）
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
```

#### 2. 数据库安全

- 使用专用数据库用户，限制权限
- 不要使用 root 用户连接数据库
- 定期备份数据库
- 考虑使用 SSL 连接

#### 3. Redis 安全

- 不要将 Redis 暴露到公网
- 设置 Redis 密码
- 使用专用数据库编号

#### 4. Nginx 配置

```nginx
# 隐藏版本号
server_tokens off;

# 安全响应头
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";

# 限制上传大小
client_max_body_size 10M;

# SSL 配置（推荐）
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
```

#### 5. 定期维护

- 定期更新依赖包：`pip install --upgrade -r requirements/production.txt`
- 关注 Django 安全公告：https://www.djangoproject.com/security/
- 定期检查服务器日志
- 设置日志监控告警

---

## 已修复的安全问题

### 2026-04-04 — v2.3.4 安全修复

| ID | 问题 | 严重度 | 修复方案 |
|----|------|--------|---------|
| SEC-20260404-001 | 纯 HTTP 部署时登录/CSRF 完全失效 | 🔴 P0 | `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` 与 HTTPS 联动 |
| SEC-20260404-002 | 验证码随机数可预测（4位，仅1万种组合） | 🔴 P0 | `random` → `secrets`，4位 → 6位（100万种组合） |
| SEC-20260404-003 | 中文标题/分类 slug 为空，URL 路由 404 | 🟡 P1 | `slugify()` → `generate_slug()`（SHA-256 fallback） |
| SEC-20260404-004 | nginx 缺少安全响应头 | 🟡 P2 | 补充 X-Frame/XSS/CSP/Permissions-Policy |

### 2026-04-02 — v2.3.3 安全修复

- `SecurityMiddleware` 命名冲突修复（→ `SecurityMonitorMiddleware`）
- Docker 部署 `SECURE_SSL_REDIRECT` 等默认值修正
- SSRF 内网 IP 检测、端口扫描范围限制

---

## 安全检查清单

部署前请确认：

- [ ] `DEBUG=False` 已设置
- [ ] `SECRET_KEY` 已更改为强随机值（至少 64 字节）
- [ ] `ALLOWED_HOSTS` 已正确配置
- [ ] `USE_X_FORWARDED_PROTO=True`（有反代时）
- [ ] 数据库不使用 root 用户
- [ ] Redis 不暴露到公网
- [ ] 上传目录不可执行
- [ ] 静态文件正确配置
- [ ] HTTPS 已启用（推荐）
- [ ] 安全响应头已配置（Nginx + Django 双重防护）
- [ ] `python manage.py migrate` 已执行
- [ ] 部署日志监控已配置

---

## 致谢

感谢以下研究人员对 DjangoBlog 安全的贡献：

<!-- 安全贡献者将在此列出 -->

---

*最后更新: 2026-04-06*
