import json
from datetime import date
from pathlib import Path

from app.domain.models import ActionItem, Meeting
from app.storage.base import MeetingRepository


class JsonMeetingRepository(MeetingRepository):
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def add(self, meeting: Meeting) -> Meeting:
        meetings = self.list()
        meetings.append(meeting)
        self._save(meetings)
        return meeting

    def list(self) -> list[Meeting]:
        payload = self._load_payload()
        return [self._deserialize_meeting(item) for item in payload]

    def get(self, meeting_id: str) -> Meeting | None:
        for meeting in self.list():
            if meeting.id == meeting_id:
                return meeting
        return None

    def update(self, meeting: Meeting) -> Meeting | None:
        meetings = self.list()
        updated = False

        for index, existing_meeting in enumerate(meetings):
            if existing_meeting.id == meeting.id:
                meetings[index] = meeting
                updated = True
                break

        if not updated:
            return None

        self._save(meetings)
        return meeting

    def delete(self, meeting_id: str) -> Meeting | None:
        meetings = self.list()
        remaining_meetings: list[Meeting] = []
        deleted_meeting: Meeting | None = None

        for meeting in meetings:
            if meeting.id == meeting_id and deleted_meeting is None:
                deleted_meeting = meeting
                continue
            remaining_meetings.append(meeting)

        if deleted_meeting is not None:
            self._save(remaining_meetings)

        return deleted_meeting

    def _load_payload(self) -> list[dict]:
        if not self._file_path.exists():
            return []

        raw_data = self._file_path.read_text(encoding="utf-8").strip()
        if not raw_data:
            return []

        return json.loads(raw_data)

    def _save(self, meetings: list[Meeting]) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [self._serialize_meeting(meeting) for meeting in meetings]
        self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _serialize_meeting(self, meeting: Meeting) -> dict:
        return {
            "id": meeting.id,
            "title": meeting.title,
            "date": meeting.date.isoformat(),
            "owner": meeting.owner,
            "participants": meeting.participants,
            "action_items": [
                {
                    "description": item.description,
                    "owner": item.owner,
                    "due_date": item.due_date.isoformat() if item.due_date else None,
                    "is_done": item.is_done,
                }
                for item in meeting.action_items
            ],
        }

    def _deserialize_meeting(self, payload: dict) -> Meeting:
        action_items = [
            ActionItem(
                description=item["description"],
                owner=item["owner"],
                due_date=date.fromisoformat(item["due_date"]) if item.get("due_date") else None,
                is_done=item.get("is_done", False),
            )
            for item in payload.get("action_items", [])
        ]
        return Meeting(
            id=payload["id"],
            title=payload["title"],
            date=date.fromisoformat(payload["date"]),
            owner=payload["owner"],
            participants=payload.get("participants", []),
            action_items=action_items,
        )
