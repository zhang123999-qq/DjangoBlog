# ========================================
# DjangoBlog 健康检查与维护脚本
# ========================================
param(
    [ValidateSet('check','logs','logs-web','logs-db','logs-redis','logs-celery','logs-nginx','backup-info')]
    [string]$Action = "check"
)

$deployDir = $PSScriptRoot
Set-Location $deployDir
$env:COMPOSE_PROJECT_NAME = "djangoblog"

function Log   { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $args" -ForegroundColor Green }
function Warn  { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] WARN: $args" -ForegroundColor Yellow }
function Err   { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ERROR: $args" -ForegroundColor Red }

if ($Action -eq "check") {
    Log "=== 健康检查 ==="
    
    # 容器状态
    $services = @("db", "redis", "web", "celery_worker", "celery_beat", "nginx")
    $allHealthy = $true
    
    foreach ($svc in $services) {
        $state = docker compose ps $svc --format json 2>$null | ConvertFrom-Json
        if ($state.State -eq "running") {
            Log "  $svc : 运行中"
        } else {
            Err "  $svc : $($state.State) - 需要检查!"
            $allHealthy = $false
        }
    }
    
    # 健康检查
    $states = docker compose ps --format "{{.Name}}: {{.Status}}" 2>$null
    Log ""
    Log "健康状态:"
    $states | ForEach-Object { Log "  $_" }
    
    if ($allHealthy) {
        Log ""
        Log "所有服务运行正常!"
    } else {
        Warn ""
        Warn "部分服务异常，建议执行: .\deploy.ps1 restart"
    }

} elseif ($Action -eq "logs") {
    docker compose logs --tail=50

} elseif ($Action -eq "logs-web") {
    docker compose logs --tail=50 web

} elseif ($Action -eq "logs-db") {
    docker compose logs --tail=50 db

} elseif ($Action -eq "logs-redis") {
    docker compose logs --tail=50 redis

} elseif ($Action -eq "logs-celery") {
    Log "=== Celery Worker 日志 ==="
    docker compose logs --tail=50 celery_worker
    Log ""
    Log "=== Celery Beat 日志 ==="
    docker compose logs --tail=50 celery_beat

} elseif ($Action -eq "logs-nginx") {
    docker compose logs --tail=50 nginx

} elseif ($Action -eq "backup-info") {
    Log "=== 数据卷信息 ==="
    docker volume ls | Select-String djangoblog
    Log ""
    Log "=== 磁盘使用 ==="
    docker system df | Select-String djangoblog
}
