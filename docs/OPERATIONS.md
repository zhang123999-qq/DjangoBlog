# 🛠 日常运维速查

> DjangoBlog 部署后的常用运维操作

---

## 🩺 健康检查

### 手动检查

```bash
bash deploy/health.sh check
```

输出示例：
```
====== 健康检查 ======
  db : 运行中 (healthy)
  redis : 运行中 (healthy)
  web : 运行中
  celery_worker : 运行中
  celery_beat : 运行中
====== 完整状态 ======
NAME                STATUS          PORTS
djangoblog-web      Up (healthy)    127.0.0.1:8000->8000/tcp
djangoblog-db       Up (healthy)    3306/tcp
djangoblog-redis    Up (healthy)    6379/tcp
djangoblog-celery-worker  Up         8000/tcp
djangoblog-celery-beat     Up         8000/tcp
所有服务运行正常!
```

### 自动监控（推荐）

```bash
# 加到 crontab，每 10 分钟检查一次
*/10 * * * * cd /opt/djangoblog && bash deploy/health.sh check >> /opt/djangoblog/deploy/logs/cron_health.log 2>&1
```

监控关键词：
- 正常：`所有服务运行正常`
- 异常：`异常!` / `not found` / `未找到`

---

## 📊 查看日志

### 一键查看

```bash
bash deploy/health.sh logs          # 所有服务，最近 100 行
bash deploy/health.sh logs-web      # 只看 web
bash deploy/health.sh logs-db       # 只看 db
bash deploy/health.sh logs-redis    # 只看 redis
bash deploy/health.sh logs-celery   # 只看 celery
bash deploy/health.sh logs-nginx    # Nginx 在宿主机
```

### 实时跟踪

```bash
docker compose -f deploy/docker-compose.yml logs -f web
docker compose -f deploy/docker-compose.yml logs -f --tail=50 celery_worker
```

### 应用日志位置

| 日志 | 路径 |
|---|---|
| Gunicorn | 容器内 stdout（`docker logs`）|
| Django 应用 | `/app/logs/`（挂载到 logs_volume）|
| Nginx 访问 | `/var/log/nginx/access.log` |
| Nginx 错误 | `/var/log/nginx/error.log` |
| Cron 备份 | `deploy/logs/cron_*.log` |
| 健康检查 | `deploy/logs/cron_health.log` |

---

## 💾 备份与恢复

### 手动备份

```bash
bash deploy/backup.sh
```

输出：`备份完成: /tmp/djangoblog_backup_YYYYMMDD_HHMMSS/djangoblog.sql.gz`

### 自动备份

`deploy/crontab.example` 已配好：
- 每天 02:00 - 备份
- 每周日 03:00 - 清理旧备份
- 每月 1 号 04:00 - 备份报告
- 每天 05:00 - 验证备份

启用：
```bash
crontab -e
# 粘贴 deploy/crontab.example 内容
```

### 恢复

```bash
# 列出所有备份
bash deploy/restore.sh --list

# 恢复到最新
bash deploy/restore.sh --latest

# 恢复指定备份
bash deploy/restore.sh /tmp/djangoblog_backup_20260903_020000/djangoblog.sql.gz
```

---

## 🔄 部署与更新

### 手动部署

```bash
# 首次部署
sudo bash deploy/auto-deploy.sh

# 增量更新
bash deploy/auto-deploy.sh update
```

### 自动部署（CI/CD）

详见 [CI_DEPLOY.md](CI_DEPLOY.md)：
- push 到 main → 自动部署
- 失败自动回滚
- 钉钉通知（可选）

### 手动重启

```bash
# 重启所有服务
bash deploy/auto-deploy.sh restart

# 重启单个服务
docker compose -f deploy/docker-compose.yml restart web
```

---

## 🔧 故障排查

### 服务起不来

```bash
# 1. 看具体哪个服务挂了
bash deploy/health.sh check

# 2. 看日志
docker compose -f deploy/docker-compose.yml logs --tail=100 web

# 3. 进容器 debug
docker compose -f deploy/docker-compose.yml exec web bash
# 在容器内：
python manage.py shell
cat /app/logs/*.log
```

### 数据库连不上

```bash
# 检查 db 容器
docker compose -f deploy/docker-compose.yml logs db

# 测试连接
docker compose -f deploy/docker-compose.yml exec db \
  mysql -u root -p$DB_ROOT_PASSWORD -e "SHOW DATABASES;"

# 检查 .env 密码匹配
grep DB_ .env
```

### Nginx 502

```bash
# web 容器没起
docker compose -f deploy/docker-compose.yml ps web
docker compose -f deploy/docker-compose.yml logs web

# 测试 web 是否在监听
curl -v http://127.0.0.1:8000/healthz/
```

### Celery 任务不执行

```bash
# 检查 worker
docker compose -f deploy/docker-compose.yml logs celery_worker

# 检查 broker（Redis）
docker compose -f deploy/docker-compose.yml exec redis \
  redis-cli -a $REDIS_PASSWORD PING

# 手动跑任务测试
docker compose -f deploy/docker-compose.yml exec web \
  python manage.py shell -c "from apps.blog.tasks import xxx; xxx.delay()"
```

### 磁盘满

```bash
# 看哪些卷占空间
docker system df

# 清理无用镜像
docker image prune -a

# 清理无用卷
docker volume prune
```

---

## 📈 性能调优

### Gunicorn 调参

`deploy/gunicorn.conf.py`：

```python
workers = int(os.environ.get("GUNICORN_WORKERS", 4))  # CPU * 2 + 1
worker_class = "gthread"
threads = 4  # 每 worker 线程数
```

**小内存机器**（4G）：workers=2, threads=2
**中内存机器**（8G）：workers=4, threads=4
**大内存机器**（16G+）：workers=8, threads=8

### MySQL 调参

`docker-compose.yml` 里 `--max-connections` 和 `--innodb-buffer-pool-size`：

```yaml
command: >
  --max-connections=200
  --innodb-buffer-pool-size=${DB_BUFFER_POOL_SIZE:-256M}
```

**小内存**：`DB_BUFFER_POOL_SIZE=128M`
**中内存**：`DB_BUFFER_POOL_SIZE=512M`
**大内存**：`DB_BUFFER_POOL_SIZE=2G`

### Redis 调参

```yaml
command: redis-server --requirepass $REDIS_PASSWORD \
  --maxmemory ${REDIS_MAXMEMORY:-256mb} \
  --maxmemory-policy allkeys-lru
```

---

## 🔐 安全运维

### 密钥轮换

```bash
# 1. 生成新 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 2. 改 .env
vim /opt/djangoblog/deploy/.env
# 改 SECRET_KEY / DB_PASSWORD / REDIS_PASSWORD

# 3. 重启服务
bash deploy/auto-deploy.sh restart
```

### 数据库密码轮换

```bash
# 1. 进 db 容器
docker compose -f deploy/docker-compose.yml exec db bash

# 2. 改 root 密码
mysql -u root -p$DB_ROOT_PASSWORD
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';
ALTER USER 'djangouser'@'%' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
exit

# 3. 改 .env 的 DB_PASSWORD
# 4. 重启
bash deploy/auto-deploy.sh restart
```

### 看安全审计

```bash
# 当前已通过的审计
cat deploy/FIX_PLAN.md  # 历史审计（已删除，参见 git history）

# 跑新审计（手动）
docker compose -f deploy/docker-compose.yml exec web \
  python manage.py check --deploy
```

---

## 📦 资源使用

```bash
# 实时资源
docker stats

# 持久化使用
bash deploy/health.sh info
```

输出：
```
====== 数据卷 ======
local     djangoblog_mysql_data    500M
local     djangoblog_redis_data    50M
====== 磁盘使用 ====
TYPE            TOTAL
Images          800M
Local Volumes   600M
====== 容器资源 ====
NAME                       CPU %   MEM USAGE
djangoblog-web             2.5%    256MiB
djangoblog-db              5%      384MiB
```

---

## 📞 紧急联系

| 场景 | 操作 |
|---|---|
| **网站完全挂** | `bash deploy/health.sh check` → 看是哪个服务 |
| **数据库损坏** | `bash deploy/restore.sh --latest` |
| **磁盘满** | `docker system prune -a`（清无用镜像）|
| **怀疑被攻击** | `bash deploy/health.sh logs` → 看异常 IP |
| **回滚版本** | `git checkout HEAD~1 && bash deploy/auto-deploy.sh update` |

---

## 🔗 相关文档

- [QUICKSTART.md](QUICKSTART.md) - 5 分钟上手
- [CI_DEPLOY.md](CI_DEPLOY.md) - 部署
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构
- [API.md](API.md) - API
