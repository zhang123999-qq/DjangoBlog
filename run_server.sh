#!/bin/bash

# =================================
# DjangoBlog Server Start Script
# Supports LAN access
# =================================

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "========================================"
echo "  DjangoBlog Server"
echo "  Supports LAN Access"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment not found!"
    echo "[INFO] Please run install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Get local IP
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    # macOS fallback
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "unknown")
fi

echo -e "${GREEN}[INFO]${NC} Local IP: $LOCAL_IP"
echo ""

# Start server on 0.0.0.0:8000
echo -e "${GREEN}[INFO]${NC} Starting server on 0.0.0.0:8000"
echo -e "${YELLOW}[INFO]${NC} Access URLs:"
echo "  - Local:   http://localhost:8000"
echo "  - LAN:     http://$LOCAL_IP:8000"
echo ""
echo -e "${YELLOW}[INFO]${NC} Press Ctrl+C to stop the server."
echo ""

python manage.py runserver 0.0.0.0:8000
