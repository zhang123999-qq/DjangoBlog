# DjangoBlog 环境配置分离 - 使用说明

## 第一阶段完成！✅

### 已完成的配置

```
config/settings/
├── __init__.py          # 自动选择配置
├── base.py              # 基础配置（已简化）
├── development.py       # 开发环境（SQLite）✅
└── production.py        # 生产环境（MySQL + Redis）✅
```

### 开发环境（SQLite）

**特点：**
- 数据库：SQLite（零配置）
- 缓存：DummyCache（不缓存）
- 会话：文件存储
- 邮件：控制台输出
- 调试：开启

**使用方法：**
```bash
# 方式1：自动检测（默认）
python manage.py runserver

# 方式2：显式指定
set DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py runserver
```

**测试成功：**
```
[SETTINGS] 使用开发环境配置 (SQLite)
System check identified no issues.
Starting development server at http://127.0.0.1:8000/
```

### 生产环境（MySQL + Redis）

**特点：**
- 数据库：MySQL 8.0
- 缓存：Redis 7.x
- 会话：Redis
- 邮件：SMTP
- 调试：关闭
- 安全：HTTPS强制

**环境变量配置 (.env)：**
```bash
# 必须配置
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# MySQL
DB_NAME=djangoblog
DB_USER=djangoblog_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# 邮件（可选）
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**使用方法：**
```bash
# 方式1：设置环境变量
set DJANGO_SETTINGS_MODULE=config.settings.production
set DEBUG=False
python manage.py runserver

# 方式2：使用 .env 文件
# 确保 .env 文件中 DEBUG=False
python manage.py runserver --settings=config.settings.production
```

### 下一步（第二阶段）

1. **安装 MySQL**
   ```bash
   # Ubuntu
   sudo apt install mysql-server-8.0
   
   # Windows
   # 下载安装包：https://dev.mysql.com/downloads/installer/
   ```

2. **安装 Redis**
   ```bash
   # Ubuntu
   sudo apt install redis-server
   
   # Windows
   # 使用 WSL2 或下载 Redis for Windows
   ```

3. **安装 Python 依赖**
   ```bash
   pip install mysqlclient
   pip install django-redis
   ```

4. **配置环境变量**
   - 复制 .env.example 为 .env
   - 填写数据库和Redis配置

5. **数据库迁移**
   ```bash
   python manage.py migrate --settings=config.settings.production
   ```

### 备份信息

原始项目已备份：
```
F:\PythonProject\DjangoBlog-backup-20260319.zip (13.5 MB)
```

### 修改的文件

1. `config/settings/base.py` - 简化基础配置
2. `config/settings/development.py` - 新建开发配置 ✅
3. `config/settings/production.py` - 新建生产配置 ✅
4. `config/settings/__init__.py` - 自动选择配置 ✅
5. `manage.py` - 自动检测环境 ✅

---

**第一阶段完成时间：** 2026-03-19 19:18
**状态：** ✅ 开发环境配置测试通过
