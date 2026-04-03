#!/usr/bin/env bash
# ========================================
# DjangoBlog 一键部署脚本 (Linux)
# 优化版：镜像只构建一次 + 断线续传 + 健康检查
# ========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ENV_FILE="$SCRIPT_DIR/.env"

# ===== 检查 .env =====
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: 缺少 $ENV_FILE"
    echo "请先复制配置: cp $ENV_FILE.example $ENV_FILE"
    exit 1
fi

export COMPOSE_PROJECT_NAME="djangoblog"
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# ===== 快捷命令 =====
dc() { docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"; }

# ===== 颜色输出 =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[$(date '+%H:%M:%S')] $*${NC}"; }
warn()  { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN: $*${NC}"; }
fail()  { echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $*${NC}"; exit 1; }

MODE="${1:-deploy}"

# ===== 用法 =====
usage() {
    echo -e "用法: $0 {deploy|update|start|stop|status|restart|clean|shell}"
    echo ""
    echo "  deploy    完整部署 (首次使用)"
    echo "  update    增量更新 (拉代码 -> 构建 -> 迁移 -> 重启)"
    echo "  start     启动全部服务"
    echo "  stop      停止全部服务"
    echo "  restart   重启全部服务"
    echo "  status    查看状态"
    echo "  clean     清理所有容器/镜像/卷"
    echo "  shell     进入 web 容器 Shell"
}

# ========================================
# 完整部署
# ========================================
do_deploy() {
    log "====== 完整部署 ======"

    # 1. 构建镜像
    log "Step 1/4: 构建 Django 镜像 (所有服务共享)"
    dc build web || fail "镜像构建失败"

    # 2. 启动依赖
    log "Step 2/4: 启动 MySQL + Redis"
    dc up -d db redis

    log "等待 MySQL 就绪 (最多60秒)..."
    local waited=0
    while ! dc exec -T db mysqladmin ping -h localhost 2>/dev/null; do
        sleep 2
        waited=$((waited + 2))
        if [ $waited -ge 60 ]; then
            fail "MySQL 启动超时"
        fi
        printf "."
    done
    echo ""
    log "MySQL 就绪!"

    # 3. 迁移
    log "Step 3/4: 运行数据库迁移"
    dc run --rm migrate || fail "迁移失败"

    # 4. 启动全部
    log "Step 4/4: 启动全部服务"
    dc up -d

    log ""
    log "====== 部署完成! ======"
    log "Web:   http://localhost:8000"
    log "Nginx: http://localhost"
    log ""
    log "服务状态:"
    dc ps
}

# ========================================
# 增量更新
# ========================================
do_update() {
    log "====== 增量更新 ======"

    # 拉最新代码
    local project_root="$(dirname "$SCRIPT_DIR")"
    if [ -d "$project_root/.git" ]; then
        log "拉取最新代码..."
        (cd "$project_root" && git pull) || warn "git pull 失败，跳过"
    fi

    # 只构建 web (其他服务共享同一镜像)
    log "构建新镜像 (只构建一次)..."
    dc build web

    # 运行迁移
    log "运行迁移..."
    dc run --rm migrate || warn "迁移有跳过项"

    # 重启使用新镜像的服务
    log "重启 web/celery 服务..."
    dc up -d --force-recreate web celery_worker celery_beat

    log ""
    log "====== 更新完成! ======"
    dc ps
}

# ========================================
# 启动
# ========================================
do_start() {
    log "启动全部服务..."
    dc up -d
    dc ps
}

# ========================================
# 停止
# ========================================
do_stop() {
    log "停止全部服务..."
    dc down
    log "已停止"
}

# ========================================
# 重启
# ========================================
do_restart() {
    log "重启全部服务..."
    dc restart
    sleep 2
    dc ps
}

# ========================================
# 状态
# ========================================
do_status() {
    log "====== 服务状态 ======"
    dc ps

    log ""
    log "====== DjangoBlog 镜像 ======"
    docker images | grep djangoblog || echo "  (无)"

    log ""
    log "====== 数据卷 ======"
    docker volume ls | grep djangoblog || echo "  (无)"

    log ""
    log "====== Docker 磁盘使用 ======"
    docker system df
}

# ========================================
# 清理
# ========================================
do_clean() {
    echo -e "${RED}警告: 此操作将删除所有容器、镜像和数据库卷!${NC}"
    read -p "确认? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log "取消清理"
        return
    fi

    log "清理中..."
    dc down -v --rmi all
    docker system prune -f
    log "清理完成"
}

# ========================================
# Shell
# ========================================
do_shell() {
    log "进入 web 容器..."
    dc exec web /bin/bash
}

# ===== 分发 =====
case "$MODE" in
    deploy)  do_deploy  ;;
    update)  do_update  ;;
    start)   do_start   ;;
    stop)    do_stop    ;;
    restart) do_restart ;;
    status)  do_status  ;;
    clean)   do_clean   ;;
    shell)   do_shell   ;;
    --help)  usage      ;;
    *)
        warn "未知模式: $MODE"
        usage
        exit 1
        ;;
esac
