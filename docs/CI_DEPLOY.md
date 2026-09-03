# 🚀 DjangoBlog CI/CD 部署指南

> 完整说明 GitHub Actions 自动部署 + 手动部署 + 回滚流程

---

## 📋 目录

- [架构总览](#架构总览)
- [GitHub Actions 自动部署](#github-actions-自动部署)
- [配置 Secrets](#配置-secrets)
- [首次手动部署](#首次手动部署)
- [日常部署流程](#日常部署流程)
- [回滚方案](#回滚方案)
- [故障排查](#故障排查)

---

## 🏗 架构总览

```
开发机 / IDE
  │
  ├─ git push origin main
  │
  ▼
GitHub Repository
  │
  ├─ 触发 .github/workflows/ci.yml（测试）
  ├─ 触发 .github/workflows/deploy.yml（部署）★
  └─ 触发 .github/workflows/scheduled.yml（每周安全扫描）
  │
  ▼
生产服务器
  ├─ git pull
  ├─ auto-deploy.sh update（增量部署）
  ├─ health.sh check（健康检查）
  └─ 失败自动回滚
```

---

## ⚙️ GitHub Actions 自动部署

### 工作流位置

`.github/workflows/deploy.yml`

### 触发条件

| 触发方式 | 场景 |
|---|---|
| **push 到 main** | 推送代码即自动部署（推荐）|
| **workflow_dispatch** | GitHub 网页手动触发（可指定环境）|

### 部署步骤（10 步）

1. ✅ 检出代码
2. 🔑 配置 SSH 密钥
3. 📝 记录部署信息（commit SHA/作者/时间）
4. 🩺 部署前健康检查
5. 💾 备份当前数据库
6. 📥 拉取最新代码（`git pull`）
7. 🚀 执行增量部署（`auto-deploy.sh update`）
8. ✅ 部署后健康检查
9. 📢 通知部署成功（钉钉 Webhook）
10. ❌ 失败时回滚 + 告警

### 特性

- ✅ **自动并发控制**（同一时间只允许一个部署）
- ✅ **自动备份**（每次部署前自动 mysqldump）
- ✅ **自动回滚**（部署失败时 `git checkout HEAD~1`）
- ✅ **健康检查**（部署前后都跑）
- ✅ **钉钉通知**（成功/失败分别推送）
- ✅ **paths-ignore**（文档改动不触发部署）

---

## 🔐 配置 Secrets

在 GitHub 仓库 **Settings → Secrets and variables → Actions** 添加以下 secrets：

| Secret 名称 | 说明 | 示例 |
|---|---|---|
| `SSH_PRIVATE_KEY` | SSH 私钥（用于连接服务器）| `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SSH_HOST` | 服务器 IP 或域名 | `1.2.3.4` |
| `SSH_USER` | SSH 用户名 | `deploy` |
| `SSH_PORT` | SSH 端口 | `22` |
| `PROJECT_DIR` | 项目部署路径 | `/opt/djangoblog` |
| `PRODUCTION_URL` | 生产环境 URL（显示在 Actions 页面）| `https://www.example.com` |
| `DINGTALK_WEBHOOK` | 钉钉机器人 Webhook（可选）| `https://oapi.dingtalk.com/robot/send?access_token=...` |

### 生成 SSH 密钥对（服务器端）

```bash
# 在本地生成密钥对（用 deploy 专用密钥）
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/deploy_key

# 把公钥加到服务器
ssh-copy-id -i ~/.ssh/deploy_key.pub deploy@your-server

# 私钥填到 GitHub Secret SSH_PRIVATE_KEY
cat ~/.ssh/deploy_key
```

### 服务器端免密登录准备

```bash
# 1. 创建 deploy 用户
useradd -m -s /bin/bash deploy

# 2. 加入 docker 组（避免每次 sudo）
usermod -aG docker deploy

# 3. 配置 sudoers（可选）
echo "deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx" >> /etc/sudoers.d/deploy

# 4. 验证 deploy 用户能跑 docker
su - deploy
docker ps
```

---

## 🆕 首次手动部署

> 即使有 CI，也建议**首次手动部署**一次，确认环境 OK

### 1. SSH 到服务器

```bash
ssh deploy@your-server
```

### 2. 克隆代码

```bash
sudo mkdir -p /opt/djangoblog
sudo chown deploy:deploy /opt/djangoblog
cd /opt/djangoblog
git clone https://github.com/zhang123999-qq/DjangoBlog.git .
```

### 3. 运行一键部署

```bash
cd /opt/djangoblog
sudo bash deploy/auto-deploy.sh
```

按提示输入：
- 域名
- 管理员用户名/邮箱/密码

### 4. 安装 Nginx

```bash
sudo bash deploy/install_nginx.sh
# 或宝塔面板: sudo bash deploy/install_nginx.sh bt
# 或前端分离: sudo bash deploy/install_nginx.sh frontend
```

### 5. 配置定时任务

```bash
crontab -e
# 粘贴 deploy/crontab.example 内容
```

### 6. 验证

```bash
bash deploy/health.sh check
curl https://your-domain/healthz/
```

---

## 🔄 日常部署流程

### 推荐：推到 main 即部署

```bash
# 本地开发
git add .
git commit -m "feat: 新功能"
git push origin main

# GitHub Actions 自动触发：
# 1. CI 测试通过
# 2. Deploy 工作流开始
# 3. 自动部署到生产
# 4. 钉钉通知成功/失败
```

### 手动触发（生产事故修复）

```
GitHub → Actions → Deploy to Production → Run workflow
  ├─ environment: production
  └─ 点击绿色按钮
```

### Staging 环境（可选）

```bash
# 创建 staging 分支
git checkout -b staging
git push origin staging

# 修改 .github/workflows/deploy.yml 添加：
# on:
#   push:
#     branches: ["main", "staging"]
```

---

## ⏪ 回滚方案

### 方案 1：自动回滚（推荐）

Deploy 工作流已内置：
- 步骤 7 失败 → 自动 `git checkout HEAD~1` + 重新部署
- 钉钉推送告警

### 方案 2：手动回滚

```bash
ssh deploy@your-server
cd /opt/djangoblog

# 查看最近 5 个提交
git log --oneline -5

# 回滚到上一个版本
git checkout HEAD~1
bash deploy/auto-deploy.sh update

# 或回到指定 commit
git checkout abc1234
bash deploy/auto-deploy.sh update
```

### 方案 3：用备份恢复

```bash
# 列出所有备份
bash deploy/restore.sh --list

# 恢复到最新备份
bash deploy/restore.sh --latest
```

---

## 🔍 故障排查

### 查看部署日志

```
GitHub → Actions → 选择失败的 run → 查看日志
```

### 查看服务日志

```bash
# SSH 到服务器
bash deploy/health.sh logs         # 所有服务
bash deploy/health.sh logs-web     # 只看 web
bash deploy/health.sh logs-db      # 只看 db
bash deploy/health.sh logs-celery  # 只看 celery
```

### 常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| **SSH 连接失败** | 密钥/端口错 | 检查 GitHub Secrets 配置 |
| **git pull 失败** | 服务器无权限 / 分支保护 | 服务器用 deploy token，关闭 main 保护 |
| **docker build 慢** | 镜像没缓存 | 用 BuildKit cache（已配）|
| **/healthz/ 500** | 数据库未就绪 | 等 30 秒重试，检查 db 日志 |
| **Nginx 502** | web 容器挂了 | `docker compose logs web` |

---

## 📊 监控建议

部署完建议接入：

| 工具 | 用途 |
|---|---|
| **UptimeRobot** | URL 监控（/healthz/） |
| **Sentry** | Django 错误追踪 |
| **Prometheus + Grafana** | 容器/数据库指标 |
| **Loki** | 日志聚合 |
| **钉钉机器人** | 部署告警（已配）|

---

## 📝 注意事项

- 🔴 **生产部署前一定在 staging 测过**
- 🔴 **每次部署前会自动备份数据库**（保留 7 天）
- 🟡 **改 docker-compose.yml 后第一次部署会重建容器**（短暂停机）
- 🟢 **代码改动（仅 Python）不重建镜像也能热重启 web 容器**

---

## 🔗 相关文件

- `deploy/auto-deploy.sh` - 一键部署主脚本
- `deploy/docker-compose.yml` - 5 容器编排
- `deploy/Dockerfile` - 多阶段构建
- `deploy/gunicorn.conf.py` - Gunicorn 配置
- `deploy/nginx.*.conf` - 3 种 Nginx 配置
- `deploy/health.sh` - 健康检查
- `deploy/backup.sh` / `deploy/restore.sh` - 备份恢复
- `deploy/install_nginx.sh` - Nginx 一键安装
- `.github/workflows/deploy.yml` - 自动部署工作流
- `.github/workflows/ci.yml` - CI 测试
