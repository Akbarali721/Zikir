from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from app.api.deps import CurrentUser, DbSession, parse_visit_header
from app.schemas.tasbeh import (
    SessionStartRequest,
    SessionStartResponse,
    SessionStopResponse,
    TasbehSyncRequest,
    TasbehSyncResponse,
)
from app.services.visit_service import get_visit_for_user
from app.services import tasbeh_service

router = APIRouter(prefix="/api", tags=["tasbeh"])


@router.post("/session/start", response_model=SessionStartResponse)
async def session_start(
    body: SessionStartRequest,
    db: DbSession,
    user: CurrentUser,
) -> SessionStartResponse:
    try:
        tasbeh = await tasbeh_service.start_session(db, user, body.mode)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to start session") from exc

    return SessionStartResponse(
        session_id=tasbeh.id,
        mode=tasbeh.mode,
        started_at=tasbeh.started_at,
    )


@router.post("/session/stop", response_model=SessionStopResponse)
async def session_stop(db: DbSession, user: CurrentUser) -> SessionStopResponse:
    try:
        tasbeh = await tasbeh_service.stop_session(db, user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to stop session") from exc

    return SessionStopResponse(
        session_id=tasbeh.id,
        ended_at=tasbeh.ended_at,
        dhikr_count=tasbeh.dhikr_count,
        active_seconds=tasbeh.active_seconds,
    )


@router.post("/tasbeh/sync", response_model=TasbehSyncResponse)
async def tasbeh_sync(
    body: TasbehSyncRequest,
    db: DbSession,
    user: CurrentUser,
    x_visit_id: Annotated[str | None, Header(alias="X-Visit-Id")] = None,
) -> TasbehSyncResponse:
    visit = await get_visit_for_user(db, user.id, parse_visit_header(x_visit_id))
    try:
        tasbeh, user, payload = await tasbeh_service.sync_tasbeh(
            db,
            user,
            body.session_id,
            body.dhikr_delta,
            body.active_seconds_delta,
            batch_id=body.batch_id,
            visit=visit,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Sync failed") from exc

    if payload:
        return TasbehSyncResponse(**payload)
    return TasbehSyncResponse(
        session_id=tasbeh.id,
        session_dhikr_count=tasbeh.dhikr_count,
        session_active_seconds=tasbeh.active_seconds,
        personal_dhikr_count=user.personal_dhikr_count,
        personal_active_seconds=user.personal_active_seconds,
    )
