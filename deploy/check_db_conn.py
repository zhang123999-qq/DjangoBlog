"""数据库连接预检查（用于 deploy/precheck.bat）

返回码：
- 0: 连接成功并可执行 SELECT 1
- 1: 连接失败
"""

from __future__ import annotations

import sys
from pathlib import Path

import pymysql


def load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def main() -> int:
    env_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".env")
    env = load_env(env_path)

    db_engine = env.get("DB_ENGINE", "")
    if "sqlite" in db_engine:
        print("DB_OK sqlite mode")
        return 0

    host = env.get("DB_HOST", "127.0.0.1")
    port = int(env.get("DB_PORT", "3306"))
    user = env.get("DB_USER", "")
    password = env.get("DB_PASSWORD", "")
    database = env.get("DB_NAME", "")

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=3,
            read_timeout=3,
            write_timeout=3,
            charset="utf8mb4",
            autocommit=True,
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        finally:
            conn.close()

        print(f"DB_OK {host}:{port} db={database} user={user}")
        return 0
    except Exception as e:
        print(f"DB_FAIL {host}:{port} db={database} user={user} err={e!r}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
