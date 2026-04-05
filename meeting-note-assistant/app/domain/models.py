from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4


@dataclass(slots=True)
class ActionItem:
    description: str
    owner: str
    due_date: date | None = None
    is_done: bool = False


@dataclass(slots=True)
class Meeting:
    title: str
    date: date
    owner: str
    participants: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(slots=True)
class MeetingReport:
    total_meetings: int
    total_participants: int
    total_action_items: int
    completed_action_items: int
