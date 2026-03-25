@echo off
setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0..
for %%i in ("%ROOT_DIR%") do set ROOT_DIR=%%~fi
set COMPOSE_FILE=%ROOT_DIR%\deploy\docker-compose.yml
set ENV_FILE=%ROOT_DIR%\.env

REM 用法:
REM   deploy\down.bat           普通停止（保留数据卷）
REM   deploy\down.bat --purge   停止并删除数据卷

cd /d "%ROOT_DIR%"

set COMPOSE_CMD=docker compose -f "%COMPOSE_FILE%"
if exist "%ENV_FILE%" (
  set COMPOSE_CMD=docker compose --env-file "%ENV_FILE%" -f "%COMPOSE_FILE%"
) else (
  echo [WARN] 未找到 %ENV_FILE%，将使用默认 compose 环境
)

if "%~1"=="--purge" (
  echo [MODE] 停止并删除容器/网络/数据卷
  %COMPOSE_CMD% down -v
) else (
  echo [MODE] 普通停止（保留数据卷）
  %COMPOSE_CMD% down
)

if errorlevel 1 exit /b 1

echo 完成 ✅
endlocal
