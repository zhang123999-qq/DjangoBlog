#!/bin/bash
# =============================================
# DjangoBlog 一键自动部署脚本
# 使用方法: bash deploy/auto-deploy.sh
# 功能: 自动生成 .env、配置镜像加速、构建镜像、拉起全部服务、数据库迁移、创建管理员
# =============================================

set -e

# 项目目录（自动检测当前目录）
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
CD_DIR=$(pwd)
cd "$PROJECT_DIR"

# .env 文件位置（在 deploy 目录下）
ENV_FILE="$PROJECT_DIR/deploy/.env"
COMPOSE_FILE="$PROJECT_DIR/deploy/docker-compose.yml"

echo "============================================================"
echo " DjangoBlog 一键自动部署"
echo " 项目路径: $PROJECT_DIR"
echo "============================================================"

# ----------------------------------------
# 1. 配置 Docker 镜像加速（中国大陆服务器）
# ----------------------------------------
configure_docker_mirror() {
    echo ""
    echo "🚀 配置 Docker 镜像加速..."
    
    local IS_CHINA=false
    if curl -s --connect-timeout 3 "https://www.baidu.com" > /dev/null 2>&1; then
        IS_CHINA=true
    fi
    
    if [ "$IS_CHINA" = true ]; then
        echo "   检测到中国大陆网络环境，配置镜像加速..."
        
        DAEMON_JSON="/etc/docker/daemon.json"
        MIRRORS='["https://docker.1ms.run","https://docker.xuanyuan.me"]'
        
        if [ -f "$DAEMON_JSON" ]; then
            if grep -q "registry-mirrors" "$DAEMON_JSON"; then
                echo "   ✅ 镜像加速已配置"
            else
                cp "$DAEMON_JSON" "${DAEMON_JSON}.bak"
                echo "{\"registry-mirrors\": $MIRRORS}" > "$DAEMON_JSON"
                echo "   ✅ 镜像加速配置完成"
                systemctl restart docker 2>/dev/null || service docker restart 2>/dev/null || true
                sleep 3
            fi
        else
            mkdir -p /etc/docker
            echo "{\"registry-mirrors\": $MIRRORS}" > "$DAEMON_JSON"
            echo "   ✅ 镜像加速配置完成"
            systemctl restart docker 2>/dev/null || service docker restart 2>/dev/null || true
            sleep 3
        fi
    else
        echo "   跳过镜像加速配置（非中国大陆网络）"
    fi
}

# ----------------------------------------
# 2. 自动生成 .env
# ----------------------------------------
if [ -f "$ENV_FILE" ]; then
    echo ""
    echo "✅ .env 文件已存在，将使用现有配置"
    echo "   如需重新生成，请先执行: rm deploy/.env"
else
    echo ""
    echo "🔧 自动生成 .env 配置文件..."

    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 40)

    cat > "$ENV_FILE" << EOF
# =============================================
# Django 配置（自动生成于 $(date '+%Y-%m-%d %H:%M:%S')）
# =============================================

# --- 安全配置 ---
DEBUG=False
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=*,127.0.0.1,localhost

# --- MySQL ---
DB_ENGINE=django.db.backends.mysql
DB_NAME=djangoblog
DB_USER=djangouser
DB_PASSWORD=djangopassword
DB_HOST=db
DB_PORT=3306
DB_ROOT_PASSWORD=rootpassword

# --- Redis ---
USE_REDIS=True
REDIS_URL=redis://redis:6379/1

# --- Celery ---
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# --- 端口 ---
DB_PORT_EXPOSED=3306
REDIS_PORT_EXPOSED=6379
WEB_PORT_EXPOSED=8000
NGINX_PORT_EXPOSED=80
NGINX_HTTPS_PORT_EXPOSED=443

# --- CSRF ---
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1

# --- 安全配置 ---
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# --- API 配置 ---
API_PAGE_SIZE=20
API_ANON_RATE=100/hour
API_USER_RATE=1000/hour
API_UPLOAD_RATE=30/hour
API_READ_RATE=1200/hour

# --- 百度内容审核 ---
BAIDU_APP_ID=
BAIDU_API_KEY=
BAIDU_SECRET_KEY=
MODERATION_MODE=auto
EOF

    echo "✅ .env 配置文件已自动生成"
fi

echo ""
echo "🔍 检查 SECRET_KEY..."
if grep -q "SECRET_KEY=.*your-secret" "$ENV_FILE" 2>/dev/null || ! grep -q "SECRET_KEY=.\+" "$ENV_FILE" 2>/dev/null; then
    echo "⚠️  SECRET_KEY 未设置，重新生成..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 40)
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|g" "$ENV_FILE" 2>/dev/null || sed -i "" "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|g" "$ENV_FILE"
    echo "✅ SECRET_KEY 已重新生成"
fi
echo "✅ SECRET_KEY 检查通过"

# ----------------------------------------
# 3. 创建数据目录
# ----------------------------------------
echo ""
echo "📁 创建数据目录..."
mkdir -p "$PROJECT_DIR/deploy/logs" "$PROJECT_DIR/deploy/nginx" "$PROJECT_DIR/deploy/nginx/ssl"
echo "✅ 数据目录就绪"

# ----------------------------------------
# 4. 检查 Docker 环境
# ----------------------------------------
echo ""
echo "🐳 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi
echo "✅ Docker 环境就绪 ($(docker compose version 2>/dev/null || echo 'unknown'))"

# ----------------------------------------
# 5. 配置镜像加速
# ----------------------------------------
configure_docker_mirror

# ----------------------------------------
# 6. 拉取基础镜像
# ----------------------------------------
echo ""
echo "📦 预拉取基础镜像..."

BASE_IMAGES=(
    "python:3.13-slim"
    "mysql:8.0"
    "redis:7-alpine"
    "nginx:1.25-alpine"
)

for image in "${BASE_IMAGES[@]}"; do
    echo "   拉取 $image ..."
    if docker pull "$image" 2>/dev/null; then
        echo "   ✅ $image 拉取成功"
    else
        echo "   ⚠️  直接拉取失败，尝试镜像源..."
        for mirror in "docker.1ms.run" "docker.xuanyuan.me"; do
            if docker pull "$mirror/$image" 2>/dev/null; then
                docker tag "$mirror/$image" "$image"
                docker rmi "$mirror/$image" 2>/dev/null || true
                echo "   ✅ $image 拉取成功"
                break
            fi
        done
    fi
done
echo "✅ 基础镜像准备完成"

# ----------------------------------------
# 7. 构建镜像
# ----------------------------------------
echo ""
echo "🔨 构建应用镜像..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
echo "✅ 镜像构建完成"

# ----------------------------------------
# 8. 启动所有服务
# ----------------------------------------
echo ""
echo "🚀 启动所有服务..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
echo "✅ 服务启动中，等待数据库就绪..."
sleep 15

# ----------------------------------------
# 9. 自动执行数据库迁移
# ----------------------------------------
echo ""
echo "📊 执行数据库迁移..."

# 清理旧的 migrate 容器
if docker ps -a --format '{{.Names}}' | grep -q 'djangoblog-migrate'; then
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" rm -f migrate 2>/dev/null || true
fi

# 执行迁移（带重试）
MIGRATE_SUCCESS=false
for i in 1 2 3; do
    echo "   尝试迁移 (第 $i 次)..."
    if docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python manage.py migrate 2>/dev/null; then
        MIGRATE_SUCCESS=true
        break
    fi
    echo "   等待数据库就绪..."
    sleep 5
done

if [ "$MIGRATE_SUCCESS" = true ]; then
    echo "✅ 数据库迁移完成"
else
    echo "❌ 数据库迁移失败，请手动执行:"
    echo "   docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec web python manage.py migrate"
fi

# ----------------------------------------
# 10. 交互式创建管理员账户
# ----------------------------------------
echo ""
echo "👤 创建管理员账户"
echo "------------------------------------------------------------"

# 检查是否已有管理员
HAS_ADMIN=$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
print('yes' if User.objects.filter(is_superuser=True).exists() else 'no')
" 2>/dev/null || echo "unknown")

if [ "$HAS_ADMIN" = "yes" ]; then
    echo "✅ 检测到已有管理员账户，跳过创建"
elif [ "$HAS_ADMIN" = "no" ]; then
    echo "请输入管理员账户信息:"
    echo ""
    
    # 交互式输入
    read -p "用户名 [admin]: " ADMIN_USER
    ADMIN_USER=${ADMIN_USER:-admin}
    
    read -p "邮箱 [admin@example.com]: " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
    
    while true; do
        read -s -p "密码: " ADMIN_PASS
        echo ""
        read -s -p "确认密码: " ADMIN_PASS_CONFIRM
        echo ""
        
        if [ "$ADMIN_PASS" = "$ADMIN_PASS_CONFIRM" ] && [ -n "$ADMIN_PASS" ]; then
            break
        fi
        echo "❌ 密码不匹配或为空，请重新输入"
    done
    
    echo ""
    echo "正在创建管理员账户..."
    
    # 创建管理员
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('$ADMIN_USER', '$ADMIN_EMAIL', '$ADMIN_PASS')
print('管理员账户创建成功!')
" 2>/dev/null && echo "✅ 管理员账户创建成功" || echo "❌ 创建失败，请手动创建"
else
    echo "⚠️  无法检测管理员状态，请手动创建:"
    echo "   docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec web python manage.py createsuperuser"
fi

# ----------------------------------------
# 11. 显示容器状态和访问信息
# ----------------------------------------
echo ""
echo "------------------------------------------------------------"
echo "📋 容器状态:"
echo "------------------------------------------------------------"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

# 获取访问地址
SERVER_IP=$(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || curl -s --connect-timeout 5 ip.sb 2>/dev/null || echo "your-server-ip")

echo ""
echo "============================================================"
echo " ✨ 部署完成！"
echo "============================================================"
echo ""
echo "  🌐 网站首页:  http://${SERVER_IP}"
echo "  🛠 管理后台:  http://${SERVER_IP}/admin/"
echo "  📊 Web 应用:  http://${SERVER_IP}:8000"
echo ""
echo "  常用命令:"
echo "    查看日志:   docker compose -f deploy/docker-compose.yml logs -f"
echo "    停止服务:   docker compose -f deploy/docker-compose.yml down"
echo "    重启服务:   docker compose -f deploy/docker-compose.yml restart"
echo "    进入容器:   docker exec -it djangoblog-web bash"
echo ""
echo "============================================================"
cd "$CD_DIR"
