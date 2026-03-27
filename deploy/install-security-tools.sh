#!/usr/bin/env bash
set -euo pipefail

WITH_GITLEAKS="${1:-}"

echo "[setup] Installing Python security tools via uv tool..."
for t in bandit pip-audit; do
  if uv tool install "$t"; then
    echo "[ok] installed: $t"
  else
    echo "[warn] install failed: $t"
  fi
done

if [[ "$WITH_GITLEAKS" == "--with-gitleaks" ]]; then
  echo "[setup] Trying to install gitleaks..."
  if command -v gitleaks >/dev/null 2>&1; then
    echo "[ok] gitleaks already installed"
  elif command -v brew >/dev/null 2>&1; then
    brew install gitleaks || echo "[warn] brew install gitleaks failed"
  elif command -v apt-get >/dev/null 2>&1; then
    echo "[warn] apt source may not include gitleaks by default; install manually if needed"
  else
    echo "[warn] package manager not found, install gitleaks manually: https://github.com/gitleaks/gitleaks"
  fi
fi

echo "[setup] Verifying tools..."
for c in bandit pip-audit gitleaks; do
  if command -v "$c" >/dev/null 2>&1; then
    echo "[ok] $c"
  else
    echo "[skip] $c not found"
  fi
done

echo "[done] security tool setup complete"
