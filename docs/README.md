# DjangoBlog 文档索引

本文档提供 DjangoBlog 项目的所有文档链接和说明。

---

## 📚 核心文档

| 文档 | 说明 | 状态 |
|------|------|------|
| [README.md](../README.md) | 项目介绍、快速开始、技术栈 | ✅ 最新 |
| [CHANGELOG.md](../CHANGELOG.md) | 版本更新日志 | ✅ 最新 |
| [SECURITY.md](../SECURITY.md) | 安全策略、漏洞报告流程 | ✅ 最新 |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 贡献指南、开发规范 | ✅ 最新 |

---

## 📊 审计与质量

| 文档 | 说明 | 日期 |
|------|------|------|
| [PROJECT_AUDIT_2026.md](PROJECT_AUDIT_2026.md) | 综合审计报告（安全、质量、功能） | 2026-04-15 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署指南、生产环境配置 | 2026-04-28 |

---

## 🛠️ 模块文档

| 模块 | 文档 | 说明 |
|------|------|------|
| 用户系统 | [模块01-用户系统.md](模块01-用户系统.md) | 注册、登录、权限、个人资料 |
| 博客核心 | [模块02-博客核心.md](模块02-博客核心.md) | 文章、分类、标签、Slug |
| 评论系统 | [模块03-评论系统.md](模块03-评论系统.md) | 评论、点赞、审核 |
| 搜索与首页 | [模块04-搜索与首页.md](模块04-搜索与首页.md) | 全文搜索、首页展示 |
| 社区论坛 | [模块05-社区论坛.md](模块05-社区论坛.md) | 主题、回复、版块 |
| 在线工具箱 | [模块06-在线工具箱.md](模块06-在线工具箱.md) | 72 个实用工具 |
| 内容审核 | [模块07-内容审核.md](模块07-内容审核.md) | AI 审核、敏感词过滤 |
| REST API | [模块08-REST-API接口.md](模块08-REST-API接口.md) | API 端点、认证、文档 |
| 文件上传 | [模块09-文件上传.md](模块09-文件上传.md) | 上传、验证、存储 |
| 安全与性能 | [模块10-安全与性能.md](模块10-安全与性能.md) | 安全措施、性能优化 |
| 后台管理 | [模块11-后台管理.md](模块11-后台管理.md) | Django Admin 配置 |
| 部署运维 | [模块12-部署运维.md](模块12-部署运维.md) | Docker、Nginx、监控 |

---

## 🔗 外部链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/zhang123999-qq/DjangoBlog |
| API 文档 (Swagger) | /api/docs/ |
| API 文档 (ReDoc) | /api/redoc/ |
| 健康检查 | /healthz/ |

---

## 📖 文档规范

### 文档结构
```
docs/
├── README.md                    # 本文件
├── PROJECT_AUDIT_2026.md        # 综合审计报告
├── DEPLOYMENT.md                # 部署指南
├── API.md                       # API 文档
├── 模块01-用户系统.md            # 模块文档
├── 模块02-博客核心.md
└── ...
```

### 文档更新
- **核心文档**: 随版本更新
- **模块文档**: 随功能更新
- **审计报告**: 定期更新（建议每季度）

### 文档贡献
1. 遵循 [贡献指南](../CONTRIBUTING.md)
2. 使用中文撰写
3. 保持格式一致
4. 及时更新过时内容

---

## 🆘 获取帮助

- **问题反馈**: [GitHub Issues](https://github.com/zhang123999-qq/DjangoBlog/issues)
- **安全漏洞**: 参考 [SECURITY.md](../SECURITY.md)
- **功能建议**: [GitHub Discussions](https://github.com/zhang123999-qq/DjangoBlog/discussions)

---

**文档索引版本:** 1.0  
**最后更新:** 2026年4月28日
**维护者:** DjangoBlog 团队
