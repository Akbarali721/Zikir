from pydantic import BaseModel, Field


class PersonalProgress(BaseModel):
    dhikr: int
    active_seconds: int


class GlobalProgressStats(BaseModel):
    dhikr: int
    dhikr_goal: int
    dhikr_percent: float
    remaining_dhikr: int
    active_seconds: int
    seconds_goal: int
    time_percent: float
    remaining_seconds: int


class ProgressResponse(BaseModel):
    personal: PersonalProgress
    global_: GlobalProgressStats = Field(serialization_alias="global")

    model_config = {"populate_by_name": True}
