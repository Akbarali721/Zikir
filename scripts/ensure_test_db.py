"""Test bazasini yaratish va migratsiya (asosiy DB ga tegmaydi)."""
import asyncio
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncpg
from app.config import get_settings


def _derive_urls():
    settings = get_settings()
    main = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    # .../dbname
    if "/" not in main:
        raise SystemExit("DATABASE_URL not understood")
    base, _ = main.rsplit("/", 1)
    test_name = os.getenv("TEST_DB_NAME", "million_istighfor_test")
    admin_url = base + "/postgres"
    test_async = settings.database_url.rsplit("/", 1)[0] + "/" + test_name
    return admin_url, test_name, test_async


async def main():
    admin_url, test_name, test_async = _derive_urls()
    conn = await asyncpg.connect(admin_url)
    row = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", test_name)
    if not row:
        await conn.execute(f'CREATE DATABASE "{test_name}"')
        print(f"Created database {test_name}")
    else:
        print(f"Database {test_name} already exists")
    await conn.close()

    env = os.environ.copy()
    env["DATABASE_URL"] = test_async
    subprocess.check_call([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=str(ROOT), env=env)
    print("Alembic upgrade head on test DB OK")
    print(f"TEST_DATABASE_URL={test_async}")


if __name__ == "__main__":
    asyncio.run(main())
