from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from app.api.deps import CurrentUser, DbSession, parse_visit_header
from app.schemas.visit import VisitHeartbeatRequest, VisitHeartbeatResponse
from app.services.retention_service import record_visit_snapshot
from app.services.visit_service import heartbeat

router = APIRouter(prefix="/api/visit", tags=["retention"])


@router.post("/heartbeat", response_model=VisitHeartbeatResponse)
async def visit_heartbeat(
    body: VisitHeartbeatRequest,
    db: DbSession,
    user: CurrentUser,
    x_visit_id: Annotated[str | None, Header(alias="X-Visit-Id")] = None,
) -> VisitHeartbeatResponse:
    visit = await heartbeat(
        db,
        user,
        visit_id=parse_visit_header(x_visit_id),
        route=body.route,
    )
    return VisitHeartbeatResponse(
        visit_id=visit.id,
        started_at=visit.started_at,
        last_seen_at=visit.last_seen_at,
    )


@router.post("/snapshot")
async def visit_snapshot(db: DbSession, user: CurrentUser) -> dict[str, str]:
    try:
        await record_visit_snapshot(db, user)
        await db.flush()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to record visit snapshot") from exc
    return {"status": "ok"}