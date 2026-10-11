from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class VisitHeartbeatRequest(BaseModel):
    route: str | None = None


class VisitHeartbeatResponse(BaseModel):
    visit_id: UUID
    started_at: datetime
    last_seen_at: datetime
