# DjangoBlog 文档目录

本目录包含项目的详细文档。

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [deployment-manual.md](./deployment-manual.md) | Ubuntu / 宝塔手动部署教程（非 Docker） |
| [TECHNICAL_AUDIT_REPORT.md](../TECHNICAL_AUDIT_REPORT.md) | 技术评估报告（项目架构、代码质量、安全性分析） |

---

## 🚀 快速开始

Docker 部署请参考项目根目录 [README.md](../README.md)

---

## 📁 项目文档结构

```
DjangoBlog/
├── README.md                      # 项目主文档（Docker 部署指南）
├── TECHNICAL_AUDIT_REPORT.md      # 技术评估报告
├── docs/
│   ├── README.md                  # 本文件（文档索引）
│   └── deployment-manual.md       # 手动部署教程
├── scripts/
│   └── README.md                  # 脚本使用说明
└── deploy/
    ├── Dockerfile                 # Docker 镜像构建
    ├── docker-compose.yml         # Docker 服务编排
    ├── auto-deploy.sh             # 一键自动部署脚本
    └── nginx.conf                 # Nginx 配置
```

---

## 📝 最近更新（2026-04-01）

- **Docker 部署修复**
  - 新增 `auto-deploy.sh` 一键部署脚本
  - 修复 `SECURE_SSL_REDIRECT` 等安全配置默认值
  - 修复 Dockerfile collectstatic 权限问题
  - 添加阿里云 pip 镜像加速

- **文档整理**
  - 合并重复文档
  - 重命名文件使其更易理解
  - 更新 README.md 部署指南

---

## 🔗 相关链接

- [GitHub 仓库](https://github.com/zhang123999-qq/DjangoBlog)
- [Django 4.2 文档](https://docs.djangoproject.com/en/4.2/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
