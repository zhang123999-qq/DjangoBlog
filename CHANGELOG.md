# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0] - 2026-03-21

### Added
- **Celery 异步队列**
  - 异步任务处理
  - 定时任务调度
  - Flower 监控界面
- **用户信誉系统**
  - 信誉积分（0-100）
  - 三级信誉等级（高信誉/正常/低信誉）
  - 自动信誉分调整
  - 连续无违规天数统计
- **AI 内容审核**
  - 百度内容审核 API 集成
  - 文本审核（色情、暴恐、政治敏感、广告、辱骂）
  - 图片审核
  - 模拟审核服务（开发环境）
- **多级审核策略**
  - 高信誉用户自动发布
  - 低信誉用户强制人工审核
  - 普通用户敏感词 + AI 双重检测
- **异步审核任务**
  - 异步文本审核
  - 异步图片审核
  - 定时检查待审核内容
  - 自动通过超时无敏感词内容
- **启动脚本**
  - Windows: `start_celery.bat`
  - Linux/macOS: `start_celery.sh`

### Changed
- 开发环境使用 Redis 缓存
- 配置文件添加 Celery 相关设置
- 更新依赖（celery、redis、baidu-aip、flower）
- 更新 README 添加审核系统说明
- 更新 .env.example 添加新配置项

### Dependencies Added
- celery 5.4+
- redis 5.2+
- baidu-aip 4.16+
- flower 2.0+

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
