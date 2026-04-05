from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /meetings
# ---------------------------------------------------------------------------

def test_create_meeting_ok(client: TestClient) -> None:
    payload = {"title": "Retro", "date": "2026-04-10", "owner": "Jorge"}
    r = client.post("/meetings", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Retro"
    assert body["owner"] == "Jorge"
    assert "id" in body


def test_create_meeting_missing_title(client: TestClient) -> None:
    r = client.post("/meetings", json={"date": "2026-04-10", "owner": "Jorge"})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_create_meeting_missing_date(client: TestClient) -> None:
    r = client.post("/meetings", json={"title": "Retro", "owner": "Jorge"})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_create_meeting_empty_owner(client: TestClient) -> None:
    r = client.post("/meetings", json={"title": "Retro", "date": "2026-04-10", "owner": " "})
    assert r.status_code == 400
    assert "detail" in r.json()


# ---------------------------------------------------------------------------
# GET /meetings
# ---------------------------------------------------------------------------

def test_list_meetings_empty(client: TestClient) -> None:
    r = client.get("/meetings")
    assert r.status_code == 200
    assert r.json() == {"total": 0, "items": []}


def test_list_meetings_paginated(client: TestClient, sample_meeting: dict) -> None:
    r = client.get("/meetings")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_list_meetings_filter_owner(client: TestClient, sample_meeting: dict) -> None:
    client.post("/meetings", json={"title": "Other", "date": "2026-04-05", "owner": "Ana"})
    r = client.get("/meetings?owner=Jorge")
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["owner"] == "Jorge"


def test_list_meetings_filter_from_date(client: TestClient) -> None:
    client.post("/meetings", json={"title": "Old", "date": "2025-01-01", "owner": "Jorge"})
    client.post("/meetings", json={"title": "New", "date": "2026-04-01", "owner": "Jorge"})
    r = client.get("/meetings?from_date=2026-01-01")
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "New"


def test_list_meetings_pagination_limit_offset(client: TestClient) -> None:
    for i in range(5):
        client.post("/meetings", json={"title": f"M{i}", "date": f"2026-04-0{i+1}", "owner": "Jorge"})
    r = client.get("/meetings?limit=2&offset=2")
    body = r.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2


# ---------------------------------------------------------------------------
# GET /meetings/{id}
# ---------------------------------------------------------------------------

def test_get_meeting_ok(client: TestClient, sample_meeting: dict) -> None:
    r = client.get(f"/meetings/{sample_meeting['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == sample_meeting["title"]


def test_get_meeting_not_found(client: TestClient) -> None:
    r = client.get("/meetings/nonexistent-id")
    assert r.status_code == 404
    assert "detail" in r.json()


# ---------------------------------------------------------------------------
# POST /meetings/{id}/action-items
# ---------------------------------------------------------------------------

def test_add_action_item_ok(client: TestClient, sample_meeting: dict) -> None:
    payload = {"description": "Write docs", "owner": "Ana", "due_date": "2026-04-15"}
    r = client.post(f"/meetings/{sample_meeting['id']}/action-items", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["description"] == "Write docs"
    assert body["owner"] == "Ana"
    assert body["is_done"] is False


def test_add_action_item_meeting_not_found(client: TestClient) -> None:
    payload = {"description": "Write docs", "owner": "Ana"}
    r = client.post("/meetings/nonexistent-id/action-items", json=payload)
    assert r.status_code == 404
    assert "detail" in r.json()


def test_add_action_item_missing_owner(client: TestClient, sample_meeting: dict) -> None:
    r = client.post(
        f"/meetings/{sample_meeting['id']}/action-items",
        json={"description": "Write docs"},
    )
    assert r.status_code == 422
    assert "detail" in r.json()


# ---------------------------------------------------------------------------
# GET /meetings/{id}/action-items
# ---------------------------------------------------------------------------

def test_list_action_items_ok(client: TestClient, sample_meeting: dict) -> None:
    client.post(
        f"/meetings/{sample_meeting['id']}/action-items",
        json={"description": "Task A", "owner": "Ana"},
    )
    client.post(
        f"/meetings/{sample_meeting['id']}/action-items",
        json={"description": "Task B", "owner": "Rui"},
    )
    r = client.get(f"/meetings/{sample_meeting['id']}/action-items")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_list_action_items_filter_owner(client: TestClient, sample_meeting: dict) -> None:
    client.post(
        f"/meetings/{sample_meeting['id']}/action-items",
        json={"description": "Task A", "owner": "Ana"},
    )
    client.post(
        f"/meetings/{sample_meeting['id']}/action-items",
        json={"description": "Task B", "owner": "Rui"},
    )
    r = client.get(f"/meetings/{sample_meeting['id']}/action-items?owner=Ana")
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["owner"] == "Ana"


# ---------------------------------------------------------------------------
# GET /dashboard/summary
# ---------------------------------------------------------------------------

def test_dashboard_summary(client: TestClient, sample_meeting: dict) -> None:
    client.post(
        f"/meetings/{sample_meeting['id']}/action-items",
        json={"description": "Task", "owner": "Ana", "is_done": False},
    )
    r = client.get("/dashboard/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_meetings"] == 1
    assert body["total_action_items"] == 1
    assert body["completed_action_items"] == 0
    assert "total_participants" in body
