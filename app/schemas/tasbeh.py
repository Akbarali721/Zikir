from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ChallengeType = Literal["million_istighfor", "tasbeh_33"]
InputMode = Literal["tap", "swipe"]


class SessionStartRequest(BaseModel):
    mode: InputMode
    challenge: ChallengeType = "million_istighfor"


class SessionStartResponse(BaseModel):
    session_id: int
    mode: str
    challenge_type: str
    started_at: datetime


class TasbehSyncRequest(BaseModel):
    session_id: int
    dhikr_delta: int = Field(ge=0)
    active_seconds_delta: int = Field(ge=0)
    batch_id: UUID | None = None


class TasbehSyncResponse(BaseModel):
    session_id: int
    session_dhikr_count: int
    session_active_seconds: int
    personal_dhikr_count: int
    personal_active_seconds: int


class SessionStopResponse(BaseModel):
    session_id: int
    ended_at: datetime
    dhikr_count: int
    active_seconds: int
