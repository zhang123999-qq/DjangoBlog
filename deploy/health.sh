#!/usr/bin/env bash
# ========================================
# DjangoBlog 健康检查与维护脚本 (Linux)
# ========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: 缺少 $ENV_FILE"
    exit 1
fi

export COMPOSE_PROJECT_NAME="djangoblog"

ACTION="${1:-check}"

# ===== 快捷命令 =====
dc() { docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"; }

# ===== 颜色 =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[$(date '+%H:%M:%S')] $*${NC}"; }
warn()  { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN: $*${NC}"; }

# ===== 健康检查 =====
do_check() {
    log "====== 健康检查 ======"

    local all_healthy=true
    for svc in db redis web celery_worker celery_beat nginx; do
        local state="unknown"
        # 兼容不同 Docker Compose 版本的输出格式
        state=$(dc ps "$svc" --format '{{.Status}}' 2>/dev/null || echo "not found")

        if echo "$state" | grep -qi "healthy"; then
            echo -e "  ${GREEN}$svc : 运行中 (healthy)${NC}"
        elif echo "$state" | grep -qi "running"; then
            echo -e "  ${GREEN}$svc : 运行中${NC}"
        elif echo "$state" | grep -qi "up"; then
            echo -e "  ${GREEN}$svc : 运行中${NC}"
        elif echo "$state" | grep -qi "completed"; then
            echo -e "  ${YELLOW}$svc : 已完成 (一次性任务)${NC}"
        elif echo "$state" != "not found"; then
            echo -e "  ${RED}$svc : $state - 异常!${NC}"
            all_healthy=false
        else
            echo -e "  ${RED}$svc : 未找到${NC}"
            all_healthy=false
        fi
    done

    log ""
    log "====== 完整状态 ======"
    dc ps 2>/dev/null || echo "无法获取容器状态"

    log ""
    if [ "$all_healthy" = true ]; then
        log "所有服务运行正常!"
    else
        warn "部分服务异常，建议: ./deploy.sh restart"
    fi
}

# ===== 日志查看 =====
do_logs() {
    dc logs --tail=100 -f
}

do_logs_web() {
    dc logs --tail=100 -f web
}

do_logs_db() {
    dc logs --tail=100 -f db
}

do_logs_redis() {
    dc logs --tail=100 -f redis
}

do_logs_celery() {
    log "=== Celery Worker ==="
    dc logs --tail=50 celery_worker
    log ""
    log "=== Celery Beat ==="
    dc logs --tail=50 celery_beat
}

do_logs_nginx() {
    dc logs --tail=100 -f nginx
}

# ===== 系统信息 =====
do_info() {
    log "====== 数据卷 ======"
    dc volume ls 2>/dev/null || docker volume ls | grep djangoblog || echo "  (无)"

    log ""
    log "====== 磁盘使用 ======"
    docker system df | grep -iE "NAME|djangoblog" || echo "  (无)"

    log ""
    log "====== 容器资源 ======"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | \
        grep -i djangoblog || echo "  (无)"
}

# ===== 数据库备份 =====
do_backup() {
    local backup_dir="/tmp/djangoblog_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    local db_pass="$(grep DB_ROOT_PASSWORD "$ENV_FILE" | head -1 | cut -d'=' -f2- | tr -d '[:space:]')"
    db_pass="${db_pass:-rootpassword123}"
    local db_name="$(grep DB_NAME "$ENV_FILE" | head -1 | cut -d'=' -f2- | tr -d '[:space:]')"
    db_name="${db_name:-djangoblog}"

    log "开始数据库备份..."
    docker compose exec -T db mysqldump \
        -u root \
        -p"${db_pass}" \
        "${db_name}" 2>/dev/null | \
        gzip > "$backup_dir/djangoblog.sql.gz"

    if [ $? -eq 0 ]; then
        log "备份完成: $backup_dir/djangoblog.sql.gz"
        ls -lh "$backup_dir/djangoblog.sql.gz"
    else
        echo -e "${RED}备份失败${NC}"
    fi
}

# ===== 分发 =====
case "$ACTION" in
    check)        do_check        ;;
    logs)         do_logs         ;;
    logs-web)     do_logs_web     ;;
    logs-db)      do_logs_db      ;;
    logs-redis)   do_logs_redis   ;;
    logs-celery)  do_logs_celery  ;;
    logs-nginx)   do_logs_nginx   ;;
    info)         do_info         ;;
    backup)       do_backup       ;;
    *)
        echo "用法: $0 {check|logs|logs-web|logs-db|logs-redis|logs-celery|logs-nginx|info|backup}"
        exit 1
        ;;
esac
