#!/usr/bin/env bash
# =============================================
# DjangoBlog 一键自动部署脚本
# 使用方法: bash deploy/auto-deploy.sh
# 功能: 自动生成 .env、配置镜像加速、构建镜像、拉起服务、迁移、创建管理员
# 架构: 5 容器 (db + redis + web + celery_worker + celery_beat)
#       宿主机 Nginx 反向代理到 web:8000
#       migrate/collectstatic 在 web 启动时由 entrypoint.sh 自动执行
# 进程守护: 支持中断信号安全退出，完成后自动退出，容器由 Docker restart 策略守护
# =============================================

set -uo pipefail

# 项目目录
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_DIR"

ENV_FILE="$PROJECT_DIR/deploy/.env"
COMPOSE_FILE="$PROJECT_DIR/deploy/docker-compose.yml"

# ====================================
# 颜色输出（必须在其他函数之前定义）
# ====================================
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
log()  { echo -e "${GREEN}[$(date '+%H:%M:%S')] $*${NC}"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN: $*${NC}"; }
fail() { echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $*${NC}"; exit 1; }

# ====================================
# 进程守护
# ====================================
# 捕获中断信号（Ctrl+C / SIGTERM），安全退出
cleanup() {
    echo ""
    echo -e "\033[0;33m⚠️  脚本中断，容器仍在运行（由 Docker restart 策略守护）\033[0m"
    echo "  查看状态: bash deploy/auto-deploy.sh status"
    exit 130
}
trap cleanup INT TERM

# ====================================
# 权限检查
# ====================================
if [ "$(id -u)" -ne 0 ]; then
    fail "此脚本需要 root 权限运行: sudo bash $0"
fi

# ====================================
# 快捷命令（统一参数）
# ====================================
dc() { docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"; }

echo "============================================================"
echo " DjangoBlog 一键自动部署"
echo " 项目路径: $PROJECT_DIR"
echo " 架构: 5 容器 (db + redis + web + celery_worker + celery_beat)"
echo "============================================================"

# ========================================
# 0. 模式判断
# ========================================
MODE="${1:-deploy}"

if [ "$MODE" = "status" ]; then
    if [ ! -f "$ENV_FILE" ]; then
        fail ".env 不存在，请先运行: bash deploy/auto-deploy.sh"
    fi
    dc ps
    echo ""
    log "镜像列表:"
    docker images | grep djangoblog || echo "  (无)"
    echo ""
    log "磁盘使用:"
    docker system df | grep -iE "NAME|djangoblog" || echo "  (无)"
    exit 0
fi

if [ "$MODE" = "update" ]; then
    log "===== 增量更新 ====="
    if [ -d "$PROJECT_DIR/.git" ]; then
        log "拉取最新代码..."
        (cd "$PROJECT_DIR" && git pull) || warn "git pull 失败，跳过"
    fi
    log "构建镜像（只构建一次）..."
    dc build web || fail "镜像构建失败"
    log "重启 web/celery（entrypoint.sh 自动执行迁移）..."
    dc up -d --force-recreate web celery_worker celery_beat || fail "服务重启失败"
    log "等待 web 就绪..."
    WEB_PORT=$(grep WEB_PORT_EXPOSED "$ENV_FILE" | head -1 | cut -d= -f2)
    WEB_PORT="${WEB_PORT:-8000}"
    waited=0
    while ! curl -sf http://localhost:${WEB_PORT}/healthz/ > /dev/null 2>&1; do
        sleep 2
        waited=$((waited + 2))
        [ $waited -ge 60 ] && { warn "Web 服务未就绪，检查日志: dc logs web"; break; }
        printf "."
    done
    echo ""
    log "===== 更新完成 ====="
    dc ps
    exit 0
fi

if [ "$MODE" = "stop" ]; then
    dc down
    log "服务已停止"
    exit 0
fi

if [ "$MODE" = "restart" ]; then
    dc restart
    dc ps
    exit 0
fi

# ========================================
# 1. 自动生成 .env
# ========================================
if [ ! -f "$ENV_FILE" ]; then
    log "生成 .env 配置文件..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || openssl rand -base64 48)
    DB_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))" 2>/dev/null || openssl rand -base64 16)
    DB_ROOT_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(20))" 2>/dev/null || openssl rand -base64 20)
    REDIS_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))" 2>/dev/null || openssl rand -base64 24)

    read -p "请输入域名 (如 www.example.com，默认 localhost): " DOMAIN
    DOMAIN="${DOMAIN:-localhost}"

    cat > "$ENV_FILE" << EOF
# DjangoBlog 配置（自动生成于 $(date '+%Y-%m-%d %H:%M:%S')）
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=${DOMAIN},127.0.0.1,localhost
DB_ENGINE=django.db.backends.mysql
DB_NAME=djangoblog
DB_USER=djangouser
DB_PASSWORD=${DB_PASS}
DB_HOST=db
DB_PORT=3306
DB_ROOT_PASSWORD=${DB_ROOT_PASS}
REDIS_PASSWORD=${REDIS_PASS}
REDIS_URL=redis://:${REDIS_PASS}@redis:6379/1
CELERY_BROKER_URL=redis://:${REDIS_PASS}@redis:6379/0
CELERY_RESULT_BACKEND=redis://:${REDIS_PASS}@redis:6379/0
WEB_PORT_EXPOSED=8000
ALLOWED_HOSTS=${DOMAIN},127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1,http://${DOMAIN}
USE_X_FORWARDED_PROTO=False
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
API_PAGE_SIZE=20
BAIDU_APP_ID=
BAIDU_API_KEY=
BAIDU_SECRET_KEY=
MODERATION_MODE=auto
EOF
    log "✅ .env 已自动生成"
else
    log "✅ .env 已存在，使用现有配置"
fi

# 检查 SECRET_KEY 有效性（长度≥40 且不是默认的 django-insecure）
_sk_val=$(grep '^SECRET_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2)
_sk_len=${#_sk_val}
if [ "$_sk_len" -lt 40 ] 2>/dev/null || echo "$_sk_val" | grep -q '^django-insecure'; then
    warn "SECRET_KEY 无效（长度=$_sk_len），重新生成..."
    new_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 40)
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${new_key}|g" "$ENV_FILE" 2>/dev/null || \
        sed -i "" "s/^SECRET_KEY=.*/SECRET_KEY=${new_key}/g" "$ENV_FILE" 2>/dev/null || true
    log "✅ SECRET_KEY 已重新生成"
fi

# ========================================
# 2. 创建数据目录
# ========================================
log "创建数据目录..."
mkdir -p "$PROJECT_DIR/deploy/logs"
log "✅ 目录就绪"

# ========================================
# 3. 检查 Docker 环境
# ========================================
log "检查 Docker 环境..."
command -v docker  &> /dev/null || fail "Docker 未安装"
docker compose version &> /dev/null  || fail "Docker Compose 未安装"
log "✅ Docker 就绪 ($(docker compose version 2>/dev/null))"

# ========================================
# 4. 配置 Docker 镜像加速（中国大陆）
# ========================================
log "检查网络环境..."
if curl -s --connect-timeout 3 "https://www.baidu.com" > /dev/null 2>&1; then
    log "中国大陆网络，配置镜像加速..."
    DAEMON_JSON="/etc/docker/daemon.json"
    # 按稳定性排序的镜像源列表（始终刷新，避免使用已失效的旧镜像）
    MIRRORS='["https://dockerpull.org","https://docker.1ms.run","https://docker.xuanyuan.me"]'
    NEED_RESTART=false
    if [ ! -f "$DAEMON_JSON" ]; then
        mkdir -p /etc/docker
        printf '{\n  "registry-mirrors": %s\n}\n' "$MIRRORS" > "$DAEMON_JSON"
        NEED_RESTART=true
        log "✅ 镜像加速已写入"
    else
        CURRENT=$(grep -o '"registry-mirrors"[^]]*]' "$DAEMON_JSON" 2>/dev/null || true)
        if [ "$CURRENT" != "\"registry-mirrors\": $MIRRORS" ]; then
            cp "$DAEMON_JSON" "${DAEMON_JSON}.bak"
            # 用 python 合并已有配置（保留其他字段），没有 python 则直接覆盖
            if command -v python3 &> /dev/null; then
                python3 -c "
import json
with open('$DAEMON_JSON') as f:
    try:
        cfg = json.load(f)
    except (json.JSONDecodeError, ValueError):
        cfg = {}
cfg['registry-mirrors'] = $MIRRORS
with open('$DAEMON_JSON', 'w') as f:
    json.dump(cfg, f, indent=2)
" 2>/dev/null || printf '{\n  "registry-mirrors": %s\n}\n' "$MIRRORS" > "$DAEMON_JSON"
            else
                printf '{\n  "registry-mirrors": %s\n}\n' "$MIRRORS" > "$DAEMON_JSON"
            fi
            NEED_RESTART=true
            log "✅ 镜像加速已更新"
        else
            log "✅ 镜像加速已是最新"
        fi
    fi
    if $NEED_RESTART; then
        log "重启 Docker 守护进程..."
        systemctl restart docker 2>/dev/null || service docker restart 2>/dev/null || true
        sleep 3
    fi
else
    log "✅ 跳过镜像加速（非中国大陆网络）"
fi

# ========================================
# 5. 预拉取基础镜像（加速构建）
# ========================================
log "预拉取基础镜像..."
# 只预拉取 Dockerfile 中直接引用的镜像（compose 服务镜像由 dc up 统一拉取）
if ! docker pull "python:3.13-slim" > /dev/null 2>&1; then
    warn "Python 基础镜像拉取失败，构建可能使用缓存或失败"
else
    log "  ✅ python:3.13-slim"
fi

# ========================================
# 6. 构建镜像（只构建一次！）
# ========================================
log "构建 Django 镜像（只构建一次，所有服务共享）..."
dc build web || fail "镜像构建失败"
log "✅ 镜像构建完成"

# ========================================
# 7. 启动基础服务 + 等待就绪
# ========================================
log "启动 MySQL + Redis..."
dc up -d db redis

log "等待 MySQL 就绪（最多60秒）..."
waited=0
while ! dc exec -T db mysqladmin ping -h localhost 2>/dev/null; do
    sleep 2
    waited=$((waited + 2))
    [ $waited -ge 60 ] && fail "MySQL 启动超时"
    printf "."
done
echo ""
log "✅ MySQL 就绪"

# ========================================
# 8. 启动全部服务
# ========================================
# web 容器的 entrypoint.sh 会自动执行 migrate + collectstatic + compress
log "启动全部服务（web entrypoint 自动执行迁移）..."
dc up -d
log "✅ 服务已启动"

# 等待 web 就绪
log "等待 Web 服务就绪（最多60秒，含迁移时间）..."
WEB_PORT=$(grep WEB_PORT_EXPOSED "$ENV_FILE" | head -1 | cut -d= -f2)
WEB_PORT="${WEB_PORT:-8000}"
waited=0
while ! curl -sf http://localhost:${WEB_PORT}/healthz/ > /dev/null 2>&1; do
    sleep 2
    waited=$((waited + 2))
    [ $waited -ge 60 ] && { warn "Web 服务未就绪，检查日志: dc logs web"; break; }
    printf "."
done
echo ""
log "✅ Web 服务就绪"

# ========================================
# 9. 交互式创建管理员
# ========================================
echo ""
echo "============================================================"
echo " 创建管理员账户"
echo "============================================================"

HAS_ADMIN=$(dc exec -T web python -c "
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django; django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
print('yes' if User.objects.filter(is_superuser=True).exists() else 'no')
" 2>/dev/null || echo "unknown")

if [ "$HAS_ADMIN" = "yes" ]; then
    log "✅ 已有管理员账户，跳过创建"
elif [ "$HAS_ADMIN" = "no" ]; then
    read -p "用户名 [admin]: " ADMIN_USER
    ADMIN_USER="${ADMIN_USER:-admin}"
    read -p "邮箱 [admin@example.com]: " ADMIN_EMAIL
    ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
    while true; do
        read -s -p "密码: " ADMIN_PASS; echo ""
        read -s -p "确认密码: " ADMIN_PASS_CONFIRM; echo ""
        if [ "$ADMIN_PASS" = "$ADMIN_PASS_CONFIRM" ] && [ -n "$ADMIN_PASS" ]; then
            break
        fi
        echo "❌ 密码不匹配或为空，重试"
    done
    log "创建管理员..."
    # 使用 Django 管理命令创建，避免 shell 变量注入 Python 代码
    dc exec -T -e DJANGO_SETTINGS_MODULE=config.settings.production \
        -e DJANGO_SUPERUSER_PASSWORD="$ADMIN_PASS" \
        web python manage.py createsuperuser \
        --noinput --username "$ADMIN_USER" --email "$ADMIN_EMAIL" \
        2>/dev/null && log "✅ 管理员创建成功" || warn "创建失败，请手动: dc exec web python manage.py createsuperuser"
else
    warn "无法检测管理员状态，请手动: dc exec web python manage.py createsuperuser"
fi

# ========================================
# 10. 显示最终状态 + 宿主机 Nginx 配置提示
# ========================================
echo ""
echo "============================================================"
log "最终容器状态:"
dc ps

SERVER_IP=$(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || echo "your-server-ip")

echo ""
echo "============================================================"
echo " ✨ 部署完成！"
echo "============================================================"
echo ""
echo "  🌐 网站首页:  http://${SERVER_IP}"
echo "  🛠 管理后台:  http://${SERVER_IP}/admin/"
echo "  📊 Web 应用:  http://${SERVER_IP}:${WEB_PORT}"
echo ""
echo "  ⚠️  宿主机 Nginx 配置提示:"
echo "    请将 deploy/nginx.generic.conf 复制到宿主机 Nginx 配置目录"
echo "    cp deploy/nginx.generic.conf /etc/nginx/sites-available/djangoblog"
echo "    ln -s /etc/nginx/sites-available/djangoblog /etc/nginx/sites-enabled/"
echo "    nginx -t && nginx -s reload"
echo ""
echo "  常用命令:"
echo "    查看日志:   dc logs -f web"
echo "    停止服务:   dc down"
echo "    重启服务:   dc restart"
echo "    进入容器:   dc exec web /bin/bash"
echo "    查看状态:   dc ps"
echo ""
echo "  增量更新:  bash deploy/auto-deploy.sh update"
echo "============================================================"
# 部署完成，脚本自动退出（exit 0）
exit 0
