@echo off
REM DjangoBlog Celery 启动脚本 (Windows)
REM 使用方法:
REM   start_celery.bat worker   - 启动 Worker
REM   start_celery.bat beat     - 启动 Beat (定时任务)
REM   start_celery.bat flower   - 启动 Flower (监控界面)
REM   start_celery.bat all      - 启动全部

setlocal

REM 设置环境
set DJANGO_SETTINGS_MODULE=config.settings.development

if "%1"=="" goto usage
if "%1"=="worker" goto worker
if "%1"=="beat" goto beat
if "%1"=="flower" goto flower
if "%1"=="all" goto all
goto usage

:worker
echo Starting Celery Worker...
celery -A config worker -l info -P eventlet
goto end

:beat
echo Starting Celery Beat...
celery -A config beat -l info
goto end

:flower
echo Starting Flower...
celery -A config flower --port=5555
goto end

:all
echo Starting all Celery services...
echo Worker starting in background...
start "Celery Worker" celery -A config worker -l info -P eventlet
echo Beat starting in background...
start "Celery Beat" celery -A config beat -l info
echo Flower starting in background...
start "Flower" celery -A config flower --port=5555
echo All services started!
echo Flower UI: http://localhost:5555
goto end

:usage
echo Usage: %0 ^<worker^|beat^|flower^|all^>
echo.
echo Commands:
echo   worker - Start Celery Worker (process tasks)
echo   beat   - Start Celery Beat (scheduled tasks)
echo   flower - Start Flower (monitoring UI at http://localhost:5555)
echo   all    - Start all services
echo.
echo Prerequisites:
echo   1. Redis must be running on localhost:6379
echo   2. Run: pip install celery redis flower eventlet
goto end

:end
endlocal
