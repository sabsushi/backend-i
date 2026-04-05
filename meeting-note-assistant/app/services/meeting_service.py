from datetime import date

from app.core.exceptions import NotFoundError
from app.core.validators import require_text
from app.domain.models import ActionItem, Meeting, MeetingReport
from app.storage.base import MeetingRepository


class MeetingService:
    def __init__(self, repository: MeetingRepository) -> None:
        self._repository = repository

    def create_meeting(
        self,
        title: str,
        meeting_date: date,
        owner: str,
        participants: list[str] | None = None,
        action_items: list[ActionItem] | None = None,
    ) -> Meeting:
        meeting = Meeting(
            title=require_text(title, "Meeting title"),
            date=meeting_date,
            owner=require_text(owner, "Meeting owner"),
            participants=self._validate_participants(participants or []),
            action_items=self._validate_action_items(action_items or []),
        )
        return self._repository.add(meeting)

    def list_meetings(
        self,
        owner: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Meeting]:
        meetings = self._repository.list()
        if owner:
            meetings = [m for m in meetings if m.owner == owner]
        if from_date:
            meetings = [m for m in meetings if m.date >= from_date]
        if to_date:
            meetings = [m for m in meetings if m.date <= to_date]
        return sorted(meetings, key=lambda m: m.date)

    def add_action_item(self, meeting_id: str, action_item: ActionItem) -> ActionItem:
        meeting = self.get_meeting(meeting_id)
        validated = self._validate_action_items([action_item])[0]
        meeting.action_items.append(validated)
        self._repository.update(meeting)
        return validated

    def list_action_items(self, meeting_id: str, owner: str | None = None) -> list[ActionItem]:
        meeting = self.get_meeting(meeting_id)
        items = meeting.action_items
        if owner:
            items = [i for i in items if i.owner == owner]
        return items

    def get_meeting(self, meeting_id: str) -> Meeting:
        meeting = self._repository.get(require_text(meeting_id, "Meeting id"))
        if meeting is None:
            raise NotFoundError(f"Meeting not found: {meeting_id}")
        return meeting

    def update_meeting(
        self,
        meeting_id: str,
        title: str,
        meeting_date: date,
        owner: str,
        participants: list[str] | None = None,
        action_items: list[ActionItem] | None = None,
    ) -> Meeting:
        existing_meeting = self.get_meeting(meeting_id)
        updated_meeting = Meeting(
            id=existing_meeting.id,
            title=require_text(title, "Meeting title"),
            date=meeting_date,
            owner=require_text(owner, "Meeting owner"),
            participants=self._validate_participants(participants or []),
            action_items=self._validate_action_items(action_items or []),
        )
        saved_meeting = self._repository.update(updated_meeting)
        if saved_meeting is None:
            raise NotFoundError(f"Meeting not found: {meeting_id}")
        return saved_meeting

    def delete_meeting(self, meeting_id: str) -> Meeting:
        cleaned_meeting_id = require_text(meeting_id, "Meeting id")
        meeting = self._repository.delete(cleaned_meeting_id)
        if meeting is None:
            raise NotFoundError(f"Meeting not found: {meeting_id}")
        return meeting

    def build_report(self) -> MeetingReport:
        meetings = self._repository.list()
        total_action_items = sum(len(meeting.action_items) for meeting in meetings)
        completed_action_items = sum(
            1
            for meeting in meetings
            for item in meeting.action_items
            if item.is_done
        )
        return MeetingReport(
            total_meetings=len(meetings),
            total_participants=sum(len(meeting.participants) for meeting in meetings),
            total_action_items=total_action_items,
            completed_action_items=completed_action_items,
        )

    def _validate_participants(self, participants: list[str]) -> list[str]:
        return [require_text(participant, "Participant") for participant in participants]

    def _validate_action_items(self, action_items: list[ActionItem]) -> list[ActionItem]:
        validated_items: list[ActionItem] = []
        for item in action_items:
            validated_items.append(
                ActionItem(
                    description=require_text(item.description, "Action item description"),
                    owner=require_text(item.owner, "Action item owner"),
                    due_date=item.due_date,
                    is_done=item.is_done,
                )
            )
        return validated_items
