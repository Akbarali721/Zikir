from app.config import Settings
from app.db.url import normalize_database_url


def test_railway_postgres_scheme():
    raw = "postgres://user:p%40ss@host.railway.app:5432/railway"
    out = normalize_database_url(raw)
    assert out.startswith("postgresql+asyncpg://")
    assert "user:p%40ss@host.railway.app:5432/railway" in out
    assert "ssl=require" in out


def test_postgresql_without_driver():
    raw = "postgresql://postgres:secret@127.0.0.1:5432/db"
    assert normalize_database_url(raw).startswith("postgresql+asyncpg://")


def test_preserves_local_asyncpg_without_forced_ssl():
    raw = "postgresql+asyncpg://postgres:postgres@localhost:5432/million_istighfor"
    assert normalize_database_url(raw) == raw


def test_settings_validator_normalizes(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://u:pass@db.example.com:5432/mydb",
    )
    s = Settings()
    assert s.database_url.startswith("postgresql+asyncpg://")
