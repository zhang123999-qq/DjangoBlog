# Git 更新指南

> 本文档介绍如何安全地使用 `git pull` 更新项目，确保数据库和已发布内容不受影响。

---

## 目录

1. [Git Pull 基础](#git-pull-基础)
2. [Git 不会改变的内容](#git-不会改变的内容)
3. [安全更新流程](#安全更新流程)
4. [常见问题处理](#常见问题处理)
5. [生产环境更新](#生产环境更新)

---

## Git Pull 基础

### 什么是 git pull？

```bash
git pull = git fetch + git merge
```

- `git fetch`：从远程仓库获取最新代码（不合并）
- `git merge`：将获取的代码合并到当前分支
- `git pull`：一步完成获取和合并

### 基本用法

```bash
# 拉取当前分支的最新代码
git pull

# 指定远程和分支
git pull origin main

# 拉取并变基（保持提交历史线性）
git pull --rebase origin main
```

---

## Git 不会改变的内容

### 📋 受保护文件列表

| 文件/目录 | 是否更新 | 说明 |
|-----------|----------|------|
| `db.sqlite3` | ❌ 不更新 | 数据库文件在 `.gitignore` 中 |
| `media/` | ❌ 不更新 | 用户上传的图片、文件 |
| `.env` | ❌ 不更新 | 环境变量配置 |
| `logs/` | ❌ 不更新 | 日志文件 |
| `*.pyc` | ❌ 不更新 | Python 编译文件 |
| `.venv/` | ❌ 不更新 | 虚拟环境 |

### ✅ 会更新的内容

| 文件类型 | 是否更新 | 说明 |
|----------|----------|------|
| `*.py` | ✅ 更新 | Python 代码 |
| `*.html` | ✅ 更新 | 模板文件 |
| `*.css` | ✅ 更新 | 样式文件 |
| `*.js` | ✅ 更新 | JavaScript 文件 |
| `migrations/` | ✅ 更新 | 数据库迁移文件 |
| `requirements*.txt` | ✅ 更新 | 依赖列表 |

### 📁 .gitignore 配置

项目已配置以下保护规则：

```gitignore
# 数据库
db.sqlite3
db.sqlite3-journal

# 用户上传文件
media/

# 环境配置
.env
.env.local

# 日志
logs/
*.log

# Python
__pycache__/
*.pyc
.venv/
```

---

## 安全更新流程

### 标准流程

```bash
# 步骤 1: 查看当前状态
git status

# 步骤 2: 备份数据库（可选但推荐）
cp db.sqlite3 db.sqlite3.backup

# 步骤 3: 暂存本地修改（如果有）
git stash

# 步骤 4: 拉取最新代码
git pull origin main

# 步骤 5: 恢复本地修改
git stash pop

# 步骤 6: 更新依赖
uv sync

# 步骤 7: 检查并执行迁移
python manage.py showmigrations
python manage.py migrate

# 步骤 8: 收集静态文件
python manage.py collectstatic --noinput
```

### 使用更新脚本

```bash
# Windows
.\scripts\safe_update.bat

# Linux/Mac
./scripts/safe_update.sh
```

---

## 常见问题处理

### 问题 1: 本地有未提交的修改

**现象**：
```
error: Your local changes to the following files would be overwritten by merge
```

**解决方案**：
```bash
# 方案 A: 暂存后更新
git stash
git pull origin main
git stash pop

# 方案 B: 提交后更新
git add .
git commit -m "本地修改"
git pull origin main

# 方案 C: 放弃本地修改
git checkout -- .
git pull origin main
```

---

### 问题 2: 迁移冲突

**现象**：
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**解决方案**：
```bash
# 查看迁移状态
python manage.py showmigrations

# 如果是新迁移，直接执行
python manage.py migrate

# 如果是冲突，可能需要 fake 迁移（谨慎使用）
python manage.py migrate --fake app_name migration_name
```

---

### 问题 3: 依赖冲突

**现象**：
```
ERROR: Cannot install package due to conflicts
```

**解决方案**：
```bash
# 清理并重新安装
rm -rf .venv
uv sync

# 或者更新特定包
uv pip install --upgrade package_name
```

---

### 问题 4: 合并冲突

**现象**：
```
CONFLICT (content): Merge conflict in file.py
```

**解决方案**：
```bash
# 查看冲突文件
git status

# 手动编辑冲突文件，解决冲突标记
# <<<<<<< HEAD
# 本地修改
# =======
# 远程修改
# >>>>>>> origin/main

# 解决后提交
git add file.py
git commit -m "解决合并冲突"
```

---

## 生产环境更新

### 🚨 更新前检查清单

- [ ] 备份数据库
- [ ] 备份 `.env` 配置
- [ ] 备份 `media/` 目录
- [ ] 通知用户维护时间
- [ ] 确认有回滚方案

### 更新步骤

```bash
# 1. 进入维护模式
touch maintenance.flag

# 2. 备份
cp db.sqlite3 backups/db.sqlite3.$(date +%Y%m%d_%H%M%S)
tar -czf backups/media_$(date +%Y%m%d_%H%M%S).tar.gz media/

# 3. 拉取代码
git fetch origin
git reset --hard origin/main

# 4. 更新依赖
uv sync

# 5. 执行迁移
python manage.py migrate

# 6. 收集静态文件
python manage.py collectstatic --noinput

# 7. 重启服务
systemctl restart djangoblog  # 或 supervisorctl restart djangoblog

# 8. 测试
curl http://localhost:8000/healthz/

# 9. 移除维护模式
rm maintenance.flag
```

### 回滚方案

```bash
# 如果更新失败，快速回滚

# 1. 回滚代码
git reset --hard HEAD~1
# 或回到指定版本
git reset --hard <commit_hash>

# 2. 恢复数据库
cp backups/db.sqlite3.YYYYMMDD_HHMMSS db.sqlite3

# 3. 重启服务
systemctl restart djangoblog
```

---

## 附录

### Git 常用命令速查

| 命令 | 说明 |
|------|------|
| `git status` | 查看当前状态 |
| `git log --oneline -10` | 查看最近10条提交 |
| `git diff` | 查看未暂存的修改 |
| `git stash` | 暂存当前修改 |
| `git stash pop` | 恢复暂存的修改 |
| `git pull origin main` | 拉取远程 main 分支 |
| `git fetch origin` | 只获取不合并 |
| `git branch -a` | 查看所有分支 |
| `git checkout -b feature` | 创建并切换新分支 |

### 相关文档

- [项目结构说明](PROJECT_STRUCTURE.md)
- [配置说明](CONFIGURATION.md)
- [快速开始](QUICKSTART.md)

---

**最后更新**: 2026-03-23  
**作者**: 小欣
