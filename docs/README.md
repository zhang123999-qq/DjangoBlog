# DjangoBlog 文档目录

本目录包含项目的详细文档。

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [API.md](./API.md) | **API 接口文档**（25+ 接口，含通知 API、curl 示例、错误码、FAQ） |
| [deployment-manual.md](./deployment-manual.md) | Ubuntu / 宝塔手动部署教程（非 Docker） |
| [VERIFICATION_REPORT.md](./VERIFICATION_REPORT.md) | 验证报告（2026-04-06） |

### 根目录文档

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目主文档（快速开始、Docker 部署） |
| [CHANGELOG.md](../CHANGELOG.md) | 版本更新日志（含 2026-04-04 安全修复） |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 贡献指南 |
| [SECURITY.md](../SECURITY.md) | 安全策略与漏洞报告（含 2026-04-04 修复记录） |

---

## 🚀 快速开始

Docker 部署请参考 [README.md](../README.md)

---

## 📁 项目文档结构

```
DjangoBlog/
├── README.md                      # 项目主文档
├── CHANGELOG.md                   # 版本更新日志
├── CONTRIBUTING.md                # 贡献指南
├── SECURITY.md                    # 安全策略
├── docs/
│   ├── README.md                  # 本文件（文档索引）
│   ├── API.md                     # API 接口文档
│   ├── deployment-manual.md       # 手动部署教程
│   └── VERIFICATION_REPORT.md     # 验证报告
├── deploy/
│   ├── Dockerfile                 # Docker 镜像构建
│   ├── docker-compose.yml         # Docker 服务编排
│   ├── auto-deploy.sh             # 一键自动部署脚本
│   └── nginx.conf                 # Nginx 配置
└── requirements/
    ├── base.txt                   # 基础依赖
    ├── development.txt            # 开发依赖
    └── production.txt             # 生产依赖
```

---

## 📝 最近更新

### 2026-04-06 — v2.4.0

- **重大更新**：WebSocket 实时通知、全文搜索、统一 API 响应格式
- **代码质量**：pre-commit 钩子、185 项测试、CI/CD 流水线
- **文档更新**：README.md、CHANGELOG.md、API.md、CONTRIBUTING.md

### 2026-04-04 — v2.3.4

- **安全修复**：生产 Cookie 与 HTTPS 联动、验证码密码学安全、中文 Slug 修复、API 路由修复
- **测试提升**：89 passed / 0 failed（此前 83 / 6 failed）
- **文档更新**：CHANGELOG.md、SECURITY.md、README.md

### 2026-04-02 — v2.3.3

- **新增文档**：CHANGELOG.md、CONTRIBUTING.md、SECURITY.md、docs/API.md
- **文档优化**：更新文档索引结构

---

## 🔗 相关链接

- [GitHub 仓库](https://github.com/zhang123999-qq/DjangoBlog)
- [Django 4.2 文档](https://docs.djangoproject.com/en/4.2/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
