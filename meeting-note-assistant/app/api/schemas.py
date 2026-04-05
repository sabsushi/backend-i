from datetime import date

from pydantic import BaseModel, Field


class ActionItemPayload(BaseModel):
    description: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    due_date: date | None = None
    is_done: bool = False


class MeetingCreatePayload(BaseModel):
    title: str = Field(..., min_length=1)
    date: date
    owner: str = Field(..., min_length=1)
    participants: list[str] = Field(default_factory=list)
    action_items: list[ActionItemPayload] = Field(default_factory=list)


class MeetingUpdatePayload(MeetingCreatePayload):
    pass


class ActionItemResponse(BaseModel):
    description: str
    owner: str
    due_date: date | None = None
    is_done: bool


class MeetingResponse(BaseModel):
    id: str
    title: str
    date: date
    owner: str
    participants: list[str]
    action_items: list[ActionItemResponse]


class HealthResponse(BaseModel):
    status: str


class MeetingListResponse(BaseModel):
    total: int
    items: list[MeetingResponse]


class ActionItemListResponse(BaseModel):
    total: int
    items: list[ActionItemResponse]


class DashboardResponse(BaseModel):
    total_meetings: int
    total_participants: int
    total_action_items: int
    completed_action_items: int
