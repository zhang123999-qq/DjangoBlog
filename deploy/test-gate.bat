@echo off
setlocal enabledelayedexpansion

REM Pre-release test gate (quick by default)
REM Usage:
REM   deploy\test-gate.bat
REM   deploy\test-gate.bat --full

set FULL=%1

REM Use production settings for deploy checks
set DJANGO_SETTINGS_MODULE=config.settings.production
set DEBUG=False

echo [gate] 1/4 python syntax smoke
python -m py_compile manage.py config\settings\base.py apps\api\moderation_views.py apps\blog\tasks.py
if errorlevel 1 goto :fail

echo [gate] 2/4 Django check
uv run python manage.py check
if errorlevel 1 goto :fail

echo [gate] 3/4 Django deploy check - warnings allowed
uv run python manage.py check --deploy
if errorlevel 1 (
  echo [gate] deploy check has warnings/issues - non-blocking in this gate.
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

echo [gate] 6/6 optional security scans
where gitleaks >nul 2>nul
if errorlevel 1 (
  echo [gate] gitleaks not found, skip
) else (
  gitleaks detect --source . --no-git --redact
  if errorlevel 1 goto :fail
)

where bandit >nul 2>nul
if errorlevel 1 (
  echo [gate] bandit not found, skip
) else (
  rem Only block medium/high findings; low-level findings are tracked separately
  bandit -q -ll -r apps config -x "**/migrations/**,tests/**,apps/tools/tool_modules/password_gen.py,apps/tools/tool_modules/random_number_tool.py,apps/tools/tool_modules/id_card_tool.py,apps/tools/tool_modules/lorem_generator.py,apps/tools/tool_modules/poem_generator_tool.py,apps/tools/tool_modules/quote_tool.py,apps/accounts/captcha.py,apps/accounts/avatar_utils.py"
  if errorlevel 1 goto :fail
)

where pip-audit >nul 2>nul
if errorlevel 1 (
  echo [gate] pip-audit not found, skip
) else (
  rem Temporary ignore: CVE-2026-4539 (local-only ReDoS, no upstream fixed version yet)
  pip-audit --ignore-vuln CVE-2026-4539
  if errorlevel 1 goto :fail
)

echo [gate] 7/7 done
echo [gate] PASS
goto :eof

:fail
echo [gate] FAIL
exit /b 1
