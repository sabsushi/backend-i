from app.domain.models import Meeting
from app.storage.base import MeetingRepository


class InMemoryMeetingRepository(MeetingRepository):
    def __init__(self) -> None:
        self._meetings: dict[str, Meeting] = {}

    def add(self, meeting: Meeting) -> Meeting:
        self._meetings[meeting.id] = meeting
        return meeting

    def list(self) -> list[Meeting]:
        return list(self._meetings.values())

    def get(self, meeting_id: str) -> Meeting | None:
        return self._meetings.get(meeting_id)

    def update(self, meeting: Meeting) -> Meeting | None:
        if meeting.id not in self._meetings:
            return None
        self._meetings[meeting.id] = meeting
        return meeting

    def delete(self, meeting_id: str) -> Meeting | None:
        return self._meetings.pop(meeting_id, None)
