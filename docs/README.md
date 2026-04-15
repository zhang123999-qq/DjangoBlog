# DjangoBlog 文档目录

本目录包含项目的详细文档和模块说明。

---

## 📚 核心文档

| 文档 | 说明 |
|------|------|
| [API.md](./API.md) | **API 接口文档**（25+ 接口，含通知 API、curl 示例、错误码、FAQ） |
| [deployment-manual.md](./deployment-manual.md) | Ubuntu / 宝塔手动部署教程（非 Docker） |
| [目录总览-项目架构与模块索引.md](./目录总览-项目架构与模块索引.md) | 项目架构与模块索引 |

---

## 📦 模块文档

| 模块 | 文档 | 说明 |
|------|------|------|
| 01 | [用户系统](./模块01-用户系统.md) | 用户认证、注册、登录、权限管理 |
| 02 | [博客核心](./模块02-博客核心.md) | 文章发布、分类、标签、评论 |
| 03 | [评论系统](./模块03-评论系统.md) | 评论功能、审核、回复 |
| 04 | [搜索与首页](./模块04-搜索与首页.md) | 全文搜索、首页展示 |
| 05 | [社区论坛](./模块05-社区论坛.md) | 论坛板块、主题、回复 |
| 06 | [在线工具箱](./模块06-在线工具箱.md) | 85+ 在线工具 |
| 07 | [内容审核](./模块07-内容审核.md) | 百度AI审核、敏感词过滤 |
| 08 | [REST API接口](./模块08-REST-API接口.md) | RESTful API 设计 |
| 09 | [文件上传](./模块09-文件上传.md) | 图片、文件上传处理 |
| 10 | [安全与性能](./模块10-安全与性能.md) | 安全防护、性能优化 |
| 11 | [后台管理](./模块11-后台管理.md) | Django Admin 定制 |
| 12 | [部署运维](./模块12-部署运维.md) | 部署配置、运维指南 |

---

## 📁 根目录文档

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目主文档（快速开始、Docker 部署） |
| [CHANGELOG.md](../CHANGELOG.md) | 版本更新日志 |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 贡献指南 |
| [SECURITY.md](../SECURITY.md) | 安全策略与漏洞报告 |

---

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 安装依赖
pip install -r requirements/base.txt

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动服务
python manage.py runserver
```

Docker 部署请参考 [README.md](../README.md)

---

## 🔗 相关链接

- [GitHub 仓库](https://github.com/zhang123999-qq/DjangoBlog)
- [Django 4.2 文档](https://docs.djangoproject.com/en/4.2/)
- [Docker Compose 文档](https://docs.docker.com/compose/)

---

*最后更新: 2026-04-15*
