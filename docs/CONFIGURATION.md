# 环境配置指南

本文档说明如何配置 DjangoBlog 的环境变量。

## 快速开始

1. 复制示例配置文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，修改必要的配置项

3. 运行安装脚本：
   ```bash
   ./install.sh        # Linux/Mac
   install.bat         # Windows
   ```

## 安装方式

### 使用 pyproject.toml（推荐）

```bash
# 标准安装
pip install -e .

# 开发模式（包含测试工具）
pip install -e ".[dev]"
```

### 使用 requirements.txt

```bash
# 生产环境
pip install -r requirements/production.txt

# 开发环境
pip install -r requirements/development.txt
```

## 核心配置

### SECRET_KEY（必需）

Django 的安全密钥，用于加密签名。

```bash
# 生成随机密钥
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### DEBUG（必需）

调试模式开关。

- `True` - 开发环境
- `False` - 生产环境

### ALLOWED_HOSTS

允许访问的主机名列表，逗号分隔。

```bash
# 开发环境
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# 生产环境
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,example.com,www.example.com
```

**默认值已包含：**
- `localhost` - 本地访问
- `127.0.0.1` - 本地IP
- `0.0.0.0` - 允许外部访问（开发环境常用）

## 数据库配置

### 方式1: 使用 DATABASE_URL（推荐）

```bash
# SQLite（默认）
DATABASE_URL=sqlite:///db.sqlite3

# MySQL
DATABASE_URL=mysql://user:password@localhost:3306/dbname

# PostgreSQL
DATABASE_URL=postgres://user:password@localhost:5432/dbname
```

### 方式2: 分项配置

```bash
# 数据库类型
DB_ENGINE=mysql           # sqlite, mysql, postgresql

# MySQL/PostgreSQL 参数
DB_NAME=djangoblog
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

## Redis 配置（可选）

启用 Redis 可以提升性能，用于缓存和会话存储。

```bash
USE_REDIS=True
REDIS_URL=redis://localhost:6379/0
```

## 邮件配置（可选）

用于发送通知邮件。

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

## 安全配置

生产环境建议启用以下配置：

```bash
DEBUG=False
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

## 完整示例

### 开发环境

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DB_ENGINE=sqlite
ENABLE_INSTALLER=True
```

### 生产环境

```bash
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,yourdomain.com
DATABASE_URL=mysql://user:password@localhost:3306/djangoblog
USE_REDIS=True
REDIS_URL=redis://localhost:6379/0
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
ENABLE_INSTALLER=False
```

## 注意事项

1. **不要提交 `.env` 文件到版本控制**
   - `.env` 已在 `.gitignore` 中排除
   - 只提交 `.env.example` 作为示例

2. **生产环境必须修改 SECRET_KEY**
   - 使用随机生成的强密钥
   - 不要使用默认值或简单密码

3. **ALLOWED_HOSTS 必须包含实际域名**
   - 否则 Django 会拒绝请求
   - 已默认包含 `0.0.0.0` 方便开发调试
