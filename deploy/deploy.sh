#!/bin/bash
# DjangoBlog 服务器部署脚本
# 使用方法: bash deploy.sh

set -e

echo "============================================================"
echo " DjangoBlog 服务器部署脚本"
echo "============================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="/www/wwwroot/DjangoBlog"
cd $PROJECT_DIR

echo ""
echo -e "${YELLOW}[1/8] 拉取最新代码...${NC}"
git fetch --all
git reset --hard origin/main
echo -e "${GREEN}✓ 代码更新完成${NC}"

echo ""
echo -e "${YELLOW}[2/8] 创建 .env 配置文件...${NC}"
cat > .env << 'ENVEOF'
# Django 配置
DEBUG=True
SECRET_KEY=&oxraj24si7h%v45_-9o1fm#esm_4q-d7-&#8_okh4p*%#-763
ALLOWED_HOSTS=localhost,127.0.0.1,www.zhtest.top,zhtest.top,*
CSRF_TRUSTED_ORIGINS=https://www.zhtest.top,https://zhtest.top,http://www.zhtest.top,http://zhtest.top

# 网站信息
SITE_NAME=Django Blog
SITE_TITLE=Django 综合网站

# MySQL 数据库配置
DB_ENGINE=django.db.backends.mysql
DB_NAME=djangoblog
DB_USER=root
DB_PASSWORD=bdc196c909535d4c
DB_HOST=localhost
DB_PORT=3306

# Redis 配置
USE_REDIS=True
REDIS_URL=redis://localhost:6379/0

# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/3
ENVEOF
echo -e "${GREEN}✓ .env 配置完成${NC}"

echo ""
echo -e "${YELLOW}[3/8] 创建 MySQL 数据库...${NC}"
mysql -u root -pbdc196c909535d4c -e "CREATE DATABASE IF NOT EXISTS djangoblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || echo -e "${YELLOW}! 数据库可能已存在${NC}"
echo -e "${GREEN}✓ 数据库准备完成${NC}"

echo ""
echo -e "${YELLOW}[4/8] 激活虚拟环境...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ 虚拟环境已激活${NC}"

echo ""
echo -e "${YELLOW}[5/8] 删除旧数据库和安装锁...${NC}"
rm -f db.sqlite3 installed.lock
echo -e "${GREEN}✓ 清理完成${NC}"

echo ""
echo -e "${YELLOW}[6/8] 执行数据库迁移...${NC}"
python manage.py migrate --run-syncdb
echo -e "${GREEN}✓ 数据库迁移完成${NC}"

echo ""
echo -e "${YELLOW}[7/8] 创建管理员账户...${NC}"
echo "请输入管理员信息:"
python manage.py createsuperuser

echo ""
echo -e "${YELLOW}[8/8] 创建安装锁文件...${NC}"
touch installed.lock
echo -e "${GREEN}✓ 安装完成${NC}"

echo ""
echo "============================================================"
echo -e "${GREEN} 部署成功！${NC}"
echo "============================================================"
echo ""
echo "启动服务:"
echo "  source .venv/bin/activate"
echo "  gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 &"
echo ""
echo "访问地址:"
echo "  网站首页: https://www.zhtest.top/"
echo "  管理后台: https://www.zhtest.top/admin/"
echo ""
