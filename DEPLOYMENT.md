# 部署文档

本文档提供了 DjangoBlog 项目的多种部署方式，包括本地开发、Docker 部署、传统服务器部署等。

## 1. 环境要求

- Python 3.8+
- Django 4.2+
- 数据库：SQLite (默认) / MySQL / PostgreSQL
- Redis (可选，用于缓存)

## 2. 本地开发环境

### 2.1 克隆项目

```bash
git clone https://github.com/yourusername/djangoblog.git
cd djangoblog
```

### 2.2 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2.3 安装依赖

```bash
pip install -r requirements/development.txt
```

### 2.4 配置环境变量

复制 `.env.example` 文件为 `.env` 并修改相应配置：

```bash
cp .env.example .env
```

### 2.5 数据库迁移

```bash
python manage.py migrate
```

### 2.6 创建超级用户

```bash
python manage.py createsuperuser
```

### 2.7 启动开发服务器

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 查看项目。

## 3. Docker 部署

### 3.1 使用 Docker Compose

1. 确保已安装 Docker 和 Docker Compose

2. 构建并启动容器：

```bash
docker-compose up -d
```

3. 运行数据库迁移：

```bash
docker-compose exec web python manage.py migrate
```

4. 创建超级用户：

```bash
docker-compose exec web python manage.py createsuperuser
```

5. 访问 http://localhost:8000/ 查看项目。

### 3.2 单独使用 Docker

1. 构建镜像：

```bash
docker build -t djangoblog .
```

2. 运行容器：

```bash
docker run -d -p 8000:8000 --name djangoblog djangoblog
```

## 4. 传统服务器部署

### 4.1 安装系统依赖

```bash
# Ubuntu/Debian
apt update
apt install -y python3 python3-pip python3-venv nginx supervisor

# CentOS/RHEL
yum install -y python3 python3-pip python3-venv nginx supervisor
```

### 4.2 部署项目

1. 克隆项目到服务器：

```bash
git clone https://github.com/yourusername/djangoblog.git /var/www/djangoblog
cd /var/www/djangoblog
```

2. 创建虚拟环境并安装依赖：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/production.txt
```

3. 配置环境变量：

```bash
cp .env.example .env
# 编辑 .env 文件，设置生产环境配置
```

4. 数据库迁移：

```bash
python manage.py migrate
python manage.py collectstatic
```

### 4.3 配置 Gunicorn

创建 Gunicorn 配置文件：

```bash
# /etc/systemd/system/gunicorn.service
[Unit]
Description=Gunicorn daemon for DjangoBlog
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/djangoblog
ExecStart=/var/www/djangoblog/venv/bin/gunicorn --workers 3 --bind unix:/var/www/djangoblog/djangoblog.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

启动 Gunicorn：

```bash
systemctl enable gunicorn
systemctl start gunicorn
```

### 4.4 配置 Nginx

创建 Nginx 配置文件：

```bash
# /etc/nginx/sites-available/djangoblog
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://unix:/var/www/djangoblog/djangoblog.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/djangoblog/staticfiles/;
    }

    location /media/ {
        alias /var/www/djangoblog/media/;
    }
}
```

启用配置：

```bash
ln -s /etc/nginx/sites-available/djangoblog /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 4.5 配置 Supervisor (可选)

创建 Supervisor 配置文件：

```bash
# /etc/supervisor/conf.d/djangoblog.conf
[program:djangoblog]
command=/var/www/djangoblog/venv/bin/gunicorn --workers 3 --bind unix:/var/www/djangoblog/djangoblog.sock config.wsgi:application
directory=/var/www/djangoblog
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/djangoblog.log
stderr_logfile=/var/log/supervisor/djangoblog.err.log
```

启动 Supervisor：

```bash
systemctl enable supervisor
systemctl start supervisor
supervisorctl update
supervisorctl start djangoblog
```

## 5. 部署注意事项

1. **安全设置**：
   - 确保 `DEBUG=False` 在生产环境
   - 设置强密码和密钥
   - 配置 HTTPS

2. **性能优化**：
   - 使用 Redis 作为缓存
   - 启用 gzip 压缩
   - 配置适当的 Gunicorn 工作进程数

3. **监控**：
   - 配置日志记录
   - 设置监控告警

4. **备份**：
   - 定期备份数据库
   - 备份重要配置文件

## 6. 常见问题

### 6.1 静态文件不显示

确保运行了 `python manage.py collectstatic` 命令，并正确配置了 Nginx 静态文件路径。

### 6.2 数据库连接失败

检查数据库配置和连接字符串，确保数据库服务正常运行。

### 6.3 502 Bad Gateway 错误

检查 Gunicorn 服务是否正常运行，以及 Nginx 配置是否正确。

## 7. 升级指南

1. 拉取最新代码：

```bash
git pull origin master
```

2. 安装新依赖：

```bash
pip install -r requirements/production.txt
```

3. 运行数据库迁移：

```bash
python manage.py migrate
```

4. 收集静态文件：

```bash
python manage.py collectstatic
```

5. 重启服务：

```bash
systemctl restart gunicorn nginx
```

---

部署完成后，您的 DjangoBlog 项目应该可以正常运行了。如需进一步帮助，请参考 Django 官方文档或项目的 README.md 文件。