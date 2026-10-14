"""PostgreSQL URL ni async SQLAlchemy (asyncpg) uchun xavfsiz normalize qilish."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def normalize_database_url(raw: str) -> str:
    """
    Railway/Heroku ko‘pincha postgres:// yoki postgresql:// beradi.
    Loyiha faqat postgresql+asyncpg ishlatadi (psycopg2 talab qilinmaydi).
    """
    url = (raw or "").strip()
    if not url:
        return url

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()

    if scheme in ("postgresql", "postgres"):
        scheme = "postgresql+asyncpg"
    elif scheme == "postgresql+asyncpg":
        pass
    elif scheme.startswith("postgresql+"):
        scheme = "postgresql+asyncpg"
    else:
        return url

    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    cleaned: list[tuple[str, str]] = []
    for key, value in query_pairs:
        k = key.lower()
        if k in ("sslmode", "channel_binding"):
            continue
        cleaned.append((key, value))

    host = (parsed.hostname or "").lower()
    is_local = host in ("localhost", "127.0.0.1", "::1")
    if not is_local and not any(k.lower() == "ssl" for k, _ in cleaned):
        cleaned.append(("ssl", "require"))

    query = urlencode(cleaned) if cleaned else ""

    return urlunparse(
        (
            scheme,
            parsed.netloc,
            parsed.path or "",
            parsed.params,
            query,
            parsed.fragment,
        )
    )


def alembic_config_url(database_url: str) -> str:
    """ConfigParser % belgisini buzmasligi uchun Alembic ga maxsus escape."""
    return normalize_database_url(database_url).replace("%", "%%")
