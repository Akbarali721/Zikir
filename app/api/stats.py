from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.schemas.progress import ProgressResponse
from app.schemas.user import (
    RetentionInfo,
    SessionBrief,
    TelegramUserData,
    TodayContribution,
    UserMeResponse,
)
from app.services import tasbeh_service
from app.services.progress_service import build_progress_response, ensure_global_progress
from app.api.admin_deps import is_user_admin
from app.services.retention_service import (
    compute_global_growth_since_last_visit,
    get_current_global_dhikr,
    get_today_totals,
    session_started_on_display_today,
)

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/config/client")
async def client_config() -> dict[str, bool]:
    """Frontend uchun: mahalliy DEV auth faqat DEBUG+DEV_TELEGRAM_ID bo‘lganda."""
    settings = get_settings()
    return {
        "allow_dev_auth": bool(settings.debug and settings.dev_telegram_id is not None),
    }


@router.get("/me", response_model=UserMeResponse)
async def get_me(db: DbSession, user: CurrentUser) -> UserMeResponse:
    settings = get_settings()
    session = await tasbeh_service.get_active_session(db, user.id)
    session_brief = None
    if session:
        challenge_type = getattr(session, "challenge_type", "million_istighfor")
        counts_today = (
            challenge_type == "million_istighfor"
            and session_started_on_display_today(session.started_at, settings.display_timezone)
        )
        session_brief = SessionBrief(
            id=session.id,
            mode=session.mode,
            challenge_type=challenge_type,
            dhikr_count=session.dhikr_count,
            active_seconds=session.active_seconds,
            is_active=session.is_active,
            started_at=session.started_at,
            counts_for_today=counts_today,
        )

    today_dhikr, today_seconds = await get_today_totals(db, user.id)
    current_global = await get_current_global_dhikr(db)
    growth = compute_global_growth_since_last_visit(user, current_global)

    return UserMeResponse(
        user=TelegramUserData(
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        ),
        personal_dhikr_count=user.personal_dhikr_count,
        personal_active_seconds=user.personal_active_seconds,
        display_name=user.display_name,
        age=user.age,
        onboarding_completed=user.onboarding_completed,
        is_admin=is_user_admin(user),
        leaderboard_opt_in=bool(getattr(user, "leaderboard_opt_in", False)),
        today=TodayContribution(dhikr=today_dhikr, active_seconds=today_seconds),
        retention=RetentionInfo(
            is_returning=user.last_visit_at is not None,
            global_growth_since_last_visit=growth,
            display_timezone=settings.display_timezone,
        ),
        session=session_brief,
    )


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(db: DbSession, user: CurrentUser) -> ProgressResponse:
    try:
        global_row = await ensure_global_progress(db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to load global progress") from exc

    return build_progress_response(
        user.personal_dhikr_count,
        user.personal_active_seconds,
        global_row,
    )
