#!/bin/bash
# ========================================
# DjangoBlog 数据库备份脚本
# ========================================
# 功能：
#   1. MySQL 数据库备份
#   2. 压缩备份文件
#   3. 保留最近 N 天备份
#   4. 支持手动和自动备份
#   5. 备份验证
#   6. 日志记录
# ========================================

set -e  # 遇到错误立即退出

# ========================================
# 配置参数
# ========================================

# 备份目录
BACKUP_DIR="/mnt/f/DjangoBlog/deploy/backups"
LOG_DIR="/mnt/f/DjangoBlog/deploy/logs"
LOG_FILE="${LOG_DIR}/backup_$(date +%Y%m%d_%H%M%S).log"

# 数据库配置（从环境变量读取）
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-djangoblog}"
DB_USER="${DB_USER:-djangouser}"
DB_PASSWORD="${DB_PASSWORD:-djangopassword123}"

# 备份配置
RETENTION_DAYS=7  # 保留最近 7 天备份
COMPRESS=true     # 是否压缩
VERIFY=true       # 是否验证备份

# Docker 配置
DOCKER_CONTAINER="djangoblog-db"

# ========================================
# 函数定义
# ========================================

# 日志函数
log() {
    local level=$1
    shift
    local message=$*
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

# 检查 Docker 容器是否运行
check_container() {
    if ! docker ps | grep -q "${DOCKER_CONTAINER}"; then
        log "ERROR" "Docker 容器 ${DOCKER_CONTAINER} 未运行"
        return 1
    fi
    log "INFO" "Docker 容器 ${DOCKER_CONTAINER} 运行正常"
    return 0
}

# 创建备份目录
create_backup_dir() {
    if [ ! -d "${BACKUP_DIR}" ]; then
        mkdir -p "${BACKUP_DIR}"
        log "INFO" "创建备份目录: ${BACKUP_DIR}"
    fi
    
    if [ ! -d "${LOG_DIR}" ]; then
        mkdir -p "${LOG_DIR}"
        log "INFO" "创建日志目录: ${LOG_DIR}"
    fi
}

# 执行 MySQL 备份
backup_mysql() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/djangoblog_${timestamp}.sql"
    
    log "INFO" "开始备份数据库: ${DB_NAME}"
    log "INFO" "备份文件: ${backup_file}"
    
    # 使用 Docker exec 执行 mysqldump
    docker exec "${DOCKER_CONTAINER}" mysqldump \
        -u "${DB_USER}" \
        -p"${DB_PASSWORD}" \
        -h localhost \
        -P "${DB_PORT}" \
        --single-transaction \
        --routines \
        --triggers \
        --add-drop-database \
        --databases "${DB_NAME}" > "${backup_file}" 2>> "${LOG_FILE}"
    
    if [ $? -eq 0 ]; then
        log "INFO" "数据库备份成功"
        
        # 获取备份文件大小
        local file_size=$(du -h "${backup_file}" | cut -f1)
        log "INFO" "备份文件大小: ${file_size}"
        
        # 压缩备份文件
        if [ "${COMPRESS}" = true ]; then
            compress_backup "${backup_file}"
        fi
        
        return 0
    else
        log "ERROR" "数据库备份失败"
        return 1
    fi
}

# 压缩备份文件
compress_backup() {
    local backup_file=$1
    local compressed_file="${backup_file}.gz"
    
    log "INFO" "压缩备份文件: ${backup_file}"
    
    gzip -f "${backup_file}"
    
    if [ $? -eq 0 ]; then
        log "INFO" "压缩完成: ${compressed_file}"
        
        # 获取压缩后文件大小
        local compressed_size=$(du -h "${compressed_file}" | cut -f1)
        log "INFO" "压缩后大小: ${compressed_size}"
        
        return 0
    else
        log "ERROR" "压缩失败"
        return 1
    fi
}

# 验证备份文件
verify_backup() {
    local backup_file=$1
    
    if [ "${VERIFY}" != true ]; then
        return 0
    fi
    
    log "INFO" "验证备份文件: ${backup_file}"
    
    # 检查文件是否存在
    if [ ! -f "${backup_file}" ]; then
        log "ERROR" "备份文件不存在: ${backup_file}"
        return 1
    fi
    
    # 检查文件大小
    local file_size=$(stat -c%s "${backup_file}")
    if [ "${file_size}" -lt 1024 ]; then
        log "ERROR" "备份文件过小，可能损坏: ${backup_file}"
        return 1
    fi
    
    # 如果是压缩文件，检查是否可以解压
    if [[ "${backup_file}" == *.gz ]]; then
        if ! gzip -t "${backup_file}" 2>/dev/null; then
            log "ERROR" "压缩文件损坏: ${backup_file}"
            return 1
        fi
    fi
    
    log "INFO" "备份文件验证通过"
    return 0
}

# 清理旧备份
cleanup_old_backups() {
    log "INFO" "清理 ${RETENTION_DAYS} 天前的备份"
    
    # 查找并删除旧备份
    find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete 2>> "${LOG_FILE}"
    
    local deleted_count=$(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f -mtime +${RETENTION_DAYS} | wc -l)
    
    if [ ${deleted_count} -gt 0 ]; then
        log "INFO" "已删除 ${deleted_count} 个旧备份"
    else
        log "INFO" "无需清理旧备份"
    fi
}

# 生成备份报告
generate_report() {
    log "INFO" "生成备份报告"
    
    local total_backups=$(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f | wc -l)
    local total_size=$(du -sh "${BACKUP_DIR}" | cut -f1)
    local latest_backup=$(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    echo ""
    echo "=========================================="
    echo "📊 数据库备份报告"
    echo "=========================================="
    echo "备份目录: ${BACKUP_DIR}"
    echo "备份总数: ${total_backups}"
    echo "总大小: ${total_size}"
    echo "最新备份: ${latest_backup}"
    echo "保留天数: ${RETENTION_DAYS}"
    echo "=========================================="
    echo ""
}

# 发送通知（可选）
send_notification() {
    local status=$1
    local message=$2
    
    # 这里可以添加发送邮件、Slack、微信等通知
    # 例如：
    # curl -X POST -H 'Content-type: application/json' --data "{\"text\":\"${message}\"}" ${SLACK_WEBHOOK_URL}
    
    log "INFO" "通知: [${status}] ${message}"
}

# ========================================
# 主函数
# ========================================

main() {
    local start_time=$(date +%s)
    
    echo "=========================================="
    echo "🚀 DjangoBlog 数据库备份开始"
    echo "=========================================="
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "数据库: ${DB_NAME}"
    echo "备份目录: ${BACKUP_DIR}"
    echo ""
    
    # 记录开始时间
    log "INFO" "========== 备份开始 =========="
    
    # 1. 创建备份目录
    create_backup_dir
    
    # 2. 检查 Docker 容器
    if ! check_container; then
        send_notification "ERROR" "Docker 容器未运行，备份失败"
        exit 1
    fi
    
    # 3. 执行备份
    if ! backup_mysql; then
        send_notification "ERROR" "数据库备份失败"
        exit 1
    fi
    
    # 4. 验证备份
    local latest_backup=$(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    if ! verify_backup "${latest_backup}"; then
        send_notification "ERROR" "备份验证失败"
        exit 1
    fi
    
    # 5. 清理旧备份
    cleanup_old_backups
    
    # 6. 生成报告
    generate_report
    
    # 计算耗时
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "INFO" "备份完成，耗时: ${duration} 秒"
    log "INFO" "========== 备份结束 =========="
    
    # 发送成功通知
    send_notification "SUCCESS" "数据库备份成功，耗时 ${duration} 秒"
    
    echo "=========================================="
    echo "✅ 数据库备份完成！"
    echo "=========================================="
    echo "耗时: ${duration} 秒"
    echo ""
}

# ========================================
# 命令行参数处理
# ========================================

case "${1:-}" in
    --help|-h)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h     显示帮助信息"
        echo "  --verify       仅验证备份文件"
        echo "  --cleanup      仅清理旧备份"
        echo "  --report       仅生成备份报告"
        echo "  --no-compress  不压缩备份文件"
        echo "  --no-verify    不验证备份文件"
        echo ""
        echo "示例:"
        echo "  $0              # 执行完整备份"
        echo "  $0 --verify     # 验证备份文件"
        echo "  $0 --cleanup    # 清理旧备份"
        echo ""
        exit 0
        ;;
    --verify)
        # 仅验证备份文件
        latest_backup=$(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        if [ -n "${latest_backup}" ]; then
            verify_backup "${latest_backup}"
        else
            echo "未找到备份文件"
            exit 1
        fi
        exit 0
        ;;
    --cleanup)
        # 仅清理旧备份
        cleanup_old_backups
        exit 0
        ;;
    --report)
        # 仅生成备份报告
        generate_report
        exit 0
        ;;
    --no-compress)
        COMPRESS=false
        ;;
    --no-verify)
        VERIFY=false
        ;;
esac

# 执行主函数
main "$@"
