@echo off
setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0..
for %%i in ("%ROOT_DIR%") do set ROOT_DIR=%%~fi
set COMPOSE_FILE=%ROOT_DIR%\deploy\docker-compose.yml
set ENV_FILE=%ROOT_DIR%\.env

set PASS=0
set WARN=0
set FAIL=0

echo ============================================================
echo  DjangoBlog Deployment Precheck
echo ============================================================

REM 1) Docker
where docker >nul 2>nul
if errorlevel 1 (
  echo [FAIL] Docker not found
  set /a FAIL+=1
) else (
  echo [PASS] Docker found
  set /a PASS+=1
  docker info >nul 2>nul
  if errorlevel 1 (
    echo [FAIL] Docker daemon is not running
    set /a FAIL+=1
  ) else (
    echo [PASS] Docker daemon is running
    set /a PASS+=1
  )
)

REM 2) Compose
docker compose version >nul 2>nul
if errorlevel 1 (
  echo [FAIL] docker compose unavailable
  set /a FAIL+=1
) else (
  echo [PASS] docker compose available
  set /a PASS+=1
)

REM 3) compose file
if exist "%COMPOSE_FILE%" (
  echo [PASS] docker-compose.yml exists
  set /a PASS+=1
) else (
  echo [FAIL] missing %COMPOSE_FILE%
  set /a FAIL+=1
)

REM 4) env file
if exist "%ENV_FILE%" (
  echo [PASS] .env exists
  set /a PASS+=1
) else (
  echo [FAIL] missing .env
  set /a FAIL+=1
)

REM 5) required keys
for %%K in (SECRET_KEY DB_NAME DB_USER DB_PASSWORD MYSQL_ROOT_PASSWORD ALLOWED_HOSTS CSRF_TRUSTED_ORIGINS DEBUG SECURE_SSL_REDIRECT SESSION_COOKIE_SECURE CSRF_COOKIE_SECURE SECURE_HSTS_SECONDS) do (
  call :check_env %%K
)

call :check_expected_env DEBUG False
call :check_expected_env SECURE_SSL_REDIRECT True
call :check_expected_env SESSION_COOKIE_SECURE True
call :check_expected_env CSRF_COOKIE_SECURE True
call :check_hsts_positive

REM 6) ports
call :check_port 80
call :check_port 8000

REM 7) compose config
if exist "%ENV_FILE%" (
  docker compose --env-file "%ENV_FILE%" -f "%COMPOSE_FILE%" config >nul 2>nul
  if errorlevel 1 (
    echo [FAIL] compose config check failed
    set /a FAIL+=1
  ) else (
    echo [PASS] compose config check passed
    set /a PASS+=1
  )
)

REM 8) rollback hint
echo [PASS] rollback available: deploy\down.bat or deploy\down.bat --purge
set /a PASS+=1

echo ------------------------------------------------------------
echo Result: PASS=%PASS% WARN=%WARN% FAIL=%FAIL%
if %FAIL% GTR 0 (
  echo Precheck FAILED. Fix FAIL items first.
  exit /b 1
) else (
  echo Precheck PASSED. Ready to deploy.
  exit /b 0
)

:check_env
set KEY=%~1
set VALUE=
if not exist "%ENV_FILE%" goto :eof
for /f "tokens=1,* delims==" %%A in ('findstr /b /c:"%KEY%=" "%ENV_FILE%"') do set VALUE=%%B
if not defined VALUE (
  echo [FAIL] missing %KEY%
  set /a FAIL+=1
) else (
  echo !VALUE! | findstr /i "your- change-in-production" >nul
  if not errorlevel 1 (
    echo [FAIL] %KEY% is still placeholder
    set /a FAIL+=1
  ) else (
    if "!VALUE!"=="" (
      echo [FAIL] %KEY% is empty
      set /a FAIL+=1
    ) else (
      echo [PASS] %KEY% configured
      set /a PASS+=1
    )
  )
)
set VALUE=
goto :eof

:check_expected_env
set KEY=%~1
set EXPECTED=%~2
set VALUE=
for /f "tokens=1,* delims==" %%A in ('findstr /b /c:"%KEY%=" "%ENV_FILE%"') do set VALUE=%%B
if not defined VALUE (
  echo [FAIL] %KEY% missing/empty
  set /a FAIL+=1
  goto :eof
)
if /I "%VALUE%"=="%EXPECTED%" (
  echo [PASS] %KEY%=%EXPECTED%
  set /a PASS+=1
) else (
  echo [FAIL] %KEY%=%VALUE% expected=%EXPECTED%
  set /a FAIL+=1
)
set VALUE=
goto :eof

:check_hsts_positive
set HSTS=
for /f "tokens=1,* delims==" %%A in ('findstr /b /c:"SECURE_HSTS_SECONDS=" "%ENV_FILE%"') do set HSTS=%%B
if not defined HSTS (
  echo [FAIL] SECURE_HSTS_SECONDS missing
  set /a FAIL+=1
  goto :eof
)
for /f %%N in ('powershell -NoProfile -Command "try{[int]('%HSTS%')}catch{-1}"') do set HSTS_NUM=%%N
if %HSTS_NUM% GTR 0 (
  echo [PASS] SECURE_HSTS_SECONDS=%HSTS%
  set /a PASS+=1
) else (
  echo [FAIL] SECURE_HSTS_SECONDS=%HSTS% expected^>0
  set /a FAIL+=1
)
set HSTS=
set HSTS_NUM=
goto :eof

:check_port
set PORT=%~1
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul
if errorlevel 1 (
  echo [PASS] port %PORT% available
  set /a PASS+=1
) else (
  echo [WARN] port %PORT% occupied
  set /a WARN+=1
)
goto :eof
