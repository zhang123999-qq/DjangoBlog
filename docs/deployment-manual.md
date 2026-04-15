# DjangoBlog 手动部署教程（Ubuntu / 宝塔环境）

> **推荐**：如果使用 Docker 部署，请参考项目根目录 [README.md](../README.md) 的「快速开始」章节。
>
> 本教程适用于：不使用 Docker，直接在服务器上通过 Python + Gunicorn + Nginx 部署。  
> 本教程按"能跑通、可排错、可维护"的顺序编写。

---

## 一、部署前准备

### 1. 服务器要求

- 系统:Ubuntu 20.04+(或其他兼容 Linux)
- Python:3.12/3.13(建议与项目一致)
- MySQL:**8.0+**(Django 4.2 不支持 MySQL 5.7)
- Redis:可选(建议安装,未安装可关闭)

### 2. 基础工具安装

```bash
apt update
apt install -y git curl vim nginx redis-server
```

> 如果你不打算使用 Redis,可先不安装,但需要在 `.env` 中关闭 `USE_REDIS`。

---

## 二、拉取代码与进入目录

```bash
cd /www/wwwroot
git clone https://github.com/zhang123999-qq/DjangoBlog.git
cd DjangoBlog

git checkout main
git pull --ff-only origin main
```

可选:确认当前版本

```bash
git rev-parse --short HEAD
```

---

## 三、创建 Python 虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -U pip wheel setuptools
pip install -r requirements/production.txt
```

---

## 四、配置环境变量(重点)

### 1. 复制配置模板

```bash
cp .env.production.example .env
```

### 2. 编辑 `.env`

```bash
vim .env
```

请至少确认以下配置:

```env
# 基础
DEBUG=False
SECRET_KEY=请替换为高强度随机字符串
ALLOWED_HOSTS=localhost,127.0.0.1,zhtest.top,www.zhtest.top

# 数据库(必须 MySQL 8.0+)
DB_ENGINE=django.db.backends.mysql
DB_NAME=djangoblog
DB_USER=root
DB_PASSWORD=你的数据库密码
DB_HOST=127.0.0.1
DB_PORT=3306

# Redis(可选)
USE_REDIS=True
REDIS_URL=redis://127.0.0.1:6379/1

# HTTPS/反向代理相关
CSRF_TRUSTED_ORIGINS=https://zhtest.top,https://www.zhtest.top
```

> 注意:
> 1. `CSRF_TRUSTED_ORIGINS` 必须带 `http://` 或 `https://` 协议。
> 2. 如果 Redis 未安装,请设置 `USE_REDIS=False`。

---

## 五、初始化数据库与静态资源

### 1. 执行迁移

```bash
source .venv/bin/activate
python manage.py migrate
```

### 2. 收集静态文件

```bash
python manage.py collectstatic --noinput
```

### 3. 创建管理员

```bash
python manage.py createsuperuser
```

### 4. 初始化分类/标签/论坛板块

```bash
python scripts/init_default_data.py
```

---

## 六、先前台验证 Gunicorn 是否正常

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --threads 2 \
  --timeout 60
```

新开终端检查:

```bash
curl -I http://127.0.0.1:8000
```

返回 `200/301/302` 说明服务已启动。

---

## 七、配置 systemd(后台常驻)

创建服务文件:

```bash
cat >/etc/systemd/system/djangoblog.service <<'EOF'
[Unit]
Description=DjangoBlog Gunicorn Service
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/www/wwwroot/DjangoBlog
EnvironmentFile=/www/wwwroot/DjangoBlog/.env
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=/www/wwwroot/DjangoBlog/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --threads 2 --timeout 60
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

生效并启动:

```bash
systemctl daemon-reload
systemctl enable --now djangoblog
systemctl status djangoblog --no-pager
```

查看日志:

```bash
journalctl -u djangoblog -n 100 --no-pager
```

---

## 八、配置 Nginx 反向代理

创建站点配置:

```bash
cat >/etc/nginx/sites-available/djangoblog.conf <<'EOF'
server {
    listen 80;
    server_name zhtest.top www.zhtest.top;

    client_max_body_size 20m;

    location /static/ {
        alias /www/wwwroot/DjangoBlog/staticfiles/;
        access_log off;
        expires 30d;
    }

    location /media/ {
        alias /www/wwwroot/DjangoBlog/media/;
        access_log off;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120;
    }
}
EOF
```

启用并重载:

```bash
ln -sf /etc/nginx/sites-available/djangoblog.conf /etc/nginx/sites-enabled/djangoblog.conf
nginx -t
systemctl reload nginx
```

---

## 九、配置 HTTPS(推荐)

如果你已解析域名到服务器,可使用 certbot:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d zhtest.top -d www.zhtest.top
```

证书自动续期检查:

```bash
certbot renew --dry-run
```

---

## 十、常用运维命令

### 1. 查看服务状态

```bash
systemctl status djangoblog --no-pager
systemctl status nginx --no-pager
```

### 2. 重启服务

```bash
systemctl restart djangoblog
systemctl reload nginx
```

### 3. 查看日志

```bash
journalctl -u djangoblog -f
journalctl -u djangoblog -n 200 --no-pager
```

### 4. 代码更新后发布

```bash
cd /www/wwwroot/DjangoBlog
source .venv/bin/activate

git pull --ff-only origin main
pip install -r requirements/production.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart djangoblog
```

---

## 十一、故障排查速查

### 问题 1:`No module named 'MySQLdb'`

原因:MySQL 驱动适配未生效。
处理:确认代码已拉到最新,项目已内置 PyMySQL 兼容逻辑;重新拉取并重启服务。

```bash
git pull --ff-only origin main
systemctl restart djangoblog
```

### 问题 2:`MySQL 8 or later is required (found 5.7.x)`

原因:Django 4.2 不支持 MySQL 5.7。
处理:升级到 MySQL 8.0+,并更新 `.env` 的连接信息。

### 问题 3:访问首页 500

优先看日志:

```bash
journalctl -u djangoblog -n 200 --no-pager
```

常见点:
- `.env` 缺少关键变量
- `CSRF_TRUSTED_ORIGINS` 未带协议
- Redis 未启动但 `USE_REDIS=True`

### 问题 4:端口占用(8000)

```bash
ss -lntp | grep :8000
fuser -k 8000/tcp
systemctl restart djangoblog
```

---

## 十二、安全建议(上线前必看)

1. 立即更换示例 `SECRET_KEY` 和数据库密码。
2. 不要把 `.env` 提交到 Git。
3. 管理后台尽量仅允许可信 IP 访问。
4. 定期执行系统与依赖更新。
5. 开启 HTTPS 后再保持 `SECURE_SSL_REDIRECT=True`。

---

## 十三、部署完成验收清单

- [ ] `python manage.py migrate` 成功
- [ ] `collectstatic` 成功
- [ ] `systemctl status djangoblog` 为 active
- [ ] `nginx -t` 通过
- [ ] 站点首页可访问
- [ ] 管理后台可登录
- [ ] API 文档/核心页面可打开

---

如果你希望,我可以再补一版《宝塔面板专用部署教程(逐项点击版)》放在同目录。