from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class AdminOverviewResponse(BaseModel):
    generated_at: datetime
    total_users: int
    today_distinct_visitors: int
    today_new_users: int
    today_visits: int
    online_users: int
    dhikring_users: int
    total_dhikr: int
    today_dhikr: int
    total_active_seconds: int
    today_active_seconds: int
    display_timezone: str


class AdminUserRow(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    display_name: str | None
    first_name: str | None
    onboarding_completed: bool
    created_at: datetime
    last_seen_at: datetime | None
    last_dhikr_at: datetime | None
    visit_count: int
    personal_dhikr_count: int
    personal_active_seconds: int


class AdminUsersResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminUserRow]


class AdminDailyPoint(BaseModel):
    date: str
    visitors: int
    dhikr: int
    active_seconds: int
    contributors: int


class AdminFunnelResponse(BaseModel):
    period_days: int
    completed_visits: int
    visits_with_dhikr: int
    left_without_dhikr: int
    new_users: int
    onboarded_new_users: int


class AdminDailyContributionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    local_date: date
    dhikr: int
    active_seconds: int
