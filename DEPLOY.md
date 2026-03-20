# DjangoBlog 部署指南

DjangoBlog 是一个基于 Django 4.2 LTS 的全功能博客与论坛系统。本文档提供详细的部署教程。

---

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [Docker 部署（推荐）](#docker-部署推荐)
- [手动部署](#手动部署)
- [生产环境部署](#生产环境部署)
- [常见问题](#常见问题)

---

## 环境要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.13 | 3.13 |
| Django | 4.2 LTS | 4.2.x |
| MySQL | 8.0 | 8.0 |
| Redis | 5.0 | 7.x |

---

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 2. 启动服务
docker-compose up -d

# 3. 访问
# 网站: http://localhost
# 管理后台: http://localhost/admin
```

### 方式二：pip 安装

```bash
# 1. 安装
pip install djangoblog

# 2. 创建项目
django-admin startproject myblog
cd myblog

# 3. 添加应用到 settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djangoblog', 'djangoblog.blog', 'djangoblog.forum',
    'djangoblog.accounts', 'djangoblog.tools', 'djangoblog.moderation',
    'djangoblog.core', 'djangoblog.install', 'djangoblog.api',
]

# 4. 配置 URL
# urls.py
from django.urls import path, include
urlpatterns = [
    path('', include('djangoblog.core.urls')),
    path('blog/', include('djangoblog.blog.urls')),
    path('forum/', include('djangoblog.forum.urls')),
    path('accounts/', include('djangoblog.accounts.urls')),
    path('tools/', include('djangoblog.tools.urls')),
    path('install/', include('djangoblog.install.urls')),
    path('api/', include('djangoblog.api.urls')),
    path('moderation/', include('djangoblog.moderation.urls')),
    path('admin/', admin.site.urls),
]

# 5. 运行
python manage.py migrate
python manage.py runserver
```

---

## Docker 部署（推荐）

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 步骤

```bash
# 1. 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 2. 创建环境配置
cp .env.example .env
# 编辑 .env 文件配置数据库密码等

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f
```

### 配置 .env 文件

```env
# 必填项
DJANGO_SECRET_KEY=your-secret-key-here
DB_PASSWORD=your_database_password

# 可选配置
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_ENGINE=django.db.backends.mysql
DB_HOST=db
DB_NAME=djangoblog
DB_USER=root
DB_PORT=3306
```

### Docker 命令

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f web

# 进入容器
docker-compose exec web bash
```

---

## 手动部署

### 方式一：Windows

```powershell
# 1. 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 2. 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements\production.txt

# 4. 配置环境
copy .env.example .env
# 编辑 .env 文件

# 5. 初始化数据库
python manage.py migrate
python manage.py init_default_data

# 6. 创建管理员
python manage.py createsuperuser

# 7. 收集静态文件
python manage.py collectstatic --noinput

# 8. 启动服务
python manage.py runserver
```

### 方式二：Linux/Mac

```bash
# 1. 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

# 2. 创建虚拟环境
python3.13 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements/production.txt

# 4. 配置环境
cp .env.example .env
# 编辑 .env 文件

# 5. 初始化数据库
python manage.py migrate
python manage.py init_default_data

# 6. 创建管理员
python manage.py createsuperuser

# 7. 收集静态文件
python manage.py collectstatic --noinput

# 8. 启动服务（开发）
python manage.py runserver

# 或者使用 Gunicorn（生产）
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

---

## 生产环境部署

### 1. 服务器准备

```bash
# Ubuntu 22.04
apt update && apt upgrade -y

# 安装 Python 3.13
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa -y
apt install python3.13 python3.13-venv python3.13-dev -y

# 安装 MySQL
apt install mysql-server -y

# 安装 Nginx
apt install nginx -y

# 安装 Git
apt install git -y
```

### 2. MySQL 配置

```bash
# 启动 MySQL
systemctl start mysql
systemctl enable mysql

# 登录 MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE djangoblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'djangoblog'@'localhost' IDENTIFIED BY 'your_strong_password';
GRANT ALL PRIVILEGES ON djangoblog.* TO 'djangoblog'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. 项目部署

```bash
# 创建项目目录
mkdir -p /var/www/djangoblog
cd /var/www/djangoblog

# 克隆项目
git clone https://github.com/zhang123999-qq/DjangoBlog.git .

# 创建虚拟环境
python3.13 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements/production.txt

# 配置环境变量
cp .env.example .env
nano .env

# 填写配置：
# SECRET_KEY=your-secret-key
# DEBUG=False
# ALLOWED_HOSTS=your-domain.com
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=djangoblog
# DB_USER=djangoblog
# DB_PASSWORD=your_password
# DB_HOST=localhost

# 初始化
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 4. Gunicorn 配置

```bash
# 安装 Gunicorn
pip install gunicorn

# 创建 systemd 服务
sudo nano /etc/systemd/system/gunicorn.service
```

写入内容：

```ini
[Unit]
Description=Gunicorn instance for DjangoBlog
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/djangoblog
Environment="PATH=/var/www/djangoblog/venv/bin"
ExecStart=/var/www/djangoblog/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### 5. Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/djangoblog
```

写入内容：

```nginx
upstream djangoblog_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # 静态文件
    location /static/ {
        alias /var/www/djangoblog/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件
    location /media/ {
        alias /var/www/djangoblog/media/;
    }

    # 动态请求
    location / {
        proxy_pass http://djangoblog_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/djangoblog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. 配置 HTTPS（推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 常见问题

### 问题一：数据库连接失败

**错误**：
```
MySQLdb.OperationalError: (2005, "Unknown MySQL server host 'db'")
```

**解决**：
- Docker 环境：使用 `DB_HOST=db`
- 本地环境：使用 `DB_HOST=localhost`

### 问题二：静态文件 404

**解决**：
```bash
python manage.py collectstatic --clear
```

### 问题三：端口被占用

**解决**：
```bash
# 查找进程
lsof -i :8000
# 或
netstat -tulpn | grep 8000

# 杀死进程
kill -9 <PID>
```

### 问题四：迁移文件冲突

**解决**：
```bash
# 删除所有迁移文件（仅开发环境）
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete

# 重新创建
python manage.py makemigrations
python manage.py migrate
```

### 问题五：验证码不显示

**解决**：
```python
# settings.py 中添加
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
```

---

## 更新项目

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements/production.txt

# 执行迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 重启服务
sudo systemctl restart gunicorn
```

---

## 更多信息

- GitHub: https://github.com/zhang123999-qq/DjangoBlog
- 问题反馈: https://github.com/zhang123999-qq/DjangoBlog/issues
