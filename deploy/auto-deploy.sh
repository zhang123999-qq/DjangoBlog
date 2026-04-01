#!/bin/bash
# =============================================
# DjangoBlog 一键自动部署脚本
# 使用方法: bash deploy/auto-deploy.sh
# 功能: 自动生成 .env、配置镜像加速、构建镜像、拉起全部服务
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
    
    # 检测是否在中国大陆（简单判断）
    local IS_CHINA=false
    if curl -s --connect-timeout 3 "https://www.baidu.com" > /dev/null 2>&1; then
        IS_CHINA=true
    fi
    
    if [ "$IS_CHINA" = true ]; then
        echo "   检测到中国大陆网络环境，配置镜像加速..."
        
        # Docker daemon 配置文件
        DAEMON_JSON="/etc/docker/daemon.json"
        
        # 国内镜像源列表（2024年可用）
        MIRRORS='["https://docker.1ms.run","https://docker.xuanyuan.me"]'
        
        if [ -f "$DAEMON_JSON" ]; then
            # 检查是否已配置镜像
            if grep -q "registry-mirrors" "$DAEMON_JSON"; then
                echo "   ✅ 镜像加速已配置"
            else
                echo "   更新现有 Docker 配置..."
                cp "$DAEMON_JSON" "${DAEMON_JSON}.bak"
                echo "{\"registry-mirrors\": $MIRRORS}" > "$DAEMON_JSON"
                echo "   ✅ 镜像加速配置完成"
                echo "   🔄 重启 Docker 服务..."
                systemctl restart docker 2>/dev/null || service docker restart 2>/dev/null || true
                sleep 3
            fi
        else
            echo "   创建 Docker 配置文件..."
            mkdir -p /etc/docker
            echo "{\"registry-mirrors\": $MIRRORS}" > "$DAEMON_JSON"
            echo "   ✅ 镜像加速配置完成"
            echo "   🔄 重启 Docker 服务..."
            systemctl restart docker 2>/dev/null || service docker restart 2>/dev/null || true
            sleep 3
        fi
    else
        echo "   跳过镜像加速配置（非中国大陆网络）"
    fi
}

# ----------------------------------------
# 2. 自动生成 .env（如果不存在或强制重新生成）
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

# --- 安全配置（纯 HTTP 模式，有 SSL 后再改为 True）---
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# --- API 配置 ---
API_PAGE_SIZE=20
API_ANON_RATE=100/hour
API_USER_RATE=1000/hour
API_UPLOAD_RATE=30/hour
API_READ_RATE=1200/hour

# --- 百度内容审核（可选，有key再填）---
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
# 3. 创建日志和数据目录
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
# 6. 拉取基础镜像（使用国内镜像源加速）
# ----------------------------------------
echo ""
echo "📦 预拉取基础镜像..."
echo "   这将使用国内镜像源加速下载..."

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
            echo "   尝试镜像源: $mirror"
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
# 9. 数据库迁移
# ----------------------------------------
echo ""
echo "📊 执行数据库迁移..."

# 清理旧的 migrate 容器
if docker ps -a --format '{{.Names}}' | grep -q 'djangoblog-migrate'; then
    echo "   清理旧的迁移容器..."
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" rm -f migrate 2>/dev/null || true
fi

# 执行迁移
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up migrate --renew-anon-volumes 2>/dev/null || {
    echo "   ⚠️ migrate 服务失败，尝试手动迁移..."
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python manage.py migrate 2>/dev/null || {
        echo "   等待数据库就绪后重试..."
        sleep 10
        docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T web python manage.py migrate
    }
}
echo "✅ 数据库迁移完成"

# ----------------------------------------
# 10. 显示容器状态
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
echo "  📝 创建管理员账户:"
echo "     docker compose --env-file deploy/.env -f deploy/docker-compose.yml exec web python manage.py createsuperuser"
echo ""
echo "  常用命令:"
echo "    查看日志:   docker compose -f deploy/docker-compose.yml logs -f"
echo "    停止服务:   docker compose -f deploy/docker-compose.yml down"
echo "    重启服务:   docker compose -f deploy/docker-compose.yml restart"
echo "    进入容器:   docker exec -it djangoblog-web bash"
echo ""
echo "============================================================"
cd "$CD_DIR"
