# Changelog

All notable changes to this project will be documented in this file.

## [2.4.4] - 2026-03-21

### Fixed
- **数据库配置修复** - 修复 `KeyError: 'ATOMIC_REQUESTS'` 错误
  - `base.py` 中 `DATABASES` 设置为空字典导致错误
  - 添加默认 SQLite 数据库配置到 `base.py`
  - 确保即使环境配置未加载也有默认数据库

## [2.4.3] - 2026-03-21

### Fixed
- **安装向导修复** - 修复快速安装失败问题
  - 修复 `BASE_DIR` 字符串与 `/` 操作符不兼容问题
  - 将 `BASE_DIR` 从字符串改为 `Path` 对象
  - 添加 `pathlib` 导入

## [2.4.2] - 2026-03-21

### Fixed
- **NAT检测工具修复** - 修复检测失败问题
  - 修复 `fetch` 超时参数问题（使用 `AbortController`）
  - 添加更好的错误处理和提示
  - 优化本地IP检测逻辑
  - 添加公网IP获取失败的友好提示
  - 并行执行本地IP和公网IP检测
  - 添加控制台日志便于调试

## [2.4.1] - 2026-03-21

### Added
- **工具搜索框** - 快速搜索工具
  - 实时搜索工具名称和描述
  - 高亮匹配文字
  - 显示匹配结果数量
  - 支持快捷键：`/` 或 `Ctrl+F` 聚焦搜索框，`ESC` 清空
  - 无匹配结果时显示提示

## [2.4.0] - 2026-03-21

### Added
- **工具分类系统** - 72个工具按功能分类展示
  - 加密解密（8个）：AES、RSA、Base64、哈希、JWT等
  - 编码转换（14个）：URL、Unicode、进制、大小写、拼音等
  - 文本处理（9个）：统计、去重、对比、翻译等
  - 生成工具（11个）：UUID、密码、二维码、条形码等
  - 数据格式（7个）：JSON、CSV、HTML、Markdown等
  - 时间日期（3个）：时间戳、时差、番茄钟
  - 图片工具（5个）：压缩、格式转换、EXIF等
  - 网络工具（7个）：IP查询、端口扫描、NAT检测等
  - 安全工具（3个）：密码强度、身份证校验、邮箱验证
  - 计算工具（3个）：BMI、字节转换、随机数
  - 文件工具（2个）：文件哈希、格式转换
- **分类快捷导航** - 顶部显示分类按钮，点击跳转
- **分类颜色标识** - 每个分类有独特的颜色和图标

### Changed
- 工具列表页面重构，按分类展示工具
- 所有工具添加 `category` 属性
- 新增 `categories.py` 定义分类常量和配置

## [2.3.3] - 2026-03-21

### Added
- **NAT 检测工具** - 检测网络地址转换状态
  - 自动检测本地IP地址（多网卡支持）
  - 自动获取公网IP地址
  - 判断是否使用NAT
  - 推测NAT类型（锥形/受限/对称）
  - 完整的NAT知识介绍
  - 隐私保护：所有检测在浏览器本地完成

## [2.3.2] - 2026-03-21

### Added
- **"我的IP"工具** - 自动检测访问者公网IP地址
  - 自动获取访问者IP，无需手动输入
  - 显示地理位置（国家、地区、城市、邮编）
  - 显示网络信息（ISP、组织、ASN）
  - 显示坐标位置，支持地图查看
  - 国旗图标显示
  - 一键复制IP功能

## [2.3.1] - 2026-03-21

### Changed
- **统一UI风格** - 移除科技主题（tech-theme），全部使用浅色Bootstrap主题
- **.gitignore生成器优化** - 新增专用模板，左右分栏布局，支持复制/下载

### Removed
- 删除 `templates/base_tech.html` 及所有 `*_tech.html` 模板（14个文件）
- 删除 `static/css/tech-theme.css` 和 `static/js/tech-effects.js`

### Fixed
- 解决网站风格不一致问题

## [2.3.0] - 2026-03-21

### Added
- **富文本编辑器集成**
  - TinyMCE 7 编辑器
  - 图片上传（拖拽/粘贴）
  - 代码块高亮（15+语言）
  - 中文界面
- **Monaco Editor 集成**
  - VS Code同款代码编辑体验
  - 语法高亮、智能提示
  - 实时错误检测
  - 支持50+编程语言
- **文章管理功能**
  - 创建文章 `/blog/create/`
  - 编辑文章 `/blog/post/<slug>/edit/`
  - 删除文章
  - 我的文章列表 `/blog/my-posts/`
  - 草稿箱 `/blog/drafts/`
- **图片上传API**
  - `/api/upload/image/` 图片上传
  - `/api/upload/file/` 文件上传
  - 自动目录管理
- **10个新工具**
  1. 密码强度检测 - 检测密码等级，给出安全建议
  2. Markdown编辑器 - 实时预览，导出HTML
  3. 图片压缩 - 质量/尺寸调整
  4. HTML/Markdown互转 - 双向转换
  5. 文本去重 - 按行/词/字符去重
  6. 清除文本格式 - 一键得到纯文本
  7. .gitignore生成器 - 根据项目类型生成
  8. 摩斯密码编解码 - 文本与摩斯密码互转
  9. 字符画生成器 - ASCII艺术字（5种风格）
  10. 图片格式转换 - PNG/JPG/WEBP/GIF/BMP/TIFF互转

### Changed
- **管理后台风格统一** - 与前端网站保持一致的设计风格
- **安装向导优化** - 更清晰的步骤引导和进度指示
- **导航栏优化** - 新增"写文章"快捷入口
- 工具总数从60+增加到70+

### Fixed
- 字符画生成器语法错误
- .gitignore生成器转义序列警告

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
