# DjangoBlog 部署指南

本文档描述如何部署 DjangoBlog 项目到生产环境。

---

## 📋 系统要求

### 基础环境
- Python 3.10+
- MySQL 8.0+ 或 PostgreSQL 13+
- Redis 6.0+
- Nginx 1.18+

### 推荐配置
- **CPU:** 2+ 核心
- **内存:** 4GB+
- **存储:** 20GB+ SSD
- **操作系统:** Ubuntu 20.04+ / CentOS 8+

---

## 🚀 快速部署

### 1. 克隆项目
```bash
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog
```

### 2. 创建虚拟环境
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖
```bash
# 生产环境依赖
pip install -r requirements/production.lock

# 或者使用 pyproject.toml（适合开发/打包验证）
pip install -e ".[prod]"
```

### 4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置以下变量：
# - SECRET_KEY: Django 密钥（必须修改）
# - DEBUG: False（生产环境）
# - DATABASE_URL: 数据库连接
# - REDIS_URL: Redis 连接
# - ALLOWED_HOSTS: 允许的域名
```

### 5. 数据库迁移
```bash
python manage.py migrate
```

### 6. 收集静态文件
```bash
python manage.py collectstatic --noinput
```

### 7. 创建超级用户
```bash
python manage.py createsuperuser
```

---

## 🔧 生产环境配置

### 1. Gunicorn 配置
```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### 2. Nginx 配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 静态文件
    location /static/ {
        alias /path/to/DjangoBlog/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 媒体文件
    location /media/ {
        alias /path/to/DjangoBlog/media/;
        expires 7d;
    }
    
    # API 和应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Systemd 服务配置
```ini
# /etc/systemd/system/djangoblog.service
[Unit]
Description=DjangoBlog Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/DjangoBlog
Environment="PATH=/path/to/DjangoBlog/.venv/bin"
ExecStart=/path/to/DjangoBlog/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable djangoblog
sudo systemctl start djangoblog
```

---

## 🔒 安全配置

### 1. 环境变量安全
```bash
# 确保 .env 文件权限
chmod 600 .env
chown www-data:www-data .env
```

### 2. 数据库安全
```bash
# MySQL 安全配置
mysql_secure_installation

# 创建专用数据库用户
mysql -u root -p
CREATE DATABASE djangoblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'djangoblog'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON djangoblog.* TO 'djangoblog'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Redis 安全
```bash
# Redis 配置（/etc/redis/redis.conf）
requirepass your_redis_password
bind 127.0.0.1
protected-mode yes
```

### 4. 防火墙配置
```bash
# UFW 配置
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 📊 监控配置

### 1. Sentry 错误监控
```python
# 在 settings/production.py 中配置
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True
)
```

### 2. 日志配置
```python
# 在 settings/base.py 中配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/djangoblog.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## 🔄 备份策略

### 1. 数据库备份脚本
```bash
#!/bin/bash
# deploy/backup.sh

BACKUP_DIR="/backups/djangoblog"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="djangoblog"
DB_USER="djangoblog"
DB_PASS="your_password"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 备份媒体文件
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /path/to/DjangoBlog/media/

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "备份完成: $DATE"
```

### 2. 定时备份
```bash
# 添加到 crontab
0 2 * * * /path/to/DjangoBlog/deploy/backup.sh
```

---

## 🧪 测试部署

### 1. 健康检查
```bash
# 检查服务状态
curl https://your-domain.com/healthz/

# 预期响应
{"status": "healthy", "timestamp": "..."}
```

### 2. API 测试
```bash
# 测试 API 端点
curl https://your-domain.com/api/posts/
curl https://your-domain.com/api/categories/
```

### 3. 性能测试
```bash
# 使用 ab 进行压力测试
ab -n 1000 -c 10 https://your-domain.com/
```

---

## 🚨 故障排除

### 常见问题

#### 1. 502 Bad Gateway
```bash
# 检查 Gunicorn 状态
sudo systemctl status djangoblog

# 检查日志
sudo journalctl -u djangoblog -f
```

#### 2. 静态文件 404
```bash
# 重新收集静态文件
python manage.py collectstatic --noinput

# 检查 Nginx 配置
sudo nginx -t
```

#### 3. 数据库连接错误
```bash
# 检查数据库服务
sudo systemctl status mysql

# 检查连接配置
python manage.py dbshell
```

---

## 📚 相关文档

- [项目审计报告](docs/PROJECT_AUDIT_2026.md)
- [安全策略](SECURITY.md)
- [贡献指南](CONTRIBUTING.md)
- [更新日志](CHANGELOG.md)

---

**文档版本:** 1.0  
**最后更新:** 2026年4月15日  
**维护者:** DjangoBlog 团队
