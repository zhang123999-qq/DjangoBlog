#!/usr/bin/env bash
# =============================================
# Nginx 配置自动安装脚本
# 使用方法: sudo bash deploy/install_nginx.sh [frontend|bt|generic]
# 默认: generic（通用宿主机）
# =============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MODE="${1:-generic}"

NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
SITE_NAME="djangoblog"

case "$MODE" in
    frontend)
        SRC_CONF="$PROJECT_DIR/deploy/nginx.frontend.conf"
        ;;
    bt)
        SRC_CONF="$PROJECT_DIR/deploy/nginx.conf"
        DEST="/www/server/panel/vhost/nginx/DjangoBlog.conf"
        if [ -d "/www/server/panel/vhost/nginx" ]; then
            echo "[nginx-bt] 安装宝塔面板配置到 $DEST"
            cp "$SRC_CONF" "$DEST"
            /etc/init.d/nginx reload || nginx -s reload
            echo "✅ 宝塔 Nginx 配置已安装"
            exit 0
        else
            echo "❌ 宝塔面板未安装，回退到 generic 模式"
            SRC_CONF="$PROJECT_DIR/deploy/nginx.generic.conf"
        fi
        ;;
    generic|*)
        SRC_CONF="$PROJECT_DIR/deploy/nginx.generic.conf"
        ;;
esac

# 检查 Nginx 是否安装
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx 未安装，请先: apt install nginx"
    exit 1
fi

DEST="$NGINX_AVAILABLE/$SITE_NAME"
echo "[nginx] 复制配置 $SRC_CONF → $DEST"
cp "$SRC_CONF" "$DEST"

if [ ! -L "$NGINX_ENABLED/$SITE_NAME" ]; then
    echo "[nginx] 启用站点"
    ln -sf "$DEST" "$NGINX_ENABLED/$SITE_NAME"
fi

# 移除 default
if [ -L "$NGINX_ENABLED/default" ]; then
    rm -f "$NGINX_ENABLED/default"
fi

# 测试 + reload
if nginx -t; then
    nginx -s reload || systemctl reload nginx
    echo "✅ Nginx 已配置并 reload"
else
    echo "❌ Nginx 配置测试失败，请检查 $DEST"
    exit 1
fi
