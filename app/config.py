from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db.url import normalize_database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/million_istighfor"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_database_url(value)
        return value

    telegram_bot_token: str = ""
    # Telegram WebApp ochiladigan asosiy URL (oxiri / bilan yoki bo‘lmasin — bot normalize qiladi).
    telegram_webapp_url: str = ""
    # Production webhook: public app URL (path qo‘shilmaydi), masalan https://app.railway.app
    telegram_webhook_base_url: str = ""
    # setWebhook secret_token — Telegram X-Telegram-Bot-Api-Secret-Token header.
    telegram_webhook_secret: str = ""
    # Bot webhook/polling faollashtirish (token bo‘lsa ham o‘chirish mumkin).
    telegram_bot_enabled: bool = True
    debug: bool = False
    dev_telegram_id: int | None = None

    # Sync validation limits (MVP)
    max_dhikr_delta_per_sync: int = 500
    max_active_seconds_delta_per_sync: int = 120

    # Session inactivity (backend may close stale sessions)
    session_idle_timeout_seconds: int = 90

    # Calendar day for "Bugungi hissam" (user_daily_contributions.local_date).
    display_timezone: str = "Asia/Tashkent"

    # Comma-separated Telegram user IDs allowed for /api/admin/* (empty = nobody).
    admin_telegram_ids: str = ""

    visit_idle_timeout_minutes: int = 30
    online_window_seconds: int = 60
    dhikring_window_seconds: int = 60

    # Faqat pytest/integration test (ENABLE_INTEGRATION_TEST_AUTH=1). Production'da false.
    enable_integration_test_auth: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
