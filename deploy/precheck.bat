@echo off
setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0..
for %%i in ("%ROOT_DIR%") do set ROOT_DIR=%%~fi
set COMPOSE_FILE=%ROOT_DIR%\deploy\docker-compose.yml
set ENV_FILE=%ROOT_DIR%\.env

set PASS=0
set WARN=0
set FAIL=0

:banner
echo ============================================================
echo  DjangoBlog 部署前预检
echo ============================================================

REM 1) Docker
where docker >nul 2>nul
if errorlevel 1 (
  echo [FAIL] Docker 未安装
  set /a FAIL+=1
) else (
  echo [PASS] Docker 已安装
  set /a PASS+=1
  docker info >nul 2>nul
  if errorlevel 1 (
    echo [FAIL] Docker daemon 未运行
    set /a FAIL+=1
  ) else (
    echo [PASS] Docker daemon 运行中
    set /a PASS+=1
  )
)

REM 2) Compose
docker compose version >nul 2>nul
if errorlevel 1 (
  echo [FAIL] Docker Compose 不可用（docker compose）
  set /a FAIL+=1
) else (
  echo [PASS] Docker Compose 可用
  set /a PASS+=1
)

REM 3) compose 文件
if exist "%COMPOSE_FILE%" (
  echo [PASS] docker-compose.yml 存在
  set /a PASS+=1
) else (
  echo [FAIL] 缺少 %COMPOSE_FILE%
  set /a FAIL+=1
)

REM 4) .env
if exist "%ENV_FILE%" (
  echo [PASS] .env 存在
  set /a PASS+=1
) else (
  echo [FAIL] 缺少 .env（请先 copy deploy\.env.docker.example .env）
  set /a FAIL+=1
)

REM 5) 必填项校验（简化）
for %%K in (SECRET_KEY DB_NAME DB_USER DB_PASSWORD MYSQL_ROOT_PASSWORD ALLOWED_HOSTS CSRF_TRUSTED_ORIGINS) do (
  call :check_env %%K
)

REM 6) 端口占用
call :check_port 80
call :check_port 8000

REM 7) compose 配置校验
if exist "%ENV_FILE%" (
  docker compose --env-file "%ENV_FILE%" -f "%COMPOSE_FILE%" config >nul 2>nul
  if errorlevel 1 (
    echo [FAIL] Compose 配置校验失败
    set /a FAIL+=1
  ) else (
    echo [PASS] Compose 配置校验通过
    set /a PASS+=1
  )
)

REM 8) 域名解析（可选）
for /f "tokens=1 delims=," %%H in ('powershell -NoProfile -Command "(Get-Content -Path '%ENV_FILE%' | Select-String '^ALLOWED_HOSTS=' | Select-Object -Last 1).ToString().Split('=')[1]" 2^>nul') do set FIRST_HOST=%%H
if defined FIRST_HOST (
  echo %FIRST_HOST% | findstr /i "localhost 127.0.0.1" >nul
  if errorlevel 1 (
    nslookup %FIRST_HOST% >nul 2>nul
    if errorlevel 1 (
      echo [WARN] 域名 %FIRST_HOST% 暂不可解析
      set /a WARN+=1
    ) else (
      echo [PASS] 域名 %FIRST_HOST% 可解析
      set /a PASS+=1
    )
  ) else (
    echo [WARN] ALLOWED_HOSTS 首域名为本地地址，跳过 DNS 检查
    set /a WARN+=1
  )
)

REM 9) 磁盘空间（建议）
for /f %%F in ('powershell -NoProfile -Command "[int]((Get-PSDrive -Name ((Get-Location).Path.Substring(0,1))).Free/1MB)"') do set FREE_MB=%%F
if defined FREE_MB (
  if %FREE_MB% GEQ 2048 (
    echo [PASS] 可用磁盘空间充足（^>=2GB）
    set /a PASS+=1
  ) else (
    echo [WARN] 可用磁盘空间较低（建议 ^>=2GB）
    set /a WARN+=1
  )
)

REM 10) 回滚命令
echo [PASS] 回滚命令可用：deploy\down.bat 或 deploy\down.bat --purge
set /a PASS+=1

echo ------------------------------------------------------------
echo 结果：PASS=%PASS% WARN=%WARN% FAIL=%FAIL%
if %FAIL% GTR 0 (
  echo 预检未通过，请先修复 FAIL 项。
  exit /b 1
) else (
  echo 预检通过，可执行部署。
  exit /b 0
)

:check_env
set KEY=%~1
if not exist "%ENV_FILE%" (
  goto :eof
)
for /f "tokens=1,* delims==" %%A in ('findstr /b /c:"%KEY%=" "%ENV_FILE%"') do set VALUE=%%B
if not defined VALUE (
  echo [FAIL] 缺少 %KEY%
  set /a FAIL+=1
) else (
  echo !VALUE! | findstr /i "your- change-in-production" >nul
  if not errorlevel 1 (
    echo [FAIL] %KEY% 仍是占位符
    set /a FAIL+=1
  ) else (
    if "!VALUE!"=="" (
      echo [FAIL] %KEY% 为空
      set /a FAIL+=1
    ) else (
      echo [PASS] %KEY% 已配置
      set /a PASS+=1
    )
  )
)
set VALUE=
goto :eof

:check_port
set PORT=%~1
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul
if errorlevel 1 (
  echo [PASS] 端口 %PORT% 可用
  set /a PASS+=1
) else (
  echo [WARN] 端口 %PORT% 已被占用
  set /a WARN+=1
)
goto :eof
