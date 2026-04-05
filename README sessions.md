# Backend I — Meeting Note Assistant

Full-stack backend project built across 21 sessions covering CLI, REST API, relational databases, and AI integration.

---

## Dev Container

This project runs inside a **VS Code Dev Container**. Open the `Backend_I/` folder in VS Code and accept the **"Reopen in Container"** prompt.

### Container configuration (`.devcontainer/devcontainer.json`)

| Setting | Value |
|---|---|
| Base image | `mcr.microsoft.com/devcontainers/python:2-3.14-trixie` (Python 3.14, Debian Trixie) |
| Extra feature | `astral.sh-uv` — installs `uv`, a fast Python package and project manager |

`uv` is used in both subprojects to create virtual environments and install dependencies instead of `pip`.

---

## Repository Layout

```
Backend_I/
├── .devcontainer/
│   └── devcontainer.json
├── backend-i/                  # Course material and session notes (reference only)
├── meeting-note-assistant/     # Main project: CLI + FastAPI (Sessions 1–14, 18–21)
├── backend_i_django/           # Django project (Sessions 15–17)
└── guidelines.md               # Execution plan and session log
```

---

## Project 1 — Meeting Note Assistant (CLI + FastAPI)

### Stack and dependencies

| Library | Version | Purpose |
|---|---|---|
| `typer` | 0.24 | CLI framework |
| `fastapi` | 0.135 | REST API framework |
| `uvicorn` | 0.42 | ASGI server |
| `pydantic` | 2.12 | Request/response validation and schemas |
| `httpx` | 0.28 | HTTP client (used by pytest test client) |
| `pytest` | 9.0 | Test runner |

### Setup

All commands run inside the dev container terminal.

```bash
cd meeting-note-assistant
uv venv
uv pip install fastapi uvicorn typer pytest httpx
```

### Running the CLI

```bash
# Create a meeting
python app/cli.py create-meeting --title "Sprint Planning" --date "2026-04-04" --owner "Jorge"

# Create with participants and action items
python app/cli.py create-meeting \
  --title "Retro" --date "2026-04-04" --owner "Jorge" \
  --participant "Ana" --participant "Rui" \
  --action-item "Write docs" --action-owner "Ana" --action-due-date "2026-04-10"

# List all meetings
python app/cli.py list-meetings

# Show a specific meeting
python app/cli.py show-meeting --id "<meeting-id>"

# Delete a meeting
python app/cli.py delete-meeting --id "<meeting-id>"

# Summary report
python app/cli.py report-summary
```

Meetings are persisted to `data/meetings.json` and survive restarts.

### Running the API

```bash
cd meeting-note-assistant
uvicorn app.api.main:app --reload
```

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/docs` | Interactive API docs (Swagger UI) |
| `http://127.0.0.1:8000/redoc` | Alternative docs (ReDoc) |
| `http://127.0.0.1:8000/openapi.json` | Raw OpenAPI schema |

### API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/meetings` | List meetings (supports `owner`, `from_date`, `to_date`, `limit`, `offset`) |
| POST | `/meetings` | Create a meeting |
| GET | `/meetings/{id}` | Get a meeting |
| PUT | `/meetings/{id}` | Update a meeting |
| POST | `/meetings/{id}/action-items` | Add an action item to a meeting |
| GET | `/meetings/{id}/action-items` | List action items (supports `owner`, `limit`, `offset`) |
| GET | `/dashboard/summary` | Aggregate counts for meetings and action items |

### Running the tests

```bash
cd meeting-note-assistant
pytest -v
```

Tests use an in-memory repository via FastAPI dependency override — no file I/O, fully isolated.

---

## Project 2 — Django Admin (backend_i_django)

### Stack and dependencies

| Library | Version | Purpose |
|---|---|---|
| `django` | 6.0.3 | Web framework + ORM + admin |
| `asgiref` | 3.11 | Django async support |
| `sqlparse` | 0.5 | SQL formatting (Django dependency) |

Database: **SQLite** (`db.sqlite3`), managed by Django migrations.

### Setup

```bash
cd backend_i_django
uv venv
uv pip install django
python manage.py migrate
python manage.py setup_groups
```

To create a superuser:

```bash
DJANGO_SUPERUSER_PASSWORD=admin123 python manage.py createsuperuser \
  --username admin --email admin@example.com --noinput
```

### Running the admin

```bash
cd backend_i_django
python manage.py runserver
```

Open `http://127.0.0.1:8000/admin/` and log in with the superuser credentials.

### Models

**Meeting** — `title`, `date`, `owner`

**ActionItem** — `meeting` (FK), `description`, `owner`, `due_date`, `status` (`open` / `done`)

### Groups and permissions

Run once after migrate to create the three access groups:

```bash
python manage.py setup_groups
```

| Group | Permissions |
|---|---|
| `admin` | Full access to Meeting and ActionItem |
| `editor` | Add, change, view — no delete |
| `viewer` | View only |

Assign users to groups in the Django admin under **Authentication → Groups**.

### Admin features

- `MeetingAdmin`: searchable by title and owner, filterable by date and owner
- `ActionItemAdmin`: searchable by description and owner, filterable by status and due date
- Custom action: **"Mark selected action items as done"** — bulk-updates status to `done`

---

## Requirements Checklist

### Phase 1 — CLI Foundation
- [x] `create-meeting --title --date --owner`
- [x] `list-meetings`
- [x] `show-meeting --id`
- [x] Domain models: `Meeting` and `ActionItem` dataclasses
- [x] Service layer separates business logic from CLI handlers

### Phase 2 — Persistence and Validation
- [x] JSON persistence — meetings survive restarts
- [x] Participants and action items persisted
- [x] `ValidationError` and `NotFoundError` custom exceptions
- [x] ISO date validation (`YYYY-MM-DD`)
- [x] Exit code `2` for validation errors, `1` for not found

### Phase 3 — Logging and CLI Checkpoint
- [x] Structured logging on create, list, delete, and error flows
- [x] `delete-meeting --id`
- [x] `report-summary` with totals for meetings, participants, action items

### Phase 4 — FastAPI Base
- [x] `GET /health`
- [x] `GET /meetings`
- [x] `POST /meetings` (201)
- [x] `GET /meetings/{id}`
- [x] `PUT /meetings/{id}`
- [x] 404 responses for missing meetings
- [x] Pydantic schemas for all request and response bodies
- [x] Service layer reused — no duplicated business logic in routers

### Phase 5 — API Expansion
- [x] `POST /meetings/{id}/action-items` (201)
- [x] `GET /meetings/{id}/action-items`
- [x] Owner filter on meetings and action items
- [x] Date range filter (`from_date`, `to_date`) on meetings
- [x] Sorting by date (ascending)
- [x] Pagination with `limit` and `offset`
- [x] Stable response shape `{ "total": N, "items": [...] }`

### Phase 6 — API Testing and Checkpoint
- [x] `pytest` + `httpx` installed
- [x] `tests/conftest.py` with isolated `client` fixture (in-memory repo, no file I/O)
- [x] `sample_meeting` fixture for downstream tests
- [x] 18 tests covering health, CRUD, filters, pagination, action items, and dashboard
- [x] All 18 tests pass
- [x] Consistent error shape `{"detail": "..."}` across 400, 404, and 422
- [x] API metadata: title, version `0.2.0`, description
- [x] `GET /dashboard/summary` (challenge)

### Phase 7 — Django Project
- [x] Separate Django project in `backend_i_django/`
- [x] `Meeting` model: title, date, owner
- [x] `ActionItem` model with `ForeignKey` to Meeting (CASCADE)
- [x] `makemigrations` and `migrate` applied cleanly
- [x] Both models registered in Django admin
- [x] `list_display`, `list_filter`, `search_fields` on both admin classes
- [x] Superuser created
- [x] `admin`, `editor`, `viewer` groups with correct permissions
- [x] `viewer` cannot edit or delete
- [x] `editor` cannot delete
- [x] `setup_groups` management command (reproducible, version-controlled)
- [x] Custom admin action: mark action items as done (challenge)

### Phase 8 — AI Features
- [ ] Meeting summarizer
- [ ] Action item extractor
- [ ] Output validation
- [ ] Retries and fallback

### Phase 9 — Final Demo and Defense
- [ ] `DEMO_CHECKLIST.md`
- [ ] End-to-end demo script
- [ ] Technical justifications
