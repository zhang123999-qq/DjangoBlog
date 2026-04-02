# 修复验证报告

## ✅ 修复1：manage_project.py - clean() 排除 .venv 目录
**修复前**：`rglob("__pycache__")` 会清理 `.venv` 内的缓存
**修复后**：添加 `EXCLUDE_DIRS = {".venv", ".git", "node_modules"}` 排除规则
**额外**：同时清理 `htmlcov`、`allure-results` 测试产物

## ✅ 修复2：manage_project.py - test() 改用 pytest
**修复前**：`uv run python manage.py test`（Django 自带测试框架）
**修复后**：`uv run pytest`（项目实际使用的 pytest）

## ✅ 修复3：migrate_to_mysql.py - 使用 ORM 获取真实表名
**修复前**：硬编码表名（如 `accounts_user`、`accounts_profile` 等）
**修复后**：使用 `User._meta.db_table`、`Profile._meta.db_table` 等 ORM 方法
**影响**：10 个表全部从硬编码改为动态获取

## ✅ 修复4：migrate_to_mysql.py - 硬编码改为动态获取
**影响表**：user、profile、category、tag、post、comment、board、topic、reply
**保留**：`blog_post_tags` 是 M2M 中间表，保留硬编码（ORM 不直接提供）

## ✅ 修复5：start.py - 增加 uv Python 路径检测
**修复前**：只检查 `.venv/Scripts/python.exe`（在 uv 环境下找不到）
**修复后**：
1. 先检查 `.venv` 虚拟环境
2. 再检查 `.python-version` + uv 管理的 Python 路径
3. 回退到当前运行的 Python

## ✅ 修复6：start.py - 增加 uv Python 路径检测
**同上，已合并到修复5中**