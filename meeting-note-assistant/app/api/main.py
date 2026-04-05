from datetime import date

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas import (
    ActionItemListResponse,
    ActionItemPayload,
    ActionItemResponse,
    DashboardResponse,
    HealthResponse,
    MeetingCreatePayload,
    MeetingListResponse,
    MeetingResponse,
    MeetingUpdatePayload,
)
from app.core import NotFoundError, ValidationError, get_meeting_service
from app.domain import ActionItem, Meeting
from app.services.meeting_service import MeetingService


app = FastAPI(
    title="Meeting Note Assistant API",
    version="0.2.0",
    description="Manage meetings, participants, and action items. Built for Backend I.",
)


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def validation_exception_handler(_: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [f"{' -> '.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "; ".join(errors)})


def _to_meeting_response(meeting: Meeting) -> MeetingResponse:
    return MeetingResponse.model_validate(meeting, from_attributes=True)


def _to_action_items(payload: MeetingCreatePayload | MeetingUpdatePayload) -> list[ActionItem]:
    return [
        ActionItem(
            description=item.description,
            owner=item.owner,
            due_date=item.due_date,
            is_done=item.is_done,
        )
        for item in payload.action_items
    ]


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/meetings", response_model=MeetingListResponse)
async def list_meetings(
    owner: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingListResponse:
    meetings = service.list_meetings(owner=owner, from_date=from_date, to_date=to_date)
    total = len(meetings)
    page = meetings[offset : offset + limit]
    return MeetingListResponse(total=total, items=[_to_meeting_response(m) for m in page])


@app.post("/meetings", response_model=MeetingResponse, status_code=201)
async def create_meeting(
    payload: MeetingCreatePayload,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingResponse:
    meeting = service.create_meeting(
        title=payload.title,
        meeting_date=payload.date,
        owner=payload.owner,
        participants=payload.participants,
        action_items=_to_action_items(payload),
    )
    return _to_meeting_response(meeting)


@app.get("/meetings/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingResponse:
    meeting = service.get_meeting(meeting_id)
    return _to_meeting_response(meeting)


@app.post("/meetings/{meeting_id}/action-items", response_model=ActionItemResponse, status_code=201)
async def add_action_item(
    meeting_id: str,
    payload: ActionItemPayload,
    service: MeetingService = Depends(get_meeting_service),
) -> ActionItemResponse:
    action_item = ActionItem(
        description=payload.description,
        owner=payload.owner,
        due_date=payload.due_date,
        is_done=payload.is_done,
    )
    item = service.add_action_item(meeting_id, action_item)
    return ActionItemResponse.model_validate(item, from_attributes=True)


@app.get("/meetings/{meeting_id}/action-items", response_model=ActionItemListResponse)
async def list_action_items(
    meeting_id: str,
    owner: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: MeetingService = Depends(get_meeting_service),
) -> ActionItemListResponse:
    items = service.list_action_items(meeting_id, owner=owner)
    total = len(items)
    page = items[offset : offset + limit]
    return ActionItemListResponse(
        total=total,
        items=[ActionItemResponse.model_validate(i, from_attributes=True) for i in page],
    )


@app.put("/meetings/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    payload: MeetingUpdatePayload,
    service: MeetingService = Depends(get_meeting_service),
) -> MeetingResponse:
    meeting = service.update_meeting(
        meeting_id=meeting_id,
        title=payload.title,
        meeting_date=payload.date,
        owner=payload.owner,
        participants=payload.participants,
        action_items=_to_action_items(payload),
    )
    return _to_meeting_response(meeting)


@app.get("/dashboard/summary", response_model=DashboardResponse)
async def dashboard_summary(
    service: MeetingService = Depends(get_meeting_service),
) -> DashboardResponse:
    report = service.build_report()
    return DashboardResponse.model_validate(report, from_attributes=True)
