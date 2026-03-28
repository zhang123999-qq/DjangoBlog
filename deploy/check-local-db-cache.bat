@echo off
setlocal

echo === MariaDB ===
"C:\Program Files\MariaDB 12.2\bin\mariadb.exe" -h 127.0.0.1 -P 3307 -u djangoblog -p"ssJCC1fq8NqWJ9uunnEEsxSp" -e "SELECT 1;"

echo === Redis ===
"F:\xmapp\redis\redis-cli.exe" -h 127.0.0.1 -p 6379 ping

endlocal
