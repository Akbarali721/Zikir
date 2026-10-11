from datetime import datetime, timezone

from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def complete_onboarding(user: User, display_name: str, age: int) -> User:
    user.display_name = display_name
    user.age = age
    user.onboarding_completed = True
    user.onboarding_completed_at = _utcnow()
    return user
