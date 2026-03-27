@echo off
setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0..
for %%i in ("%ROOT_DIR%") do set ROOT_DIR=%%~fi
set COMPOSE_FILE=%ROOT_DIR%\deploy\docker-compose.yml
set ENV_FILE=%ROOT_DIR%\.env

if not exist "%ENV_FILE%" (
  echo [ERROR] 缺少 %ENV_FILE%
  echo 请先执行: copy deploy\.env.docker.example .env ^&^& 编辑真实配置
  exit /b 1
)

cd /d "%ROOT_DIR%"

REM P1: enable BuildKit for faster/cached builds
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1

echo [1/4] 启动容器
docker compose --env-file "%ENV_FILE%" -f "%COMPOSE_FILE%" up -d
if errorlevel 1 exit /b 1

echo [2/4] 等待 Web 容器就绪
timeout /t 5 /nobreak >nul

echo [3/4] 执行数据库迁移
docker compose --env-file "%ENV_FILE%" -f "%COMPOSE_FILE%" exec web python manage.py migrate
if errorlevel 1 exit /b 1

echo [4/4] 跳过 collectstatic（已在镜像构建阶段完成）

echo 完成 ✅
echo 访问: http://localhost:8000/
echo 如需创建管理员: docker compose --env-file .env -f deploy/docker-compose.yml exec web python manage.py createsuperuser

endlocal
