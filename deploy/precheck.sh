#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/docker-compose.yml"
ENV_FILE="$ROOT_DIR/.env"

PASS=0
WARN=0
FAIL=0

ok(){ echo "[PASS] $1"; PASS=$((PASS+1)); }
warn(){ echo "[WARN] $1"; WARN=$((WARN+1)); }
fail(){ echo "[FAIL] $1"; FAIL=$((FAIL+1)); }

check_cmd(){
  local cmd="$1"; local name="$2"
  if command -v "$cmd" >/dev/null 2>&1; then ok "$name 已安装"; else fail "$name 未安装"; fi
}

check_port(){
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    if ss -ltn | awk '{print $4}' | grep -E ":${port}$" >/dev/null 2>&1; then
      warn "端口 ${port} 已被占用"
    else
      ok "端口 ${port} 可用"
    fi
  elif command -v netstat >/dev/null 2>&1; then
    if netstat -ltn 2>/dev/null | grep -E ":${port}[[:space:]]" >/dev/null 2>&1; then
      warn "端口 ${port} 已被占用"
    else
      ok "端口 ${port} 可用"
    fi
  else
    warn "无法检测端口 ${port}（缺少 ss/netstat）"
  fi
}

check_required_env(){
  local key="$1"
  if [ -f "$ENV_FILE" ] && grep -E "^${key}=" "$ENV_FILE" >/dev/null 2>&1; then
    local value
    value=$(grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d'=' -f2-)
    if [ -z "$value" ]; then
      fail "${key} 为空"
    elif [[ "$value" =~ your- ]] || [[ "$value" =~ change-in-production ]]; then
      fail "${key} 仍是占位符"
    else
      ok "${key} 已配置"
    fi
  else
    fail "缺少 ${key}"
  fi
}

check_expected_env(){
  local key="$1"
  local expected="$2"
  if [ ! -f "$ENV_FILE" ]; then
    fail "缺少 .env，无法校验 ${key}"
    return
  fi

  local value
  value=$(grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d'=' -f2- || true)
  if [ -z "$value" ]; then
    fail "${key} 缺失或为空"
    return
  fi

  if [ "$value" = "$expected" ]; then
    ok "${key}=${expected}"
  else
    fail "${key}=${value}（期望 ${expected}）"
  fi
}

echo "============================================================"
echo " DjangoBlog 部署前预检"
echo "============================================================"

# 1) 基础命令
check_cmd docker "Docker"
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then ok "Docker daemon 运行中"; else fail "Docker daemon 未运行"; fi
fi

# 2) Compose
if docker compose version >/dev/null 2>&1; then
  ok "Docker Compose 可用"
else
  fail "Docker Compose 不可用（docker compose）"
fi

# 3) compose 文件
if [ -f "$COMPOSE_FILE" ]; then ok "docker-compose.yml 存在"; else fail "缺少 $COMPOSE_FILE"; fi

# 4) .env
if [ -f "$ENV_FILE" ]; then
  ok ".env 存在"
else
  fail "缺少 .env（请先 cp deploy/.env.docker.example .env）"
fi

# 5) 必填变量
check_required_env SECRET_KEY
check_required_env DB_NAME
check_required_env DB_USER
check_required_env DB_PASSWORD
check_required_env MYSQL_ROOT_PASSWORD
check_required_env ALLOWED_HOSTS
check_required_env CSRF_TRUSTED_ORIGINS

# 生产安全开关（P0）
check_required_env DEBUG
check_required_env SECURE_SSL_REDIRECT
check_required_env SESSION_COOKIE_SECURE
check_required_env CSRF_COOKIE_SECURE
check_required_env SECURE_HSTS_SECONDS

check_expected_env DEBUG False
check_expected_env SECURE_SSL_REDIRECT True
check_expected_env SESSION_COOKIE_SECURE True
check_expected_env CSRF_COOKIE_SECURE True

# HSTS 需 > 0
if [ -f "$ENV_FILE" ]; then
  hsts_val=$(grep -E '^SECURE_HSTS_SECONDS=' "$ENV_FILE" | tail -n1 | cut -d'=' -f2-)
  if [[ "$hsts_val" =~ ^[0-9]+$ ]] && [ "$hsts_val" -gt 0 ]; then
    ok "SECURE_HSTS_SECONDS=${hsts_val}"
  else
    fail "SECURE_HSTS_SECONDS=${hsts_val}（期望 > 0）"
  fi
fi

# 6) 端口占用
check_port 80
check_port 8000

# 7) compose 语法校验
if [ -f "$ENV_FILE" ]; then
  if docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
    ok "Compose 配置校验通过"
  else
    fail "Compose 配置校验失败"
  fi
fi

# 8) DNS 基础检查（可选）
if [ -f "$ENV_FILE" ]; then
  hosts_val=$(grep -E '^ALLOWED_HOSTS=' "$ENV_FILE" | tail -n1 | cut -d'=' -f2-)
  first_host=$(echo "$hosts_val" | cut -d',' -f1)
  if [ -n "$first_host" ] && [[ "$first_host" != "localhost" ]] && [[ "$first_host" != "127.0.0.1" ]]; then
    if command -v nslookup >/dev/null 2>&1; then
      if nslookup "$first_host" >/dev/null 2>&1; then ok "域名 ${first_host} 可解析"; else warn "域名 ${first_host} 暂不可解析"; fi
    else
      warn "未安装 nslookup，跳过域名解析检查"
    fi
  else
    warn "ALLOWED_HOSTS 首域名为本地地址，跳过 DNS 检查"
  fi
fi

# 9) 磁盘空间（可选）
if command -v df >/dev/null 2>&1; then
  avail_mb=$(df -Pm "$ROOT_DIR" | awk 'NR==2{print $4}')
  if [ -n "$avail_mb" ] && [ "$avail_mb" -ge 2048 ]; then
    ok "可用磁盘空间充足（>=2GB）"
  else
    warn "可用磁盘空间较低（建议 >=2GB）"
  fi
fi

# 10) 回滚命令提示
ok "回滚命令可用：bash deploy/down.sh 或 bash deploy/down.sh --purge"

echo "------------------------------------------------------------"
echo "结果：PASS=$PASS WARN=$WARN FAIL=$FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo "预检未通过，请先修复 FAIL 项。"
  exit 1
else
  echo "预检通过，可执行部署。"
fi
