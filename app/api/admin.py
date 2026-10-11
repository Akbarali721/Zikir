from fastapi import APIRouter, HTTPException, Query

from app.api.admin_deps import AdminUser
from app.api.deps import DbSession
from app.schemas.admin import AdminDailyPoint, AdminFunnelResponse, AdminOverviewResponse, AdminUsersResponse
from app.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewResponse)
async def admin_overview(db: DbSession, _admin: AdminUser) -> AdminOverviewResponse:
    data = await admin_service.get_overview(db)
    return AdminOverviewResponse(**data)


@router.get("/users", response_model=AdminUsersResponse)
async def admin_users(
    db: DbSession,
    _admin: AdminUser,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    onboarding: str | None = Query(None, pattern="^(completed|pending)$"),
    online_only: bool = False,
) -> AdminUsersResponse:
    data = await admin_service.list_users(
        db, q=q, page=page, page_size=page_size, onboarding=onboarding, online_only=online_only
    )
    return AdminUsersResponse(**data)


@router.get("/users/{user_id}")
async def admin_user_detail(db: DbSession, user_id: int, _admin: AdminUser):
    detail = await admin_service.get_user_detail(db, user_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="User not found")
    u = detail["user"]
    return {
        "user": {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "username": u.username,
            "display_name": u.display_name,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "age": u.age,
            "onboarding_completed": u.onboarding_completed,
            "personal_dhikr_count": u.personal_dhikr_count,
            "personal_active_seconds": u.personal_active_seconds,
            "created_at": u.created_at,
            "last_dhikr_at": u.last_dhikr_at,
        },
        "visits": [
            {
                "id": v.id,
                "started_at": v.started_at,
                "last_seen_at": v.last_seen_at,
                "ended_at": v.ended_at,
                "last_route": v.last_route,
                "first_dhikr_at": v.first_dhikr_at,
            }
            for v in detail["visits"]
        ],
        "sessions": [
            {
                "id": s.id,
                "mode": s.mode,
                "dhikr_count": s.dhikr_count,
                "active_seconds": s.active_seconds,
                "started_at": s.started_at,
                "ended_at": s.ended_at,
                "is_active": s.is_active,
            }
            for s in detail["sessions"]
        ],
        "daily": [
            {"local_date": d.local_date, "dhikr": d.dhikr, "active_seconds": d.active_seconds}
            for d in detail["daily"]
        ],
    }


@router.get("/daily", response_model=list[AdminDailyPoint])
async def admin_daily(
    db: DbSession,
    _admin: AdminUser,
    days: int = Query(30, ge=7, le=90),
) -> list[AdminDailyPoint]:
    return await admin_service.daily_series(db, days)


@router.get("/funnel", response_model=AdminFunnelResponse)
async def admin_funnel(
    db: DbSession,
    _admin: AdminUser,
    days: int = Query(7, ge=1, le=30),
) -> AdminFunnelResponse:
    data = await admin_service.funnel_stats(db, days)
    return AdminFunnelResponse(**data)
