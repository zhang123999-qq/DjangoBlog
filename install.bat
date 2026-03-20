@echo off
chcp 65001 >nul 2>&1
REM =================================
REM DjangoBlog Windows Install Script
REM Version: 2.1.0
REM Python 3.13+ required
REM =================================

setlocal enabledelayedexpansion

REM Parse arguments
set QUICK_INSTALL=1
set USE_MYSQL=0
set USE_DOCKER=0
set DEV_MODE=0

:parse_args
if "%~1"=="" goto end_parse
if /I "%~1"=="--quick" set QUICK_INSTALL=1
if /I "%~1"=="--mysql" set USE_MYSQL=1
if /I "%~1"=="--docker" set USE_DOCKER=1
if /I "%~1"=="--dev" set DEV_MODE=1
if /I "%~1"=="--help" goto show_help
if /I "%~1"=="-h" goto show_help
shift
goto parse_args

:show_help
echo.
echo DjangoBlog Windows Install Script v2.1.0
echo.
echo Usage: install.bat [OPTIONS]
echo.
echo Options:
echo   --help, -h    Show this help message
echo   --quick       Quick install with SQLite (default)
echo   --mysql       Use MySQL database
echo   --docker      Use Docker deployment
echo   --dev         Development mode
echo.
echo Examples:
echo   install.bat              Quick install
echo   install.bat --mysql      Use MySQL
echo   install.bat --docker     Docker deploy
echo.
exit /b 0

:end_parse

echo.
echo ========================================
echo   DjangoBlog v2.1.0 Install Script
echo   Python 3.13+ required
echo ========================================
echo.

REM Docker deployment
if "%USE_DOCKER%"=="1" (
    call :log_info "Checking Docker..."
    docker --version >nul 2>&1
    if errorlevel 1 (
        call :log_error "Docker not installed"
        exit /b 1
    )
    
    call :log_info "Using Docker deployment..."
    
    if not exist .env (
        call :log_info "Creating .env file..."
        copy .env.example .env >nul
    )
    
    call :log_info "Building and starting services..."
    docker-compose up -d --build
    
    echo.
    call :log_success "Docker deployment complete!"
    call :log_info "Visit: http://localhost"
    exit /b 0
)

REM Check Python
call :log_info "Checking Python..."
python --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Python not installed. Please install Python 3.13+"
    call :log_info "Download: https://www.python.org/downloads/"
    pause
    exit /b 1
)

REM Display Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
call :log_info "Python version: %PYVER%"

REM Check virtual environment
if not exist "venv" (
    call :log_info "Creating virtual environment..."
    python -m venv venv
    if errorlevel 1 (
        call :log_error "Failed to create virtual environment"
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call :log_info "Activating virtual environment..."
call venv\Scripts\activate.bat

REM Install dependencies
call :log_info "Installing Python dependencies..."
call :log_info "This may take a few minutes..."
if "%DEV_MODE%"=="1" (
    pip install -r requirements\development.txt --quiet
) else (
    pip install -r requirements\production.txt --quiet
)
if errorlevel 1 (
    call :log_error "Failed to install dependencies"
    call :log_info "Try running: pip install -r requirements\production.txt"
    pause
    exit /b 1
)

REM Create .env file
if not exist ".env" (
    call :log_info "Creating .env configuration..."
    copy .env.example .env >nul
    call :log_info "Created .env file with default settings"
) else (
    call :log_info "Using existing .env file"
)

REM MySQL configuration
if "%USE_MYSQL%"=="1" (
    echo.
    call :log_info "Configuring MySQL..."
    call :log_info "Please ensure MySQL is installed and database is created"
    echo.
    set /p DB_NAME="MySQL database name [djangoblog]: "
    if "!DB_NAME!"=="" set DB_NAME=djangoblog
    set /p DB_USER="MySQL username [root]: "
    if "!DB_USER!"=="" set DB_USER=root
    set /p DB_PASSWORD="MySQL password: "
    set /p DB_HOST="MySQL host [localhost]: "
    if "!DB_HOST!"=="" set DB_HOST=localhost
    set /p DB_PORT="MySQL port [3306]: "
    if "!DB_PORT!"=="" set DB_PORT=3306
    
    call :log_info "Updating .env file..."
    (
        echo DEBUG=True
        echo ALLOWED_HOSTS=localhost,127.0.0.1
        echo SITE_NAME=Django Blog
        echo SECRET_KEY=d96^(s^gk@&9o!3^g^(71f7@!bnamvp1yanvph&%%wn^^(_r4xzt*&j
        echo DB_ENGINE=mysql
        echo DB_NAME=!DB_NAME!
        echo DB_USER=!DB_USER!
        echo DB_PASSWORD=!DB_PASSWORD!
        echo DB_HOST=!DB_HOST!
        echo DB_PORT=!DB_PORT!
    ) > .env
    call :log_info "MySQL configuration saved"
)

REM Run migrations
call :log_info "Running database migrations..."
python manage.py migrate --noinput
if errorlevel 1 (
    call :log_error "Migration failed"
    pause
    exit /b 1
)

REM Initialize default data
call :log_info "Initializing default data..."
python manage.py init_default_data

REM Collect static files
call :log_info "Collecting static files..."
if not exist "staticfiles" mkdir staticfiles
python manage.py collectstatic --noinput
if errorlevel 1 (
    call :log_warn "Static files collection had issues, continuing..."
)

REM Create admin account
call :log_info "Creating admin account..."
if "%QUICK_INSTALL%"=="1" (
    python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development'); import django; django.setup(); from apps.accounts.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" >nul 2>&1
    if errorlevel 1 (
        python manage.py shell -c "from apps.accounts.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" >nul 2>&1
    )
    call :log_info "Admin account: admin / admin123"
) else (
    python manage.py createsuperuser
)

REM Create install lock
call :log_info "Finalizing installation..."
echo Installed at %date% %time% > installed.lock

REM Success message
echo.
echo ========================================
echo        Installation Complete!
echo ========================================
echo.
call :log_info "Quick start commands:"
echo   python manage.py runserver
echo.
call :log_info "Access URLs:"
echo   Main site:    http://localhost:8000
echo   Admin panel:  http://localhost:8000/admin/
echo.
call :log_info "Admin credentials:"
echo   Username: admin
echo   Password: admin123
echo.
call :log_warn "For production:"
echo   1. Change SECRET_KEY in .env
echo   2. Set DEBUG=False in .env
echo   3. Use a strong password for admin
echo.
pause
exit /b 0

REM =================================
REM Logging functions
REM =================================

:log_info
echo [INFO] %~1
goto :eof

:log_warn
echo [WARN] %~1
goto :eof

:log_error
echo [ERROR] %~1
goto :eof

:log_success
echo [SUCCESS] %~1
goto :eof
