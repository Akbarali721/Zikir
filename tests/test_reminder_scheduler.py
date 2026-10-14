from zoneinfo import ZoneInfo

from app.config import Settings


def test_scheduler_uses_display_timezone(monkeypatch):
    monkeypatch.setenv("DISPLAY_TIMEZONE", "Asia/Tashkent")
    s = Settings()
    tz = ZoneInfo(s.display_timezone)
    assert str(tz) == "Asia/Tashkent"
