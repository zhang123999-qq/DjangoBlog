# DjangoBlog deploy/ 目录修复方案

> 生成时间: 2026-04-12
> 问题总数: 10 个（严重 3 / 中等 4 / 小问题 3）

---

## 总览

| 阶段 | 修复内容 | 涉及文件 | 预计工时 |
|------|---------|---------|---------|
| P0 | Python 版本 + collectstatic + gunicorn 统一 | Dockerfile, docker-compose.yml | 30min |
| P1 | Nginx 配置适配 Docker | docker-compose.yml | 10min |
| P2 | 安全加固 | auto-deploy.sh, docker-compose.yml, .env.example | 20min |
| P3 | 健康检查集成 + 清理 | docker-compose.yml, health.sh, 旧文件 | 15min |

---

## P0: 严重问题修复（必须）

### P0-1: Dockerfile Python 版本不匹配

**问题**: 基础镜像 `python:3.14.3-slim`，但 COPY 路径是 `python3.13/site-packages`

**方案**: 统一使用 `python:3.13-slim`（项目 requirements 标注 Python 3.13+）

```dockerfile
# === 修改前 ===
FROM docker.1ms.run/library/python:3.14.3-slim AS builder
FROM docker.1ms.run/library/python:3.14.3-slim
COPY --from=builder /usr/local/lib/python3.13/site-packages ...

# === 修改后 ===
FROM docker.1ms.run/library/python:3.13-slim AS builder
FROM docker.1ms.run/library/python:3.13-slim
COPY --from=builder /usr/local/lib/python3.13/site-packages ...
```

同时修复 apt 源代号：Python 3.13 slim 基于 Debian bookworm，不是 trixie。

```dockerfile
# === 修改前 ===
echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main"

# === 修改后 ===
echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main"
echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main"
echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main"
```

**完整 Dockerfile 修改点**:
1. 基础镜像: `python:3.14.3-slim` → `python:3.13-slim`
2. apt 源: `trixie` → `bookworm`（两处 builder + final）
3. 注释修正: "单阶段构建" → "多阶段构建"
4. 添加 collectstatic 阶段（见 P0-2）

---

### P0-2: 添加 collectstatic 步骤

**问题**: production.py 用 `WhiteNoise CompressedManifestStaticFilesStorage`，但从未执行 `collectstatic`

**方案 A（推荐）**: 在 Dockerfile 的 builder 阶段执行 collectstatic

```dockerfile
# 在 builder 阶段末尾添加
COPY --chown=root:root . /app
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=build-placeholder \
    python manage.py collectstatic --noinput
```

**方案 B**: 在 docker-compose.yml 添加 init 服务

```yaml
collectstatic:
  image: djangoblog-web:latest
  container_name: djangoblog-collectstatic
  restart: "no"
  depends_on:
    web:
      condition: service_started
  environment:
    - DJANGO_SETTINGS_MODULE=config.settings.production
    - SECRET_KEY=${SECRET_KEY}
  volumes:
    - static_volume:/app/staticfiles
  command: python manage.py collectstatic --noinput
  networks:
    - djangoblog
```

**决策**: 采用方案 A（构建时完成，启动时无需额外步骤），同时在 docker-compose 的 migrate 服务也执行 collectstatic 作为兜底。

---

### P0-3: 统一 Gunicorn 配置

**问题**: gunicorn.conf.py 存在但未被引用，docker-compose.yml 硬编码了不同的参数

**方案**: 删除 docker-compose.yml 中的硬编码 command，改用 gunicorn.conf.py

```yaml
# === 修改前 ===
command: ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]

# === 修改后 ===
command: ["gunicorn", "config.wsgi:application", "--config", "deploy/gunicorn.conf.py"]
```

同时把 gunicorn.conf.py 复制到镜像中（Dockerfile 添加）:

```dockerfile
COPY --chown=root:root deploy/gunicorn.conf.py /app/deploy/gunicorn.conf.py
```

**gunicorn.conf.py 调整**（适配 Docker）:
- 日志路径改为 stdout/stderr（Docker 日志驱动接管）
- workers 从 `cpu_count * 2 + 1` 改为环境变量控制，默认 4

```python
# 修改日志配置
accesslog = '-'
errorlog = '-'
```

---

## P1: 中等问题修复（建议）

### P1-1: Nginx 配置适配 Docker

**问题**: docker-compose.yml 挂载了 `nginx.conf`（宝塔专用），路径全部不对

**方案**: docker-compose.yml 改用 `nginx.generic.conf`，并修改适配 Docker：

```yaml
nginx:
  volumes:
    - ./nginx.generic.conf:/etc/nginx/conf.d/default.conf:ro
    # 删除: - ./nginx/ssl:/etc/nginx/ssl:ro（路径不存在）
```

**nginx.generic.conf 修改**:
```nginx
upstream djangoblog_backend {
    server web:8000;  # Docker 内用服务名，非 127.0.0.1
    keepalive 32;
}

server {
    listen 80;
    server_name www.zhtest.top zhtest.top;

    location /static/ {
        alias /app/staticfiles/;  # Docker volume 路径
        expires 30d;
        add_header Cache-Control "public, no-transform";
        access_log off;
    }

    location /media/ {
        alias /app/media/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
        access_log off;
    }

    location / {
        proxy_pass http://djangoblog_backend;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    # 禁止访问敏感文件
    location ~* (\.env|\.git|\.project)$ {
        return 404;
    }
}
```

> 注：HTTPS 由外部负载均衡器或宿主机 Nginx 终结，Docker 内部走 HTTP。

---

### P1-2: auto-deploy.sh 安全加固

**问题 1**: `ALLOWED_HOSTS=*`
```bash
# === 修改前 ===
ALLOWED_HOSTS=*,127.0.0.1,localhost

# === 修改后 ===
read -p "请输入域名 (如 www.example.com): " DOMAIN
DOMAIN="${DOMAIN:-localhost}"
ALLOWED_HOSTS=${DOMAIN},127.0.0.1,localhost
```

**问题 2**: 弱密码
```bash
# === 修改前 ===
DB_PASSWORD=***

# === 修改后 ===
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
DB_ROOT_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(20))")
```

**问题 3**: SECRET_KEY 格式错误
```bash
# === 修改前（第112行） ===
SECRET_KEY=*** -c "import secrets; print(secrets.token_urlsafe(50))" ...

# === 修改后 ===
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || openssl rand -base64 48)
```

---

### P1-3: docker-compose.yml 端口安全

**问题**: MySQL 3306 和 Redis 6379 对外暴露

**方案**: 仅在内部网络通信，移除 ports 映射。需要外部访问时通过 `docker exec` 或临时映射。

```yaml
# === 修改前 ===
db:
  ports:
    - "${DB_PORT_EXPOSED:-3306}:3306"
redis:
  ports:
    - "${REDIS_PORT_EXPOSED:-6379}:6379"

# === 修改后 ===
db:
  # 仅内部网络访问，不暴露端口
  # 如需外部访问: docker compose exec db mysql -u root -p
  expose:
    - "3306"
redis:
  expose:
    - "6379"
```

> `expose` 仅对内部网络可见，`ports` 对外可见。

---

### P1-4: migrate 服务添加 collectstatic 兜底

```yaml
migrate:
  command: >
    sh -c "
      python manage.py migrate --noinput &&
      python manage.py collectstatic --noinput &&
      echo 'Migrations and collectstatic complete.'
    "
```

---

## P2: 小问题修复

### P2-1: fix-fnnas.sh 移除

此脚本是飞牛 NAS 的临时 hack，已不需要。当前 Dockerfile 没有 `--mount=type=cache` 语法。

**操作**: 删除 `deploy/fix-fnnas.sh`

---

### P2-2: health.sh 接入 docker-compose

添加独立的健康检查服务（可选），或直接使用 compose 内置的 healthcheck。

当前 compose 已有 healthcheck 定义，无需额外集成。health.sh 保留作为手动诊断工具。

---

### P2-3: Dockerfile 注释修正

```dockerfile
# === 修改前 ===
# 优化版本：单阶段构建 + 清华 apt 源 + pip 清华源

# === 修改后 ===
# 多阶段构建：builder 编译依赖 → final 仅运行时
# 优化：清华 apt/pip 源加速构建
```

---

## 修改文件清单

| 文件 | 操作 | 改动量 |
|------|------|--------|
| `deploy/Dockerfile` | 修改 | ~15 行 |
| `deploy/docker-compose.yml` | 修改 | ~20 行 |
| `deploy/gunicorn.conf.py` | 修改 | ~3 行 |
| `deploy/auto-deploy.sh` | 修改 | ~10 行 |
| `deploy/nginx.generic.conf` | 修改 | ~5 行 |
| `deploy/nginx.conf` | 不动 | 宝塔专用保留 |
| `deploy/fix-fnnas.sh` | 删除 | - |
| `deploy/.env.example` | 不动 | 已正确 |

---

## 验证清单

修复完成后按以下步骤验证：

```bash
# 1. 构建镜像
docker compose -f deploy/docker-compose.yml build web

# 2. 启动服务
docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d

# 3. 检查 collectstatic
docker compose exec web ls /app/staticfiles/staticfiles.json

# 4. 检查 gunicorn 配置加载
docker compose logs web | grep "工作进程数"

# 5. 检查 nginx 代理
curl -I http://localhost/

# 6. 健康检查
bash deploy/health.sh check

# 7. 验证 404 不泄露 DEBUG 信息
curl -s http://localhost/nonexistent | grep -c "DEBUG"  # 应为 0
```

---

## 回滚方案

如修复后出现问题：

```bash
# 停止服务
docker compose -f deploy/docker-compose.yml down

# 回退代码
git checkout HEAD -- deploy/

# 重新启动
docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d
```
