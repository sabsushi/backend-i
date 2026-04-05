from pathlib import Path

from app.services.meeting_service import MeetingService
from app.storage.json_repository import JsonMeetingRepository


_repository = JsonMeetingRepository(
    Path(__file__).resolve().parent.parent.parent / "data" / "meetings.json"
)
_meeting_service = MeetingService(_repository)


def get_meeting_service() -> MeetingService:
    return _meeting_service
