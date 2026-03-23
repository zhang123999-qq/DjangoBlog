@echo off
echo ========================================
echo DjangoBlog 安全更新脚本
echo ========================================
echo.

REM 1. 备份数据库
echo [1/7] 备份数据库...
copy db.sqlite3 db.sqlite3.backup >nul 2>&1
echo       已备份到 db.sqlite3.backup

REM 2. 查看本地修改
echo.
echo [2/7] 检查本地修改...
git status --short

REM 3. 暂存本地修改
echo.
echo [3/7] 暂存本地修改...
git stash

REM 4. 拉取最新代码
echo.
echo [4/7] 拉取最新代码...
git pull origin main

REM 5. 恢复本地修改
echo.
echo [5/7] 恢复本地修改...
git stash pop >nul 2>&1

REM 6. 更新依赖
echo.
echo [6/7] 更新依赖...
uv sync

REM 7. 检查迁移
echo.
echo [7/7] 检查数据库迁移...
python manage.py showmigrations

echo.
echo ========================================
echo 更新完成！
echo ========================================
echo.
echo 如果有新的迁移，请运行: python manage.py migrate
echo 如果有静态文件变更，请运行: python manage.py collectstatic
echo.
pause
