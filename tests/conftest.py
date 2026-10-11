import os
import sys
from pathlib import Path

import pytest
import asyncpg

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _test_database_url() -> str:
    if os.getenv("TEST_DATABASE_URL"):
        return os.getenv("TEST_DATABASE_URL")
    from app.config import get_settings

    main = get_settings().database_url
    return main.rsplit("/", 1)[0] + "/million_istighfor_test"


def _pg_dsn_for_asyncpg(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def _can_connect() -> bool:
    url = _test_database_url()
    try:
        conn = await asyncpg.connect(_pg_dsn_for_asyncpg(url))
        await conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def integration_env():
    import asyncio

    test_url = _test_database_url()
    if not asyncio.run(_can_connect()):
        pytest.skip(
            f"Test PostgreSQL ulanmadi: {test_url}. "
            "scripts/ensure_test_db.py ni ishga tushiring."
        )

    os.environ["DATABASE_URL"] = test_url
    os.environ["ENABLE_INTEGRATION_TEST_AUTH"] = "1"
    os.environ["DEBUG"] = "false"
    os.environ["ADMIN_TELEGRAM_IDS"] = "900000001"
    from app.config import get_settings

    get_settings.cache_clear()
    import importlib
    import app.db.database as database

    importlib.reload(database)
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def integration_app(integration_env):
    from app.main import create_app

    return create_app()


