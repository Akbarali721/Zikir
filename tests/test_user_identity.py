from app.models.user import User
from app.services.user_identity_service import preferred_display_name, sync_profile_from_telegram


def test_auto_onboarding_from_telegram():
    user = User(telegram_id=99, first_name="Ali", onboarding_completed=False)
    sync_profile_from_telegram(user, {"id": 99, "first_name": "Ali", "username": "ali"})
    assert user.onboarding_completed is True
    assert user.display_name == "Ali"


def test_preferred_display_name_keeps_legacy_display_name():
    user = User(telegram_id=1, display_name="Eski ism", first_name="Yangi")
    assert preferred_display_name(user) == "Eski ism"


def test_returning_user_keeps_data():
    user = User(
        telegram_id=1,
        display_name="Saqlangan",
        personal_dhikr_count=500,
        onboarding_completed=True,
    )
    sync_profile_from_telegram(user, {"id": 1, "first_name": "TG"})
    assert user.display_name == "Saqlangan"
    assert user.personal_dhikr_count == 500
