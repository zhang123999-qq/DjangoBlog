#!/bin/bash

# =================================
# DjangoBlog Auto Install Script
# Version: 2.1.0
# Python 3.13+ required
# =================================

set -e  # Exit on error

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}==>${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install $1 first."
        exit 1
    fi
}

# Show help message
show_help() {
    echo "DjangoBlog Install Script v2.1.0"
    echo ""
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --quick             Quick install with SQLite (default)"
    echo "  --mysql             Use MySQL database"
    echo "  --postgres          Use PostgreSQL database"
    echo "  --docker            Use Docker deployment"
    echo "  --dev               Development mode"
    echo "  --no-venv           Don't create virtual environment"
    echo ""
    echo "Examples:"
    echo "  ./install.sh              # Quick install"
    echo "  ./install.sh --mysql      # Use MySQL"
    echo "  ./install.sh --docker     # Docker deploy"
}

# Parse arguments
QUICK_INSTALL=true
USE_MYSQL=false
USE_POSTGRES=false
USE_DOCKER=false
DEV_MODE=false
CREATE_VENV=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --quick)
            QUICK_INSTALL=true
            shift
            ;;
        --mysql)
            USE_MYSQL=true
            QUICK_INSTALL=false
            shift
            ;;
        --postgres)
            USE_POSTGRES=true
            QUICK_INSTALL=false
            shift
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --no-venv)
            CREATE_VENV=false
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Welcome message
echo ""
echo "========================================"
echo "   DjangoBlog v2.1.0 Install Script"
echo "   Python 3.13+ required"
echo "========================================"
echo ""

# Docker deployment
if [ "$USE_DOCKER" = true ]; then
    log_step "Checking Docker environment..."
    check_command docker
    
    # Check docker compose (v2) or docker-compose (v1)
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        log_error "Docker Compose is not installed"
        log_info "Install: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    log_info "Using: $COMPOSE_CMD"
    
    # Create .env file
    if [ ! -f .env ]; then
        log_step "Creating .env configuration..."
        cp .env.example .env
        
        # Generate random secret key
        SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))' 2>/dev/null || openssl rand -base64 50 | tr -d '\n')
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
        else
            sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
        fi
    fi
    
    log_step "Building Docker image..."
    $COMPOSE_CMD build
    
    log_step "Starting services..."
    $COMPOSE_CMD up -d
    
    log_success "Docker deployment complete!"
    log_info "Visit: http://localhost"
    exit 0
fi

# Check system dependencies
log_step "Checking system dependencies..."
check_command python3

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log_info "Python version: $PYTHON_VERSION"

# Check Python 3.13+
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 13 ]; }; then
    log_error "Python 3.13+ is required. Current version: $PYTHON_VERSION"
    log_info "Download: https://www.python.org/downloads/"
    exit 1
fi

# Check virtual environment
if [ "$CREATE_VENV" = true ]; then
    if [ ! -d "venv" ]; then
        log_step "Creating virtual environment..."
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            log_error "Failed to create virtual environment"
            exit 1
        fi
    fi
    
    log_step "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies
log_step "Installing Python dependencies..."
log_info "This may take a few minutes..."

if [ "$DEV_MODE" = true ]; then
    pip install -r requirements/development.txt --quiet
else
    pip install -r requirements/production.txt --quiet
fi

if [ $? -ne 0 ]; then
    log_error "Failed to install dependencies"
    log_info "Try running manually: pip install -r requirements/production.txt"
    exit 1
fi

# Create .env file
if [ ! -f .env ]; then
    log_step "Creating configuration file..."
    cp .env.example .env
    
    # Generate random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))' 2>/dev/null || openssl rand -base64 50 | tr -d '\n')
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
    else
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
    fi
    
    log_info "Created .env file with random SECRET_KEY"
else
    log_info "Using existing .env file"
fi

# MySQL configuration
if [ "$USE_MYSQL" = true ]; then
    log_step "Configuring MySQL database..."
    log_warn "Please ensure MySQL is installed and database is created"
    echo ""
    read -p "MySQL database name [djangoblog]: " DB_NAME
    DB_NAME=${DB_NAME:-djangoblog}
    read -p "MySQL username [root]: " DB_USER
    DB_USER=${DB_USER:-root}
    read -sp "MySQL password: " DB_PASSWORD
    echo ""
    read -p "MySQL host [localhost]: " DB_HOST
    DB_HOST=${DB_HOST:-localhost}
    read -p "MySQL port [3306]: " DB_PORT
    DB_PORT=${DB_PORT:-3306}
    
    log_info "Updating .env file..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|DB_ENGINE=.*|DB_ENGINE=mysql|" .env
        sed -i '' "s|DB_NAME=.*|DB_NAME=$DB_NAME|" .env
        sed -i '' "s|DB_USER=.*|DB_USER=$DB_USER|" .env
        sed -i '' "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|" .env
        sed -i '' "s|DB_HOST=.*|DB_HOST=$DB_HOST|" .env
        sed -i '' "s|DB_PORT=.*|DB_PORT=$DB_PORT|" .env
    else
        sed -i "s|DB_ENGINE=.*|DB_ENGINE=mysql|" .env
        sed -i "s|DB_NAME=.*|DB_NAME=$DB_NAME|" .env
        sed -i "s|DB_USER=.*|DB_USER=$DB_USER|" .env
        sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|" .env
        sed -i "s|DB_HOST=.*|DB_HOST=$DB_HOST|" .env
        sed -i "s|DB_PORT=.*|DB_PORT=$DB_PORT|" .env
    fi
    
    log_info "MySQL configuration saved"
fi

# PostgreSQL configuration
if [ "$USE_POSTGRES" = true ]; then
    log_step "Configuring PostgreSQL database..."
    log_warn "Please ensure PostgreSQL is installed and database is created"
    echo ""
    read -p "PostgreSQL database name [djangoblog]: " DB_NAME
    DB_NAME=${DB_NAME:-djangoblog}
    read -p "PostgreSQL username [postgres]: " DB_USER
    DB_USER=${DB_USER:-postgres}
    read -sp "PostgreSQL password: " DB_PASSWORD
    echo ""
    read -p "PostgreSQL host [localhost]: " DB_HOST
    DB_HOST=${DB_HOST:-localhost}
    read -p "PostgreSQL port [5432]: " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    
    log_info "Updating .env file..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|DB_ENGINE=.*|DB_ENGINE=postgresql|" .env
        sed -i '' "s|DB_NAME=.*|DB_NAME=$DB_NAME|" .env
        sed -i '' "s|DB_USER=.*|DB_USER=$DB_USER|" .env
        sed -i '' "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|" .env
        sed -i '' "s|DB_HOST=.*|DB_HOST=$DB_HOST|" .env
        sed -i '' "s|DB_PORT=.*|DB_PORT=$DB_PORT|" .env
    else
        sed -i "s|DB_ENGINE=.*|DB_ENGINE=postgresql|" .env
        sed -i "s|DB_NAME=.*|DB_NAME=$DB_NAME|" .env
        sed -i "s|DB_USER=.*|DB_USER=$DB_USER|" .env
        sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|" .env
        sed -i "s|DB_HOST=.*|DB_HOST=$DB_HOST|" .env
        sed -i "s|DB_PORT=.*|DB_PORT=$DB_PORT|" .env
    fi
    
    log_info "PostgreSQL configuration saved"
fi

# Run migrations
log_step "Running database migrations..."
python manage.py migrate --noinput
if [ $? -ne 0 ]; then
    log_error "Database migration failed"
    exit 1
fi

# Initialize default data
log_step "Initializing default data..."
python manage.py init_default_data

# Collect static files
log_step "Collecting static files..."
mkdir -p staticfiles
python manage.py collectstatic --noinput
if [ $? -ne 0 ]; then
    log_warn "Static files collection had issues, continuing..."
fi

# Create admin account
log_step "Creating admin account..."
if [ "$QUICK_INSTALL" = true ]; then
    # Check if admin already exists
    ADMIN_EXISTS=$(python manage.py shell -c "
from apps.accounts.models import User
print(User.objects.filter(username='admin').exists())
" 2>/dev/null | tail -1)
    
    if [ "$ADMIN_EXISTS" != "True" ]; then
        python manage.py shell -c "
from apps.accounts.models import User
User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log_info "Admin account created: admin / admin123"
        else
            log_warn "Failed to create admin automatically"
            log_info "Run manually: python manage.py createsuperuser"
        fi
    else
        log_info "Admin account already exists"
    fi
else
    python manage.py createsuperuser
fi

# Create install lock file
log_step "Finalizing installation..."
echo "Installed at $(date)" > installed.lock

# Success message
echo ""
echo "========================================"
echo "       Installation Complete!"
echo "========================================"
echo ""
log_info "Quick start commands:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
log_info "Access URLs:"
echo "  Main site:    http://localhost:8000"
echo "  Admin panel:  http://localhost:8000/admin/"
echo ""
log_info "Admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
log_warn "For production:"
echo "  1. Change SECRET_KEY in .env"
echo "  2. Set DEBUG=False in .env"
echo "  3. Use a strong password for admin"
echo ""
