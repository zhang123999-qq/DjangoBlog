# DjangoBlog Makefile
# 使用方法: make <target>

.PHONY: help install dev test lint format clean docker-up docker-down

# 默认目标
.DEFAULT_GOAL := help

# ============================================================
# 帮助信息
# ============================================================
help: ## 显示帮助信息
	@echo "DjangoBlog 开发命令:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ============================================================
# 安装与设置
# ============================================================
install: ## 安装开发依赖
	pip install uv
	uv venv
	uv pip install -r requirements/development.lock
	pre-commit install

setup: install ## 完整设置（安装 + pre-commit）
	pre-commit run --all-files

# ============================================================
# 开发服务器
# ============================================================
dev: ## 启动开发服务器
	python manage.py runserver 0.0.0.0:8000

celery: ## 启动 Celery Worker
	celery -A config worker --loglevel=info

celery-beat: ## 启动 Celery Beat
	celery -A config beat --loglevel=info

# ============================================================
# 测试
# ============================================================
test: ## 运行所有测试
	pytest -v

test-cov: ## 运行测试并生成覆盖率报告
	pytest --cov=apps --cov-report=html --cov-report=term

test-quick: ## 快速测试（跳过慢测试）
	pytest -v -m "not slow"

test-smoke: ## 冒烟测试
	pytest -v -m smoke

# ============================================================
# 代码质量
# ============================================================
lint: ## 代码检查 (flake8 + mypy)
	flake8 apps/ --max-line-length=120 --ignore=E203,W503,E501
	mypy apps/ --ignore-missing-imports

format: ## 格式化代码 (black + isort)
	black apps/ --line-length=120
	isort apps/ --profile=black --line-length=120

format-check: ## 检查代码格式
	black --check apps/ --line-length=120
	isort --check-only apps/ --profile=black --line-length=120

pre-commit: ## 运行 pre-commit 检查
	pre-commit run --all-files

# ============================================================
# 数据库
# ============================================================
migrate: ## 执行数据库迁移
	python manage.py migrate

makemigrations: ## 创建迁移文件
	python manage.py makemigrations

db-reset: ## 重置数据库（警告：删除所有数据）
	python manage.py flush --noinput
	python manage.py migrate

# ============================================================
# Docker
# ============================================================
docker-up: ## 启动 Docker 服务
	docker compose -f deploy/docker-compose.yml up -d

docker-down: ## 停止 Docker 服务
	docker compose -f deploy/docker-compose.yml down

docker-logs: ## 查看 Docker 日志
	docker compose -f deploy/docker-compose.yml logs -f --tail=50

docker-rebuild: ## 重建 Docker 镜像
	docker compose -f deploy/docker-compose.yml build --no-cache

# ============================================================
# 清理
# ============================================================
clean: ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .pytest_cache/ .coverage .mypy_cache/ 2>/dev/null || true
	rm -rf staticfiles/ 2>/dev/null || true

clean-all: clean ## 深度清理（包括数据库）
	rm -f db.sqlite3 test_db.sqlite3 2>/dev/null || true

# ============================================================
# 实用工具
# ============================================================
check: ## 完整检查（格式 + lint + 测试）
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test

shell: ## Django Shell
	python manage.py shell

superuser: ## 创建超级管理员
	python manage.py createsuperuser

stats: ## 显示代码统计
	@echo "Python 文件统计:"
	@find apps -name "*.py" | wc -l | xargs echo "  文件数量:"
	@find apps -name "*.py" -exec wc -l {} + | tail -1 | awk '{print "  总行数: " $$1}'
