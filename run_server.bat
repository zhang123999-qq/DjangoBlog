@echo off
chcp 65001 >nul 2>&1
REM =================================
REM DjangoBlog Server Start Script
REM Supports LAN access
REM =================================

echo.
echo ========================================
echo   DjangoBlog Server
echo   Supports LAN Access
echo ========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo [INFO] Please run install.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :got_ip
)
:got_ip
set LOCAL_IP=%LOCAL_IP: =%

echo [INFO] Local IP: %LOCAL_IP%
echo.

REM Start server on 0.0.0.0:8000
echo [INFO] Starting server on 0.0.0.0:8000
echo [INFO] Access URLs:
echo   - Local:   http://localhost:8000
echo   - LAN:     http://%LOCAL_IP%:8000
echo.
echo [INFO] Press Ctrl+C to stop the server.
echo.

python manage.py runserver 0.0.0.0:8000
