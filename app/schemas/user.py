from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TelegramUserData(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class SessionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mode: str
    challenge_type: str = "million_istighfor"
    dhikr_count: int
    active_seconds: int
    is_active: bool
    started_at: datetime
    counts_for_today: bool = True


class TodayContribution(BaseModel):
    dhikr: int
    active_seconds: int


class RetentionInfo(BaseModel):
    is_returning: bool
    global_growth_since_last_visit: int | None = None
    display_timezone: str = "UTC"


class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: TelegramUserData
    personal_dhikr_count: int
    personal_active_seconds: int
    display_name: str | None = None
    age: int | None = None
    onboarding_completed: bool = False
    is_admin: bool = False
    leaderboard_opt_in: bool = False
    today: TodayContribution
    retention: RetentionInfo
    session: SessionBrief | None = None
