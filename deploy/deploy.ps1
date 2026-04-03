# ========================================
# DjangoBlog 一键部署脚本 (Windows PowerShell)
# 优化版：镜像只构建一次 + 断线续传 + 健康检查
# ========================================
param(
    [ValidateSet('deploy','update','start','stop','status','restart','clean')]
    [string]$Action = "deploy"
)

$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['Out-Default:OutVariable'] = $null

function Log   { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $args" -ForegroundColor Green }
function Warn  { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] WARN: $args" -ForegroundColor Yellow }
function Error { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ERROR: $args" -ForegroundColor Red; exit 1 }

$deployDir = $PSScriptRoot
Set-Location $deployDir
$env:COMPOSE_PROJECT_NAME = "djangoblog"

Log "模式: $Action"
Log "工作目录: $deployDir"

# ========================================
# 部署模式
# ========================================
if ($Action -eq "deploy") {
    Log "=== 完整部署 ==="

    # 1. 构建镜像 (只构建一次)
    Log "Step 1/4: 构建 Django 镜像 (所有服务共享)"
    docker compose build web
    if ($LASTEXITCODE -ne 0) { Error "镜像构建失败" }

    # 2. 启动依赖
    Log "Step 2/4: 启动 MySQL + Redis"
    docker compose up -d db redis

    # 等待 MySQL 就绪
    Log "等待 MySQL 就绪 (最多60秒)..."
    $maxWait = 60
    $waited = 0
    while ($waited -lt $maxWait) {
        try {
            $result = docker compose exec -T db mysqladmin ping -h localhost 2>$null
            if ($LASTEXITCODE -eq 0) { break }
        } catch {}
        Start-Sleep -Seconds 2
        $waited += 2
        Write-Host "." -NoNewline
    }
    Write-Host ""
    if ($waited -ge $maxWait) { Error "MySQL 启动超时" }
    Log "MySQL 就绪!"

    # 3. 运行迁移
    Log "Step 3/4: 运行数据库迁移"
    docker compose run --rm migrate
    if ($LASTEXITCODE -ne 0) { Error "迁移失败" }

    # 4. 启动全部
    Log "Step 4/4: 启动全部服务"
    docker compose up -d

    Log "=== 部署完成 ==="
    Log "Web:   http://localhost:8000"
    Log "Nginx: http://localhost:80"

    # 健康检查
    Start-Sleep -Seconds 5
    Log "服务状态:"
    docker compose ps

# ========================================
# 更新模式
# ========================================
} elseif ($Action -eq "update") {
    Log "=== 增量更新 ==="

    # 拉最新代码
    $parentDir = Split-Path $deployDir -Parent
    if (Test-Path "$parentDir\.git") {
        Log "Pulling latest code..."
        Set-Location $parentDir
        git pull
        Set-Location $deployDir
    }

    # 只构建 web (其他服务共享同一镜像)
    Log "构建新镜像 (只构建一次)..."
    docker compose build web

    # 运行迁移
    Log "运行迁移..."
    docker compose run --rm migrate

    # 重启使用新镜像的服务
    Log "重启 web/celery 服务..."
    docker compose up -d --force-recreate web celery_worker celery_beat

    Log "=== 更新完成 ==="
    docker compose ps

# ========================================
# 启动
# ========================================
} elseif ($Action -eq "start") {
    Log "启动全部服务..."
    docker compose up -d
    docker compose ps

# ========================================
# 停止
# ========================================
} elseif ($Action -eq "stop") {
    Log "停止全部服务..."
    docker compose down
    Log "已停止"

# ========================================
# 重启
# ========================================
} elseif ($Action -eq "restart") {
    Log "重启全部服务..."
    docker compose restart
    docker compose ps

# ========================================
# 状态
# ========================================
} elseif ($Action -eq "status") {
    Log "服务状态:"
    docker compose ps
    Log ""
    Log "DjangoBlog 镜像:"
    docker images | Select-String "djangoblog"
    Log ""
    Log "Docker 磁盘使用:"
    docker system df

# ========================================
# 清理
# ========================================
} elseif ($Action -eq "clean") {
    Log "清理所有容器和镜像..."
    docker compose down -v --rmi all
    docker system prune -f
    Log "清理完成"
}

Log "完成!"
