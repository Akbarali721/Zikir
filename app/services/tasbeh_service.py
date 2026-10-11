import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.progress import GlobalProgress
from app.models.sync_batch import TasbehSyncBatch
from app.models.tasbeh_session import TasbehSession
from app.models.user import User
from app.models.visit import UserVisit
from app.services.daily_service import apply_daily_contribution
from app.services.progress_service import ensure_global_progress
from app.services.visit_service import mark_first_dhikr


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def get_active_session(session: AsyncSession, user_id: int, *, for_update: bool = False) -> TasbehSession | None:
    stmt = (
        select(TasbehSession)
        .where(TasbehSession.user_id == user_id, TasbehSession.is_active.is_(True))
        .order_by(TasbehSession.id.desc())
        .limit(1)
    )
    if for_update:
        stmt = stmt.with_for_update()
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _validate_sync_deltas(dhikr_delta: int, active_seconds_delta: int) -> None:
    settings = get_settings()
    if dhikr_delta > settings.max_dhikr_delta_per_sync:
        raise HTTPException(
            status_code=400,
            detail=f"dhikr_delta exceeds limit ({settings.max_dhikr_delta_per_sync})",
        )
    if active_seconds_delta > settings.max_active_seconds_delta_per_sync:
        raise HTTPException(
            status_code=400,
            detail=f"active_seconds_delta exceeds limit ({settings.max_active_seconds_delta_per_sync})",
        )
    if dhikr_delta == 0 and active_seconds_delta == 0:
        raise HTTPException(status_code=400, detail="Empty sync payload")


def _build_sync_response(tasbeh: TasbehSession, user: User) -> dict:
    return {
        "session_id": tasbeh.id,
        "session_dhikr_count": tasbeh.dhikr_count,
        "session_active_seconds": tasbeh.active_seconds,
        "personal_dhikr_count": user.personal_dhikr_count,
        "personal_active_seconds": user.personal_active_seconds,
    }


async def start_session(session: AsyncSession, user: User, mode: str) -> TasbehSession:
    now = _utcnow()
    existing = await get_active_session(session, user.id, for_update=True)
    if existing is not None:
        if existing.mode == mode:
            existing.last_activity_at = now
            user.last_active_at = now
            await session.flush()
            return existing
        await session.execute(
            update(TasbehSession)
            .where(TasbehSession.id == existing.id)
            .values(is_active=False, ended_at=now)
        )

    tasbeh = TasbehSession(
        user_id=user.id,
        mode=mode,
        is_active=True,
        started_at=now,
        last_activity_at=now,
    )
    session.add(tasbeh)
    user.last_active_at = now
    try:
        await session.flush()
    except IntegrityError as exc:
        active = await get_active_session(session, user.id)
        if active:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "active_session_exists",
                    "session_id": active.id,
                    "mode": active.mode,
                },
            ) from exc
        raise HTTPException(status_code=500, detail="Failed to start session") from exc
    return tasbeh


async def stop_session(session: AsyncSession, user: User) -> TasbehSession:
    tasbeh = await get_active_session(session, user.id, for_update=True)
    if tasbeh is None:
        raise HTTPException(status_code=404, detail="No active session")

    now = _utcnow()
    tasbeh.is_active = False
    tasbeh.ended_at = now
    await session.flush()
    return tasbeh


async def sync_tasbeh(
    session: AsyncSession,
    user: User,
    session_id: int,
    dhikr_delta: int,
    active_seconds_delta: int,
    *,
    batch_id: uuid.UUID | None = None,
    visit: UserVisit | None = None,
) -> tuple[TasbehSession, User, dict | None]:
    _validate_sync_deltas(dhikr_delta, active_seconds_delta)

    if batch_id is not None:
        existing = await session.get(TasbehSyncBatch, batch_id)
        if existing is not None:
            if (
                existing.user_id != user.id
                or existing.session_id != session_id
                or existing.dhikr_delta != dhikr_delta
                or existing.active_seconds_delta != active_seconds_delta
            ):
                raise HTTPException(status_code=409, detail="batch_id payload mismatch")
            tasbeh = await session.get(TasbehSession, session_id)
            refreshed_user = await session.get(User, user.id)
            if tasbeh is None or refreshed_user is None:
                raise HTTPException(status_code=404, detail="Session not found")
            return tasbeh, refreshed_user, _build_sync_response(tasbeh, refreshed_user)

    result = await session.execute(
        select(TasbehSession).where(TasbehSession.id == session_id).with_for_update()
    )
    tasbeh = result.scalar_one_or_none()
    if tasbeh is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if tasbeh.user_id != user.id:
        raise HTTPException(status_code=403, detail="Session does not belong to current user")
    if not tasbeh.is_active:
        raise HTTPException(status_code=409, detail="Session already stopped")

    now = _utcnow()
    elapsed_session = max(0, int((now - tasbeh.started_at).total_seconds()))
    max_allowed_active = elapsed_session + 30
    if active_seconds_delta > max_allowed_active:
        raise HTTPException(
            status_code=400,
            detail="active_seconds_delta exceeds plausible session elapsed time",
        )

    global_row = await ensure_global_progress(session)

    if batch_id is not None:
        session.add(
            TasbehSyncBatch(
                batch_id=batch_id,
                user_id=user.id,
                session_id=session_id,
                dhikr_delta=dhikr_delta,
                active_seconds_delta=active_seconds_delta,
            )
        )
        try:
            await session.flush()
        except IntegrityError:
            existing = await session.get(TasbehSyncBatch, batch_id)
            if existing and (
                existing.user_id == user.id
                and existing.session_id == session_id
                and existing.dhikr_delta == dhikr_delta
                and existing.active_seconds_delta == active_seconds_delta
            ):
                tasbeh = await session.get(TasbehSession, session_id)
                refreshed_user = await session.get(User, user.id)
                if tasbeh and refreshed_user:
                    return tasbeh, refreshed_user, _build_sync_response(tasbeh, refreshed_user)
            raise HTTPException(status_code=409, detail="batch_id payload mismatch")

    await session.execute(
        update(TasbehSession)
        .where(TasbehSession.id == session_id)
        .values(
            dhikr_count=TasbehSession.dhikr_count + dhikr_delta,
            active_seconds=TasbehSession.active_seconds + active_seconds_delta,
            last_activity_at=now,
        )
    )

    await session.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            personal_dhikr_count=User.personal_dhikr_count + dhikr_delta,
            personal_active_seconds=User.personal_active_seconds + active_seconds_delta,
            last_active_at=now,
        )
    )

    await session.execute(
        update(GlobalProgress)
        .where(GlobalProgress.id == global_row.id)
        .values(
            total_dhikr_count=GlobalProgress.total_dhikr_count + dhikr_delta,
            total_active_seconds=GlobalProgress.total_active_seconds + active_seconds_delta,
        )
    )

    await apply_daily_contribution(
        session, user.id, dhikr_delta, active_seconds_delta, at=now
    )

    if dhikr_delta > 0:
        await mark_first_dhikr(session, user, visit)

    await session.flush()

    result = await session.execute(select(TasbehSession).where(TasbehSession.id == session_id))
    tasbeh = result.scalar_one()
    result = await session.execute(select(User).where(User.id == user.id))
    user = result.scalar_one()
    return tasbeh, user, _build_sync_response(tasbeh, user)
