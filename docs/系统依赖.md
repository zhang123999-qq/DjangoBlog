# 系统依赖安装指南

本文档说明在不同操作系统上安装 DjangoBlog 所需的系统依赖。

---

## Linux (Debian/Ubuntu)

### 基础依赖

```bash
# 更新包列表
sudo apt update

# Python 开发头文件
sudo apt install python3-dev python3-pip python3-venv

# 编译工具
sudo apt install build-essential

# SSL 支持（MySQL、Redis 等）
sudo apt install libssl-dev

# 事件库（gevent 依赖）
sudo apt install libevent-dev

# 图片处理
sudo apt install libjpeg-dev zlib1g-dev libpng-dev

# 数据库客户端（可选）
# MySQL
sudo apt install libmysqlclient-dev default-libmysqlclient-dev

# PostgreSQL（可选）
sudo apt install libpq-dev

# XML 解析（可选）
sudo apt install libxml2-dev libxslt1-dev
```

### 一键安装脚本

```bash
# 完整安装
sudo apt update && sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev \
    libevent-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libmysqlclient-dev \
    default-libmysqlclient-dev
```

---

## Linux (CentOS/RHEL/Rocky)

### 基础依赖

```bash
# 更新包列表
sudo dnf update

# Python 开发头文件
sudo dnf install python3-devel python3-pip

# 编译工具
sudo dnf groupinstall "Development Tools"

# SSL 支持
sudo dnf install openssl-devel

# 事件库
sudo dnf install libevent-devel

# 图片处理
sudo dnf install libjpeg-devel zlib-devel libpng-devel

# 数据库客户端（可选）
# MySQL
sudo dnf install mysql-devel

# PostgreSQL（可选）
sudo dnf install postgresql-devel
```

### 一键安装脚本

```bash
sudo dnf update && sudo dnf install -y \
    python3-devel \
    python3-pip \
    openssl-devel \
    libevent-devel \
    libjpeg-devel \
    zlib-devel \
    libpng-devel \
    mysql-devel
```

---

## Linux (Arch Linux)

```bash
# 更新系统
sudo pacman -Syu

# 基础依赖
sudo pacman -S --needed \
    python \
    python-pip \
    base-devel \
    openssl \
    libevent \
    libjpeg-turbo \
    zlib \
    libpng

# MySQL 客户端（可选）
sudo pacman -S mariadb-libs
```

---

## macOS

### 使用 Homebrew

```bash
# 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python
brew install python@3.13

# 安装编译工具
xcode-select --install

# 安装依赖库
brew install openssl libevent jpeg zlib libpng mysql-client

# 设置 OpenSSL 路径（Apple Silicon）
export LDFLAGS="-L/opt/homebrew/opt/openssl/lib"
export CPPFLAGS="-I/opt/homebrew/opt/openssl/include"

# Intel Mac
export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"
```

---

## Windows

### 方式一：使用预编译包

Windows 不需要编译系统依赖，大多数 Python 包提供预编译的 wheel 文件。

```powershell
# 安装 Visual Studio Build Tools（某些包需要）
# 下载地址: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 或使用 Chocolatey
choco install visualstudio2022buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools"

# 安装 Python（推荐从官网下载）
# https://www.python.org/downloads/windows/
```

### 方式二：使用 WSL2（推荐）

```bash
# 在 WSL2 中使用 Linux 方式安装
wsl --install -d Ubuntu-24.04

# 然后按照 Linux (Debian/Ubuntu) 的步骤操作
```

---

## Gunicorn 生产部署依赖

### 系统包

```bash
# Debian/Ubuntu
sudo apt install python3-dev build-essential libssl-dev libevent-dev

# CentOS/RHEL
sudo dnf install python3-devel gcc openssl-devel libevent-devel
```

### Python 包

```bash
pip install gunicorn gevent django setproctitle
```

### Gunicorn 配置示例

创建 `gunicorn.conf.py`：

```python
# gunicorn.conf.py
import multiprocessing

# 服务器绑定
bind = "0.0.0.0:8000"

# 工作进程数（推荐: CPU核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "gevent"  # 使用 gevent 异步模式
worker_connections = 1000  # 每个 worker 的最大并发连接

# 超时设置
timeout = 120
graceful_timeout = 30
keepalive = 5

# 进程名
proc_name = "djangoblog"

# 日志
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 预加载应用
preload_app = True

# 安全设置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

### 启动命令

```bash
# 开发模式
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --reload

# 生产模式
gunicorn config.wsgi:application -c gunicorn.conf.py

# 使用 gevent
gunicorn config.wsgi:application --worker-class gevent --workers 4

# 使用 systemd 管理（推荐）
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

---

## Systemd 服务配置

创建 `/etc/systemd/system/gunicorn.service`：

```ini
[Unit]
Description=DjangoBlog Gunicorn Server
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/DjangoBlog
Environment="PATH=/var/www/DjangoBlog/.venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/var/www/DjangoBlog/.venv/bin/gunicorn \
    --worker-class gevent \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/www/DjangoBlog/logs/access.log \
    --error-logfile /var/www/DjangoBlog/logs/error.log \
    config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

---

## Nginx 配置

创建 `/etc/nginx/sites-available/djangoblog`：

```nginx
upstream djangoblog {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL 配置
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 静态文件
    location /static/ {
        alias /var/www/DjangoBlog/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 媒体文件
    location /media/ {
        alias /var/www/DjangoBlog/media/;
        expires 7d;
    }
    
    # 代理到 Gunicorn
    location / {
        proxy_pass http://djangoblog;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/djangoblog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 验证安装

### 检查系统依赖

```bash
# 检查 Python 版本
python3 --version  # 应该 >= 3.10

# 检查编译工具
gcc --version
make --version

# 检查 SSL
python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"

# 检查图片处理
python3 -c "from PIL import Image; print('Pillow OK')"

# 检查 MySQL 客户端
python3 -c "import MySQLdb; print('MySQL OK')" 2>/dev/null || echo "MySQL not configured"
```

### 检查 Gunicorn

```bash
# 检查 Gunicorn 版本
gunicorn --version

# 检查 gevent
python3 -c "import gevent; print(f'gevent {gevent.__version__}')"

# 检查 setproctitle
python3 -c "import setproctitle; print('setproctitle OK')"
```

---

## 故障排除

### mysqlclient 安装失败

```bash
# Debian/Ubuntu
sudo apt install libmysqlclient-dev default-libmysqlclient-dev

# macOS
brew install mysql-client
export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"
```

### gevent 安装失败

```bash
# Debian/Ubuntu
sudo apt install python3-dev libevent-dev build-essential

# CentOS/RHEL
sudo dnf install python3-devel libevent-devel gcc
```

### Pillow 安装失败

```bash
# Debian/Ubuntu
sudo apt install libjpeg-dev zlib1g-dev libpng-dev

# CentOS/RHEL
sudo dnf install libjpeg-devel zlib-devel libpng-devel

# macOS
brew install jpeg zlib libpng
```

---

## 快速参考

| 依赖 | 用途 | 包名 |
|------|------|------|
| python3-dev | Python 头文件 | Debian/Ubuntu |
| build-essential | 编译工具 | Debian/Ubuntu |
| libssl-dev | SSL 支持 | Debian/Ubuntu |
| libevent-dev | gevent 依赖 | Debian/Ubuntu |
| libmysqlclient-dev | MySQL 客户端 | Debian/Ubuntu |
| gunicorn | WSGI 服务器 | pip |
| gevent | 异步工作模式 | pip |
| setproctitle | 进程名设置 | pip |
