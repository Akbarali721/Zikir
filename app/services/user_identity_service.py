from datetime import datetime, timezone

from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def preferred_display_name(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    if user.first_name and user.first_name.strip():
        return user.first_name.strip()
    if user.username:
        return f"@{user.username}"
    return "do‘st"


def sync_profile_from_telegram(user: User, tg_user: dict | None = None) -> None:
    """Ism/yosh formasiz: Telegram first_name / username asosida ko‘rinish nomi."""
    if tg_user:
        user.username = tg_user.get("username") or user.username
        user.first_name = tg_user.get("first_name") or user.first_name
        user.last_name = tg_user.get("last_name") or user.last_name

    if not user.display_name or not user.display_name.strip():
        fn = user.first_name
        if fn and fn.strip():
            user.display_name = fn.strip()[:50]

    if not user.onboarding_completed:
        user.onboarding_completed = True
        user.onboarding_completed_at = user.onboarding_completed_at or _utcnow()


def bind_telegram_chat(user: User, chat_id: int | None) -> None:
    if chat_id is None:
        return
    user.telegram_chat_id = int(chat_id)
