$mariadb = 'C:\Program Files\MariaDB 12.2\bin\mariadbd.exe'
$mysqlArgs = '--defaults-file=F:\xmapp\mysql\my.ini'

$redis = 'F:\xmapp\redis\redis-server.exe'
$redisArgs = '--port 6379 --bind 127.0.0.1'

Start-Process -FilePath $mariadb -ArgumentList $mysqlArgs -WorkingDirectory 'F:\xmapp\mysql'
Start-Sleep -Seconds 1
Start-Process -FilePath $redis -ArgumentList $redisArgs -WorkingDirectory 'F:\xmapp\redis'
