# Django Blog

博客论坛系统，支持 85+ 在线工具。

## 快速开始

```bash
# 安装依赖
uv sync

# 启动服务器
uv run python manage.py runserver
```

## 目录结构

```
DjangoBlog/
├── apps/           # 应用模块
│   ├── accounts/   # 用户认证
│   ├── blog/       # 博客系统
│   ├── forum/      # 论坛系统
│   ├── tools/      # 在线工具
│   └── core/       # 核心功能
├── config/         # 配置文件
├── templates/      # 模板文件
├── static/         # 静态文件
├── scripts/        # 启动和管理脚本
├── deploy/         # 部署相关文件
├── docs/           # 项目文档
└── manage.py       # Django 管理脚本
```

## 访问地址

- 首页: http://localhost:8000/
- 博客: http://localhost:8000/blog/
- 论坛: http://localhost:8000/forum/
- 工具: http://localhost:8000/tools/
- 后台: http://localhost:8000/admin/

## 文档

详细文档请查看 [docs/](docs/) 目录。
