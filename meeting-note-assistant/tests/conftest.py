import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.core.dependencies import get_meeting_service
from app.services.meeting_service import MeetingService
from app.storage.memory import InMemoryMeetingRepository


@pytest.fixture()
def client() -> TestClient:
    service = MeetingService(InMemoryMeetingRepository())
    app.dependency_overrides[get_meeting_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_meeting(client: TestClient) -> dict:
    payload = {
        "title": "Sprint Planning",
        "date": "2026-04-01",
        "owner": "Jorge",
        "participants": ["Ana", "Rui"],
        "action_items": [],
    }
    response = client.post("/meetings", json=payload)
    return response.json()
