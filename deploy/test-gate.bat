@echo off
setlocal enabledelayedexpansion

REM 发布前测试门禁（默认快速门禁）
REM 用法：
REM   deploy\test-gate.bat
REM   deploy\test-gate.bat --full

set FULL=%1

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

echo [gate] 4/4 backend regression suites
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
