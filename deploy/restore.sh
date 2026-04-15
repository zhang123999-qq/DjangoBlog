#!/bin/bash
# ========================================
# DjangoBlog 数据库恢复脚本
# ========================================
# 功能：
#   1. 从备份文件恢复数据库
#   2. 支持选择特定备份
#   3. 恢复前确认
#   4. 恢复后验证
#   5. 日志记录
# ========================================

set -e  # 遇到错误立即退出

# ========================================
# 配置参数
# ========================================

# 备份目录
BACKUP_DIR="/mnt/f/DjangoBlog/deploy/backups"
LOG_DIR="/mnt/f/DjangoBlog/deploy/logs"
LOG_FILE="${LOG_DIR}/restore_$(date +%Y%m%d_%H%M%S).log"

# 数据库配置（从环境变量读取）
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-djangoblog}"
DB_USER="${DB_USER:-djangouser}"
DB_PASSWORD="${DB_PASSWORD:-djangopassword123}"

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

# 列出可用备份
list_backups() {
    echo ""
    echo "=========================================="
    echo "📋 可用备份文件"
    echo "=========================================="
    
    local count=0
    while IFS= read -r file; do
        count=$((count + 1))
        local size=$(du -h "${file}" | cut -f1)
        local date=$(stat -c %y "${file}" | cut -d' ' -f1,2 | cut -d'.' -f1)
        local filename=$(basename "${file}")
        
        echo "${count}. ${filename}"
        echo "   大小: ${size}"
        echo "   时间: ${date}"
        echo ""
    done < <(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f -printf '%T@ %p\n' | sort -rn | cut -d' ' -f2-)
    
    if [ ${count} -eq 0 ]; then
        echo "未找到备份文件"
        return 1
    fi
    
    echo "总计: ${count} 个备份"
    echo ""
    return 0
}

# 选择备份文件
select_backup() {
    list_backups
    
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    local count=$(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f | wc -l)
    
    if [ ${count} -eq 1 ]; then
        SELECTED_BACKUP=$(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f | head -1)
        log "INFO" "自动选择唯一备份: ${SELECTED_BACKUP}"
        return 0
    fi
    
    echo "请选择要恢复的备份 (1-${count}): "
    read -r selection
    
    if ! [[ "${selection}" =~ ^[0-9]+$ ]] || [ "${selection}" -lt 1 ] || [ "${selection}" -gt ${count} ]; then
        log "ERROR" "无效选择: ${selection}"
        return 1
    fi
    
    SELECTED_BACKUP=$(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f -printf '%T@ %p\n' | sort -rn | sed -n "${selection}p" | cut -d' ' -f2-)
    
    if [ -z "${SELECTED_BACKUP}" ]; then
        log "ERROR" "未找到选择的备份"
        return 1
    fi
    
    log "INFO" "选择备份: ${SELECTED_BACKUP}"
    return 0
}

# 确认恢复
confirm_restore() {
    echo ""
    echo "⚠️  警告：恢复操作将覆盖当前数据库！"
    echo ""
    echo "数据库: ${DB_NAME}"
    echo "备份文件: $(basename ${SELECTED_BACKUP})"
    echo ""
    echo "请确认是否继续？(yes/no): "
    read -r confirmation
    
    if [ "${confirmation}" != "yes" ]; then
        log "INFO" "用户取消恢复操作"
        return 1
    fi
    
    log "INFO" "用户确认恢复操作"
    return 0
}

# 验证备份文件
verify_backup() {
    local backup_file=$1
    
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

# 解压备份文件
decompress_backup() {
    local backup_file=$1
    local temp_file="/tmp/djangoblog_restore_$$.sql"
    
    log "INFO" "解压备份文件: ${backup_file}"
    
    if [[ "${backup_file}" == *.gz ]]; then
        gunzip -c "${backup_file}" > "${temp_file}"
        
        if [ $? -eq 0 ]; then
            log "INFO" "解压完成: ${temp_file}"
            echo "${temp_file}"
            return 0
        else
            log "ERROR" "解压失败"
            return 1
        fi
    else
        # 不是压缩文件，直接返回原文件
        echo "${backup_file}"
        return 0
    fi
}

# 恢复数据库
restore_database() {
    local backup_file=$1
    
    log "INFO" "开始恢复数据库: ${DB_NAME}"
    log "INFO" "备份文件: ${backup_file}"
    
    # 解压备份文件
    local sql_file=$(decompress_backup "${backup_file}")
    
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # 使用 Docker exec 执行 mysql 恢复
    docker exec -i "${DOCKER_CONTAINER}" mysql \
        -u "${DB_USER}" \
        -p"${DB_PASSWORD}" \
        -h localhost \
        -P "${DB_PORT}" < "${sql_file}" 2>> "${LOG_FILE}"
    
    local restore_result=$?
    
    # 清理临时文件
    if [[ "${backup_file}" == *.gz ]] && [ -f "${sql_file}" ]; then
        rm -f "${sql_file}"
        log "INFO" "清理临时文件: ${sql_file}"
    fi
    
    if [ ${restore_result} -eq 0 ]; then
        log "INFO" "数据库恢复成功"
        return 0
    else
        log "ERROR" "数据库恢复失败"
        return 1
    fi
}

# 验证恢复结果
verify_restore() {
    log "INFO" "验证恢复结果"
    
    # 检查数据库连接
    docker exec "${DOCKER_CONTAINER}" mysql \
        -u "${DB_USER}" \
        -p"${DB_PASSWORD}" \
        -h localhost \
        -P "${DB_PORT}" \
        -e "USE ${DB_NAME}; SELECT COUNT(*) FROM django_migrations;" 2>> "${LOG_FILE}"
    
    if [ $? -eq 0 ]; then
        log "INFO" "数据库连接正常"
        
        # 检查表数量
        local table_count=$(docker exec "${DOCKER_CONTAINER}" mysql \
            -u "${DB_USER}" \
            -p"${DB_PASSWORD}" \
            -h localhost \
            -P "${DB_PORT}" \
            -e "USE ${DB_NAME}; SHOW TABLES;" 2>/dev/null | wc -l)
        
        log "INFO" "数据库表数量: $((table_count - 1))"
        
        return 0
    else
        log "ERROR" "数据库连接失败"
        return 1
    fi
}

# 发送通知（可选）
send_notification() {
    local status=$1
    local message=$2
    
    # 这里可以添加发送邮件、Slack、微信等通知
    log "INFO" "通知: [${status}] ${message}"
}

# ========================================
# 主函数
# ========================================

main() {
    local start_time=$(date +%s)
    
    echo "=========================================="
    echo "🔄 DjangoBlog 数据库恢复开始"
    echo "=========================================="
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "数据库: ${DB_NAME}"
    echo ""
    
    # 记录开始时间
    log "INFO" "========== 恢复开始 =========="
    
    # 1. 检查 Docker 容器
    if ! check_container; then
        send_notification "ERROR" "Docker 容器未运行，恢复失败"
        exit 1
    fi
    
    # 2. 选择备份文件
    if ! select_backup; then
        send_notification "ERROR" "选择备份文件失败"
        exit 1
    fi
    
    # 3. 验证备份文件
    if ! verify_backup "${SELECTED_BACKUP}"; then
        send_notification "ERROR" "备份文件验证失败"
        exit 1
    fi
    
    # 4. 确认恢复
    if ! confirm_restore; then
        exit 0
    fi
    
    # 5. 执行恢复
    if ! restore_database "${SELECTED_BACKUP}"; then
        send_notification "ERROR" "数据库恢复失败"
        exit 1
    fi
    
    # 6. 验证恢复结果
    if ! verify_restore; then
        send_notification "ERROR" "恢复验证失败"
        exit 1
    fi
    
    # 计算耗时
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "INFO" "恢复完成，耗时: ${duration} 秒"
    log "INFO" "========== 恢复结束 =========="
    
    # 发送成功通知
    send_notification "SUCCESS" "数据库恢复成功，耗时 ${duration} 秒"
    
    echo "=========================================="
    echo "✅ 数据库恢复完成！"
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
        echo "  --list         列出可用备份"
        echo "  --latest       恢复最新备份"
        echo "  --file FILE    恢复指定文件"
        echo ""
        echo "示例:"
        echo "  $0              # 交互式选择备份"
        echo "  $0 --list       # 列出可用备份"
        echo "  $0 --latest     # 恢复最新备份"
        echo "  $0 --file xxx.gz # 恢复指定文件"
        echo ""
        exit 0
        ;;
    --list)
        # 仅列出备份
        list_backups
        exit 0
        ;;
    --latest)
        # 恢复最新备份
        SELECTED_BACKUP=$(find "${BACKUP_DIR}" -name "djangoblog_*.sql.gz" -type f -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2-)
        if [ -z "${SELECTED_BACKUP}" ]; then
            echo "未找到备份文件"
            exit 1
        fi
        log "INFO" "选择最新备份: ${SELECTED_BACKUP}"
        ;;
    --file)
        # 恢复指定文件
        if [ -z "${2:-}" ]; then
            echo "错误: 请指定备份文件"
            exit 1
        fi
        SELECTED_BACKUP="${2}"
        if [ ! -f "${SELECTED_BACKUP}" ]; then
            # 尝试在备份目录中查找
            SELECTED_BACKUP="${BACKUP_DIR}/${2}"
            if [ ! -f "${SELECTED_BACKUP}" ]; then
                echo "错误: 备份文件不存在: ${2}"
                exit 1
            fi
        fi
        log "INFO" "选择指定备份: ${SELECTED_BACKUP}"
        ;;
esac

# 如果通过命令行参数选择了备份，跳过交互式选择
if [ -n "${SELECTED_BACKUP}" ]; then
    # 验证备份文件
    if ! verify_backup "${SELECTED_BACKUP}"; then
        exit 1
    fi
    
    # 确认恢复
    if ! confirm_restore; then
        exit 0
    fi
    
    # 执行恢复
    if ! restore_database "${SELECTED_BACKUP}"; then
        exit 1
    fi
    
    # 验证恢复结果
    if ! verify_restore; then
        exit 1
    fi
    
    echo "✅ 数据库恢复完成！"
    exit 0
fi

# 执行主函数
main "$@"
