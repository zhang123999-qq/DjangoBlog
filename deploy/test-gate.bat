@echo off
setlocal enabledelayedexpansion

REM 发布前测试门禁（默认快速门禁）
REM 用法：
REM   deploy\test-gate.bat
REM   deploy\test-gate.bat --full

set FULL=%1

REM 强制按生产配置执行 deploy 检查，避免误用开发配置产生噪声告警
set DJANGO_SETTINGS_MODULE=config.settings.production
set DEBUG=False

echo [gate] 1/4 python 语法冒烟
python -m py_compile manage.py config\settings\base.py apps\api\moderation_views.py apps\blog\tasks.py
if errorlevel 1 goto :fail

echo [gate] 2/4 Django check
uv run python manage.py check
if errorlevel 1 goto :fail

echo [gate] 3/4 Django deploy check (warnings allowed)
uv run python manage.py check --deploy
if errorlevel 1 (
  echo [gate] deploy check has warnings/issues (non-blocking in this gate).
)

echo [gate] 4/6 scoped quality checks
uv run python -m mypy apps\api\moderation_views.py apps\blog\tasks.py
if errorlevel 1 goto :fail
uv run python -m flake8 apps\api\moderation_views.py apps\blog\tasks.py --max-line-length=140 --extend-ignore=W293
if errorlevel 1 goto :fail

echo [gate] 5/6 backend regression suites
set DJANGO_SETTINGS_MODULE=config.settings.test
set DEBUG=False
uv run pytest -q tests\test_smoke_backend.py tests\test_core_backend_suite.py tests\test_core_backend_suite_ext.py tests\test_core_backend_suite_auth.py tests\test_core_backend_suite_ops.py
if errorlevel 1 goto :fail

if /I "%FULL%"=="--full" (
  echo [gate] full mode: run full pytest collection
  uv run pytest -q --maxfail=1
  if errorlevel 1 goto :fail
)

echo [gate] PASS
goto :eof

:fail
echo [gate] FAIL
exit /b 1
