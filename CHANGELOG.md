# Changelog

All notable changes to this project will be documented in this file.

## [2.1.0] - 2026-03-15

### Changed
- **升级 Python 版本要求到 3.13+**
- 更新所有依赖到最新兼容版本
- 添加 .python-version 文件
- **安装方式改用 pyproject.toml**
  - `pip install -e .` - 标准安装
  - `pip install -e ".[dev]"` - 开发模式

### Dependencies Updated
- Django 4.2.20
- django-axes 7.0.2
- Pillow 11.1.0
- redis 5.2.1
- requests 2.32.3
- pytest 8.3.5
- black 25.1.0
- gunicorn 23.0.0
- uvicorn 0.34.0

### Fixed
- Windows colorama OSError in logging

## [2.0.0] - 2026-03-15

### Added
- 安装向导系统（快速安装/向导安装两种模式）
- 14个实用工具
  - AES加密解密
  - Base64编解码
  - 进制转换（二/八/十/十六进制）
  - 颜色转换（HEX/RGB/HSL）
  - 哈希计算（MD5/SHA系列）
  - JSON格式化
  - JWT解码生成
  - 密码生成器
  - 二维码生成
  - 正则表达式测试
  - 文本统计
  - 时间戳转换
  - Unicode编码解码
  - URL编码解码
- 自动化测试套件（Playwright + pytest）
- Docker部署支持
- GitHub Actions CI/CD配置

### Changed
- 优化安装向导UI/UX
- 重构工具栏架构（模块化设计）
- 优化敏感词检测（添加缓存）
- 修复浏览量并发问题（使用F()表达式）
- 优化Profile信号处理器

### Fixed
- CommentForm字段删除KeyError
- Profile信号处理器缺失更新逻辑
- 数据库迁移文件兼容性

## [1.0.0] - 2026-03-12

### Added
- 博客系统（文章、分类、标签、评论）
- 论坛系统（版块、主题、回复、点赞）
- 用户系统（注册、登录、个人资料）
- 管理后台
- 响应式设计
