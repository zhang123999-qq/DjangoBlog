@echo off
echo ========================================
echo   DjangoBlog 局域网启动脚本
echo ========================================
echo.
echo 启动服务并允许局域网访问...
echo 访问地址: http://你的IP:8000
echo.
python manage.py runserver 0.0.0.0:8000
