@echo off
setlocal

echo [1/2] Starting MariaDB (F:\xmapp\mysql, port 3307)...
start "mariadbd-xmapp" /min "C:\Program Files\MariaDB 12.2\bin\mariadbd.exe" --defaults-file=F:\xmapp\mysql\my.ini

timeout /t 2 >nul

echo [2/2] Starting Redis (F:\xmapp\redis, port 6379)...
start "redis-xmapp" /min "F:\xmapp\redis\redis-server.exe" --port 6379 --bind 127.0.0.1

echo Done.
endlocal
