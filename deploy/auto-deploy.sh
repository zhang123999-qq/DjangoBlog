#!/bin/bash
# =============================================
# DjangoBlog 一键自动部署脚本
# 使用方法: bash deploy/auto-deploy.sh
# 功能: 自动生成 .env、构建镜像、拉起全部服务
# =============================================

set -e

# 项目目录（自动检测当前目录）
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
CD_DIR=$(pwd)
cd "$PROJECT_DIR"

echo "============================================================"
echo " DjangoBlog 一键自动部署"
echo " 项目路径: $PROJECT_DIR"
echo "============================================================"

# ----------------------------------------
# 1. 自动生成 .env（如果不存在或强制重新生成）
# ----------------------------------------
ENV_FILE="$PROJECT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    echo ""
    echo "✅ .env 文件已存在，将使用现有配置"
    echo "   如需重新生成，请先执行: rm .env"
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
CSRF_TRUSTED_ORIGINS=http://localhost:80,http://127.0.0.1:80

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
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|g" "$ENV_FILE" || sed -i "" "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|g" "$ENV_FILE"
    echo "✅ SECRET_KEY 已重新生成"
fi
echo "✅ SECRET_KEY 检查通过"

# ----------------------------------------
# 2. 创建日志和数据目录
# ----------------------------------------
echo ""
echo "📁 创建数据目录..."
mkdir -p "$PROJECT_DIR/deploy/logs" "$PROJECT_DIR/deploy/nginx" "$PROJECT_DIR/deploy/nginx/ssl"
echo "✅ 数据目录就绪"

# ----------------------------------------
# 3. 检查 Docker 环境
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
# 4. 构建镜像
# ----------------------------------------
echo ""
echo "🔨 构建镜像..."
docker compose --env-file "$ENV_FILE" -f deploy/docker-compose.yml build
echo "✅ 镜像构建完成"

# ----------------------------------------
# 5. 启动所有服务
# ----------------------------------------
echo ""
echo "🚀 启动所有服务..."
docker compose --env-file "$ENV_FILE" -f deploy/docker-compose.yml up -d
echo "✅ 服务启动中，等待 10 秒..."
sleep 10

# 6. 数据库迁移（处理旧容器）
echo ""
echo "📊 执行数据库迁移..."

# 检查是否有旧的 migrate 容器残留
if docker ps -a --format '{{.Names}}' | grep -q 'djangoblog-migrate'; then
    echo "   发现旧的迁移容器，清理中..."
    docker compose --env-file "$ENV_FILE" -f deploy/docker-compose.yml rm -f migrate 2>/dev/null || true
fi

# 启动 migrate 服务（完成即退出）
docker compose --env-file "$ENV_FILE" -f deploy/docker-compose.yml up migrate --renew-anon-volumes
echo "✅ 数据库迁移完成"

# ----------------------------------------
# 7. 显示容器状态
# ----------------------------------------
echo ""
echo "------------------------------------------------------------"
echo "📋 容器状态:"
echo "------------------------------------------------------------"
docker compose --env-file "$ENV_FILE" -f deploy/docker-compose.yml ps

# 获取访问地址
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")
echo ""
echo "============================================================"
echo " ✨ 部署完成！"
echo "============================================================"
echo ""
echo "  🌐 网站首页:  http://${SERVER_IP}:80"
echo "  🛠 管理后台:  http://${SERVER_IP}/admin/"
echo "  📊 Web 应用:  http://${SERVER_IP}:8000"
echo ""
echo "  查看日志:     docker compose -f deploy/docker-compose.yml logs -f"
echo "  停止服务:     docker compose -f deploy/docker-compose.yml down"
echo "  重启服务:     docker compose -f deploy/docker-compose.yml restart"
echo ""
cd "$CD_DIR"
