# DjangoBlog 文档目录

本目录包含项目的详细文档。

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [API.md](./API.md) | **API 接口文档**（21 个接口，含 curl 示例、错误码、FAQ） |
| [deployment-manual.md](./deployment-manual.md) | Ubuntu / 宝塔手动部署教程（非 Docker） |
| [PROJECT_EVALUATION.md](./PROJECT_EVALUATION.md) | 项目评估报告（代码质量、安全性分析） |

### 根目录文档

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目主文档（快速开始、Docker 部署） |
| [CHANGELOG.md](../CHANGELOG.md) | 版本更新日志 |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 贡献指南 |
| [SECURITY.md](../SECURITY.md) | 安全策略与漏洞报告 |
| [TECHNICAL_AUDIT_REPORT.md](../TECHNICAL_AUDIT_REPORT.md) | 技术评估报告 |

---

## 🚀 快速开始

Docker 部署请参考项目根目录 [README.md](../README.md)

---

## 📁 项目文档结构

```
DjangoBlog/
├── README.md                      # 项目主文档（Docker 部署指南）
├── CHANGELOG.md                   # 版本更新日志
├── CONTRIBUTING.md                # 贡献指南
├── SECURITY.md                    # 安全策略
├── TECHNICAL_AUDIT_REPORT.md      # 技术评估报告
├── docs/
│   ├── README.md                  # 本文件（文档索引）
│   ├── API.md                     # API 接口文档
│   ├── deployment-manual.md       # 手动部署教程
│   └── PROJECT_EVALUATION.md      # 项目评估报告
├── scripts/
│   └── README.md                  # 脚本使用说明
└── deploy/
    ├── Dockerfile                 # Docker 镜像构建
    ├── docker-compose.yml         # Docker 服务编排
    ├── auto-deploy.sh             # 一键自动部署脚本
    └── nginx.conf                 # Nginx 配置
```

---

## 📝 最近更新（2026-04-02）

- **新增文档**
  - `CHANGELOG.md` - 版本更新日志
  - `CONTRIBUTING.md` - 贡献指南
  - `SECURITY.md` - 安全策略与漏洞报告
  - `docs/API.md` - 完整 API 接口文档

- **文档优化**
  - 更新文档索引结构
  - 添加根目录文档链接

---

## 🔗 相关链接

- [GitHub 仓库](https://github.com/zhang123999-qq/DjangoBlog)
- [Django 4.2 文档](https://docs.djangoproject.com/en/4.2/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
