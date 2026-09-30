# Full-Stack Task Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the Flet frontend → FastAPI backend → PostgreSQL so users can register, log in, and create / list / edit / complete / delete / categorise tasks that persist in the database, with all configuration coming from `.env`.

**Architecture:** The backend `tasks` module is restructured into Lich layers (entity → service → repository port → SQLAlchemy adapter, with thin HTTP routes and pydantic DTOs); users/auth only get bug and security fixes. Alembic owns the schema and runs on backend start. The Flet app runs server-side in its own container and calls the API over the internal Docker network through one `ApiClient` per browser session. JWTs are held only in that session's Python memory, never in the browser.

**Tech Stack:** Python 3.12, FastAPI 0.115, SQLAlchemy 2.0, Alembic 1.15, PyJWT 2.10, pydantic-settings 2.9, PostgreSQL 15, Flet 1.0.3 (web), httpx 0.28, pytest 8.3, Docker Compose.

**Spec:** the §Decisions section below (agreed with the user in-session on 2026-09-30) plus the user's standing rules in `/mnt/c/Users/SepehrMaadani/Documents/rules.md`.

## Decisions (the spec)

1. **Backend architecture:** Lich layers for `tasks` only. `users`/`auth` keep their layout and only get bug and security fixes.
2. **Frontend auth:** Login and Register screens. Tokens are kept only in server-side Python memory for the session, and the access token is refreshed automatically using the refresh token.
3. **Categories:** a nullable `category` column with a fixed allowed list: `university`, `finnish`, `general`. Category cards show real totals and progress.
4. **Schema:** Alembic migrations, with `alembic upgrade head` run when the backend container starts.
5. **Config:** everything environment-specific lives in `.env`. `.env.example` is committed and `.env` never is.
6. **Features that must work end to end:** register, log in, log out, list tasks, filter by category, create, edit (title, description, category), mark complete/incomplete, and delete with confirmation. Data must survive container restarts.

## Global Constraints

- Follow `/mnt/c/Users/SepehrMaadani/Documents/rules.md`. Every task appends an entry to `agentlog.md` at the repo root in the existing format (`## [<ISO timestamp>] — <title>`, then `### WHAT changed` and `### WHY changed`). Get the timestamp from `date -Iseconds`.
- Every task writes the docs listed in its **Docs** step, using the rules.md templates in the exact heading order given. A task is not done without its code, docs and agentlog entry.
- Never hardcode or print secrets. Never `cat` or echo `.env`. Only the controller edits `.env`.
- Never log passwords, tokens or request bodies.
- Backend imports are **flat from `app/backend`**, for example `from tasks.services import TaskService`. Never write `from backend.x import ...`.
- Frontend imports are **flat from `app/frontend`**, for example `from api.client import ApiClient`.
- Test names use the form `test_<unit>_should_<behaviour>` and the AAA pattern. Unit tests use no DB or network.
- Pinned versions: `flet[web]==1.0.3`, `httpx==0.28.1`, `pytest==8.3.5`. Don't add other new dependencies.
- The flet 1.0 API is **not** 0.x. Use `ft.Button(content=...)` (there is no `ElevatedButton`), `ft.Icons.X`, `ft.Padding.only(...)`, `ft.BorderRadius.only(...)`, `ft.Alignment.CENTER`, `ft.Scale(...)`, `ft.Animation(...)`, `page.push_route(route)` (async), `page.run_task(fn, *args)`, `page.show_dialog(ctrl)` / `page.pop_dialog()`, `ft.View(route=..., controls=[...])` (keyword args only), `TextField(error=...)`, and `Dropdown(on_select=...)`.
- Work on branch `feat/fullstack-task-wiring`. Commit once per task. Every commit message ends with `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
- Run backend tests with `cd app/backend && python -m pytest -q`. Run frontend tests with `cd app/frontend && python -m pytest -q`. Both use the interpreter at `/mnt/c/Users/SepehrMaadani/Documents/linux_venv/bin/python`. Install frontend test deps into that venv only if they're missing: `pip install httpx==0.28.1 pytest==8.3.5`. Do **not** install `flet` there, because `flet-web` conflicts with the backend's pinned uvicorn.

## Review Focus

1. **Whitespace-only title** (`"   "`) must be rejected with 422 and must never be stored as a blank task. Pinned by the Task 2 entity test and the Task 3 API test.
2. **Unchecking a completed task** must persist `is_completed=false`. The old code dropped falsy updates. Pinned by the Task 2 service test and the Task 3 API test.
3. **Access token expiring mid-session** (15-minute lifetime): the client refreshes once, silently. If the refresh also fails, the user goes to the login screen with a friendly message instead of a crash. Pinned by the Task 6 `ApiClient` tests.
4. **Backend down or returning 5xx:** the user sees a friendly generic message, and no status codes or stack details leak into the UI. Pinned by the Task 6 `ApiClient` tests.
5. **Another user's task id** (for example, a hand-typed `/tasks/5`): the API returns 404, and the UI shows "That item no longer exists." then returns home. Pinned by the Task 3 API test (`other_client`) and the Task 6 client test for the 404 message.
6. **Passwords echoed back in validation errors** (a register mismatch returns 422): the response must not contain the submitted password. Pinned by a Task 4 API test.

---

## File Structure

```
.env.example                              NEW   documented env vars (no secrets)
.dockerignore                             NEW   keep caches/tests/.env out of images
.github/workflows/CI.yml                  MOD   lint + backend tests + frontend tests jobs
docker-compose.yml                        MOD   explicit env, healthchecks, strict nets, no-new-privileges
Dockerfile.backend                        MOD   non-root, healthcheck, alembic on start
Dockerfile.frontend                       MOD   non-root, healthcheck
README.md                                 MOD   stack/run instructions (Postgres, Flet web)
agentlog.md                               MOD   one entry per task
docs/                                     NEW   rules.md documentation tree (per task)

app/backend/
  pytest.ini                              NEW   pythonpath=., testpaths=tests
  main.py                                 MOD   flat imports, CORS from settings, safe error handlers, domain handlers, health router
  core/config.py                          MOD   CORS_ORIGINS, extra="ignore"
  health/__init__.py, health/routes.py    NEW   GET /health (DB ping)
  tasks/entities.py                       NEW   Task, TaskCategory, CategorySummary, domain errors + rules
  tasks/ports.py                          NEW   TaskRepository Protocol
  tasks/services.py                       NEW   TaskService use cases
  tasks/adapters.py                       NEW   SqlAlchemyTaskRepository
  tasks/dependencies.py                   NEW   get_task_service (composition root)
  tasks/models.py                         MOD   category column, FK not-null + index, real onupdate
  tasks/schemas.py                        MOD   create / partial-update / response / summary DTOs
  tasks/routes.py                         MOD   thin HTTP layer incl. PATCH + /tasks/summary
  users/models.py                         MOD   unique username
  users/schemas.py                        MOD   username/password length rules, normalisation
  users/routes.py                         MOD   refresh checks user still exists
  auth/jwt_auth.py                        MOD   PyJWT-validated expiry, generic 401s, no None user
  alembic.ini, migrations/env.py, migrations/script.py.mako, migrations/versions/0001_initial_schema.py   NEW
  tests/conftest.py                       MOD   env only
  tests/api/{__init__,conftest,test_tasks_api,test_users_api,test_health_api}.py        NEW (moved)
  tests/unit/{__init__,fakes,test_task_entities,test_task_service,test_jwt_auth}.py     NEW
  tests/integration/{__init__,test_migrations}.py                                        NEW

app/frontend/
  requirements.txt                        MOD   + httpx
  requirements-dev.txt, pytest.ini        NEW
  main.py                                 REWRITE  bootstrap only
  config.py                               NEW   env → FrontendSettings
  router.py                               NEW   route table + auth guard
  api/__init__.py, api/client.py          NEW   ApiClient, ApiError, AuthenticationError
  features/__init__.py
  features/auth/{__init__,validation,service,views}.py         NEW
  features/tasks/{__init__,models,service,home_view,form_view}.py  NEW
  shared/{__init__,theme,ui}.py           NEW
  custom_checkbox.py, mock.py             DELETE (replaced by ft.Checkbox; mock unused)
  tests/{__init__}.py, tests/unit/{__init__,test_api_client,test_auth,test_task_models,test_task_service}.py  NEW
```

---

### Task 1: Foundation: branch, flat imports, config, test layout, CI, agentlog backfill

**Files:**
- Modify: `app/backend/main.py` (full rewrite below)
- Modify: `app/backend/core/config.py`
- Create: `app/backend/pytest.ini`
- Modify: `app/backend/tests/conftest.py`
- Move: `app/backend/tests/test_users_api.py` → `app/backend/tests/api/test_users_api.py`, then rewrite it
- Delete: `app/backend/tests/test_tasks_api.py` (its only test asserts a non-existent route 404s; Task 3 replaces it)
- Create: `app/backend/tests/api/__init__.py`, `app/backend/tests/api/conftest.py`, `app/backend/tests/unit/__init__.py`, `app/backend/tests/integration/__init__.py` (the `__init__` files are empty)
- Modify: `.github/workflows/CI.yml`
- Create: `docs/onboarding/dev-setup.md`
- Modify: `agentlog.md`

**Interfaces:**
- Produces: `settings.SQLALCHEMY_DATABASE_URL: str`, `settings.JWT_SECRET_KEY: str`, `settings.CORS_ORIGINS: list[str]`. Also `main.error_response(status_code: int, detail: Any, headers: dict | None = None) -> JSONResponse`. API test fixtures in `tests/api/conftest.py`: `db_session`, `user`, `other_user`, `anonymous_client`, `auth_client`, `other_client`.

- [ ] **Step 1: Create the branch**

```bash
cd /mnt/c/Users/SepehrMaadani/Documents/oldProjects/fast_API/todo
git checkout -b feat/fullstack-task-wiring
```

- [ ] **Step 2: Replace `app/backend/core/config.py`**

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend configuration, read from environment variables (or a local .env file)."""

    SQLALCHEMY_DATABASE_URL: str
    JWT_SECRET_KEY: str = Field(min_length=1)
    # JSON list, e.g. CORS_ORIGINS='["http://localhost:3000"]'. Empty = no cross-origin browser access.
    CORS_ORIGINS: list[str] = []

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
```

- [ ] **Step 3: Replace `app/backend/main.py`**

This version switches to flat imports, reads CORS from settings, and adds error handlers that no longer print raw exception state. They also no longer echo submitted input (such as passwords) back to the client.

```python
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.config import settings
from pages.routes import router as pages_routes
from tasks.routes import router as tasks_routes
from users.routes import router as users_routes

logger = logging.getLogger("todo")

tags_metadata = [
    {
        "name": "tasks",
        "description": "Operations related to task management",
        "externalDocs": {
            "description": "More about tasks",
            "url": "https://example.com/docs/tasks",
        },
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan"""
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    title="Todo App",
    description="Simple todo app for testing purpose",
    summary="Remember everything todo...",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Sepehr Maadani",
        "url": "https://github.com/sepehrmdn77/todo",
        "email": "sepehrmaadani98@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://choosealicense.com/",
    },
)

app.include_router(tasks_routes)
app.include_router(users_routes)
app.include_router(pages_routes)


@app.post("/set-cookie", tags=["Cookie management"])
def set_cookie(response: Response):
    response.set_cookie(key="test", value="something")
    return {"message": "Cookie has been set successfully"}


@app.get("/get-cookie", tags=["Cookie management"])
def get_cookie(request: Request):
    return {"requested cookie": request.cookies.get("test")}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def error_response(
    status_code: int, detail: Any, headers: Optional[dict[str, str]] = None
) -> JSONResponse:
    """Uniform error body used by every handler: {"error", "status_code", "detail"}."""
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "status_code": status_code, "detail": detail},
        headers=headers,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return error_response(exc.status_code, exc.detail, getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.info("Validation failed for %s %s", request.method, request.url.path)
    # Drop "input"/"ctx": they can contain submitted secrets (e.g. passwords).
    errors = [
        {key: value for key, value in error.items() if key not in ("input", "ctx")}
        for error in exc.errors()
    ]
    return error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, jsonable_encoder(errors))
```

- [ ] **Step 4: Create `app/backend/pytest.ini`**

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 5: Replace `app/backend/tests/conftest.py`**

```python
import os

# Settings are read at import time; give the test process a self-contained configuration
# so tests never depend on (or touch) a developer's real database or secrets.
os.environ["SQLALCHEMY_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["CORS_ORIGINS"] = "[]"
```

- [ ] **Step 6: Create `app/backend/tests/api/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from auth.jwt_auth import generate_access_token
from core.database import Base, get_db
from main import app
from tasks.models import TaskModel  # noqa: F401  (registers the table on Base.metadata)
from users.models import UsersModel

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DEFAULT_PASSWORD = "12345678"


@pytest.fixture(autouse=True)
def db_session():
    """Fresh schema for every test so tests never depend on each other's data."""
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    app.dependency_overrides[get_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        Base.metadata.drop_all(bind=engine)


def create_user(session: Session, username: str, password: str = DEFAULT_PASSWORD) -> UsersModel:
    user = UsersModel(username=username)
    user.set_password(password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def client_for(user: UsersModel) -> TestClient:
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {generate_access_token(user.id)}"
    return client


@pytest.fixture
def user(db_session):
    return create_user(db_session, "usertest")


@pytest.fixture
def other_user(db_session):
    return create_user(db_session, "otheruser")


@pytest.fixture
def anonymous_client():
    return TestClient(app)


@pytest.fixture
def auth_client(user):
    return client_for(user)


@pytest.fixture
def other_client(other_user):
    return client_for(other_user)
```

- [ ] **Step 7: Move and rewrite the users API test**

```bash
cd /mnt/c/Users/SepehrMaadani/Documents/oldProjects/fast_API/todo/app/backend
git mv tests/test_users_api.py tests/api/test_users_api.py
git rm -q tests/test_tasks_api.py
touch tests/api/__init__.py tests/unit/__init__.py tests/integration/__init__.py
```

Run `mkdir -p tests/api tests/unit tests/integration` **before** the `git mv` above (the target directories must exist). Then replace the content of `tests/api/test_users_api.py`:

```python
from tests.api.conftest import DEFAULT_PASSWORD


def test_login_should_return_401_for_unknown_user(anonymous_client):
    response = anonymous_client.post("/users/login", json={"username": "nobody", "password": "1234567"})
    assert response.status_code == 401


def test_login_should_return_401_for_wrong_password(anonymous_client, user):
    response = anonymous_client.post("/users/login", json={"username": user.username, "password": "@1234567"})
    assert response.status_code == 401


def test_register_should_return_201(anonymous_client):
    payload = {"username": "kazem", "password": "secret1234", "confirm_password": "secret1234"}
    response = anonymous_client.post("/users/register", json=payload)
    assert response.status_code == 201


def test_login_should_return_202_with_tokens(anonymous_client, user):
    response = anonymous_client.post("/users/login", json={"username": user.username, "password": DEFAULT_PASSWORD})
    assert response.status_code == 202
    body = response.json()
    assert body["access_token"] and body["refresh_token"]
```

- [ ] **Step 8: Run the backend tests**

Run: `cd app/backend && python -m pytest -q`
Expected: `4 passed`. `main.py` imports `tasks.routes` flat, and the current routes and models still work.

- [ ] **Step 9: Replace `.github/workflows/CI.yml`**

```yaml
name: CI for ToDo app

run-name: ${{ github.actor }} is running workflow

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install flake8
        run: pip install flake8==7.1.1
      - name: Lint with flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

  backend-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    defaults:
      run:
        working-directory: app/backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: app/backend/requirements.txt
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest --disable-warnings -v
```

- [ ] **Step 10: Docs.** Create `docs/onboarding/dev-setup.md` with these sections: `# Developer Setup`, `## Prerequisites` (Python 3.12, Docker + Compose), `## Repository Layout` (app/backend, app/frontend, docs, Dockerfiles, compose), `## Configuration` (the root `.env` is created from `.env.example`, which arrives in Task 8; never commit `.env`), `## Running Backend Tests` (`cd app/backend && python -m pytest -q`; tests set their own env in `tests/conftest.py`; layout `tests/unit`, `tests/api`, `tests/integration`), `## Import Convention` (flat imports from `app/backend` and `app/frontend`, with the reason why).

- [ ] **Step 11: agentlog.** Append two entries to `agentlog.md`:
  1. A **backfill** for the earlier session. WHAT: `Dockerfile.frontend` and the frontend dependency split (`app/frontend/requirements.txt` with `flet[web]==1.0.3`, removed from the backend requirements), `FLET_SERVER_IP=0.0.0.0`, and the port of `main.py`/`custom_checkbox.py` to the flet 1.0 API (`ElevatedButton`→`Button(content=)`, lowercase helper modules → classes, `page.go`→`push_route`, keyword `View(route=, controls=)`, `FontWeight.W_700`). WHY: flet 1.0 removed those APIs, which crash-looped the container with `ImportError: cannot import name 'ElevatedButton'`; `flet-web` needs a newer uvicorn/fastapi than the backend pins.
  2. This task. WHAT: flat backend imports, `CORS_ORIGINS` setting, error handlers that no longer print exceptions or echo input, the `tests/unit|api|integration` layout with a per-test DB, and the CI fix. WHY: CI was installing a `requirements.txt` that had moved; mixed `backend.*` and flat imports only worked through PYTHONPATH tricks; the validation handler echoed passwords and could 500 on `ValueError` ctx; and module-scoped fixtures leaked data between test files.

- [ ] **Step 12: Commit**

```bash
git add -A app/backend .github/workflows/CI.yml docs/onboarding/dev-setup.md agentlog.md
git commit -m "chore(backend): flat imports, env-driven CORS, safe error handlers, test layout, CI fix

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

`agentlog.md` is listed in `.gitignore`, so git refuses to add it without force. Use `git add -f agentlog.md`. The user keeps it local-only by choice, so if `git add -f` is the only way, leave it **uncommitted** instead: skip it in the `git add` and just keep the file updated. This applies to every later task too.

---

### Task 2: Task domain: entity, port, service (unit-tested)

**Files:**
- Create: `app/backend/tasks/entities.py`, `app/backend/tasks/ports.py`, `app/backend/tasks/services.py`
- Test: `app/backend/tests/unit/fakes.py`, `app/backend/tests/unit/test_task_entities.py`, `app/backend/tests/unit/test_task_service.py`

**Interfaces:**
- Produces (used by Task 3):
  - `TaskCategory(str, Enum)`: `UNIVERSITY="university"`, `FINNISH="finnish"`, `GENERAL="general"`
  - `TITLE_MAX_LENGTH = 150`, `DESCRIPTION_MAX_LENGTH = 500`
  - `Task` dataclass with fields `user_id: int, title: str, description: Optional[str]=None, is_completed: bool=False, category: Optional[TaskCategory]=None, id: Optional[int]=None, created_date: Optional[datetime]=None, updated_date: Optional[datetime]=None`, and `Task.apply_changes(changes: Mapping[str, Any]) -> None`
  - `CategorySummary(category: TaskCategory, total: int, completed: int)` (frozen)
  - `TaskNotFoundError(task_id: int)`, `InvalidTaskError(ValueError)`
  - `TaskRepository` Protocol with `list_for_user`, `get_for_user`, `add`, `save`, `delete`, `summarize_by_category` (exact signatures below)
  - `TaskService(repository)` with `list_tasks`, `get_task`, `create_task`, `update_task`, `delete_task`, `summarize_categories`

- [ ] **Step 1: Write failing entity tests**: `app/backend/tests/unit/test_task_entities.py`

```python
import pytest

from tasks.entities import (
    DESCRIPTION_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    InvalidTaskError,
    Task,
    TaskCategory,
)


def test_task_should_strip_title_and_description():
    task = Task(user_id=1, title="  Buy milk  ", description="  2 litres ")
    assert task.title == "Buy milk"
    assert task.description == "2 litres"


def test_task_should_reject_whitespace_only_title():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="   ")


def test_task_should_reject_title_longer_than_limit():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="x" * (TITLE_MAX_LENGTH + 1))


def test_task_should_store_blank_description_as_none():
    assert Task(user_id=1, title="Read", description="   ").description is None


def test_task_should_reject_description_longer_than_limit():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="Read", description="x" * (DESCRIPTION_MAX_LENGTH + 1))


def test_task_should_accept_category_given_as_string():
    assert Task(user_id=1, title="Verbs", category="finnish").category is TaskCategory.FINNISH


def test_task_should_reject_unknown_category():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="Verbs", category="cooking")


def test_apply_changes_should_only_touch_given_fields():
    task = Task(user_id=1, title="Old", description="keep", category=TaskCategory.GENERAL)
    task.apply_changes({"title": "New"})
    assert (task.title, task.description, task.category) == ("New", "keep", TaskCategory.GENERAL)


def test_apply_changes_should_allow_marking_incomplete():
    task = Task(user_id=1, title="Done already", is_completed=True)
    task.apply_changes({"is_completed": False})
    assert task.is_completed is False


def test_apply_changes_should_clear_description_and_category_with_none():
    task = Task(user_id=1, title="T", description="d", category=TaskCategory.FINNISH)
    task.apply_changes({"description": None, "category": None})
    assert task.description is None and task.category is None


def test_apply_changes_should_reject_null_title():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="T").apply_changes({"title": None})


def test_apply_changes_should_reject_null_completion():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="T").apply_changes({"is_completed": None})


def test_apply_changes_should_reject_unknown_fields():
    with pytest.raises(InvalidTaskError):
        Task(user_id=1, title="T").apply_changes({"user_id": 2})
```

- [ ] **Step 2: Run to verify failure**

Run: `cd app/backend && python -m pytest tests/unit/test_task_entities.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'tasks.entities'`.

- [ ] **Step 3: Implement `app/backend/tasks/entities.py`**

```python
"""Task domain model and rules. Pure Python: no ORM, HTTP or framework imports."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional

TITLE_MAX_LENGTH = 150
DESCRIPTION_MAX_LENGTH = 500
UPDATABLE_FIELDS = frozenset({"title", "description", "is_completed", "category"})


class TaskCategory(str, Enum):
    UNIVERSITY = "university"
    FINNISH = "finnish"
    GENERAL = "general"


class InvalidTaskError(ValueError):
    """Task data breaks a domain rule. The message is safe to show to users."""


class TaskNotFoundError(Exception):
    """The task does not exist or belongs to another user."""

    def __init__(self, task_id: int) -> None:
        super().__init__(f"Task {task_id} not found")
        self.task_id = task_id


def normalize_title(title: Any) -> str:
    if not isinstance(title, str):
        raise InvalidTaskError("Title is required")
    cleaned = title.strip()
    if not cleaned:
        raise InvalidTaskError("Title must not be blank")
    if len(cleaned) > TITLE_MAX_LENGTH:
        raise InvalidTaskError(f"Title must be at most {TITLE_MAX_LENGTH} characters")
    return cleaned


def normalize_description(description: Any) -> Optional[str]:
    if description is None:
        return None
    if not isinstance(description, str):
        raise InvalidTaskError("Description must be text")
    cleaned = description.strip()
    if len(cleaned) > DESCRIPTION_MAX_LENGTH:
        raise InvalidTaskError(f"Description must be at most {DESCRIPTION_MAX_LENGTH} characters")
    return cleaned or None


def to_category(value: Any) -> Optional[TaskCategory]:
    if value is None or isinstance(value, TaskCategory):
        return value
    try:
        return TaskCategory(value)
    except ValueError:
        raise InvalidTaskError(f"Unknown category: {value}") from None


def require_completion_flag(value: Any) -> bool:
    if not isinstance(value, bool):
        raise InvalidTaskError("Completion status must be true or false")
    return value


@dataclass
class Task:
    user_id: int
    title: str
    description: Optional[str] = None
    is_completed: bool = False
    category: Optional[TaskCategory] = None
    id: Optional[int] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

    def __post_init__(self) -> None:
        self.title = normalize_title(self.title)
        self.description = normalize_description(self.description)
        self.is_completed = require_completion_flag(self.is_completed)
        self.category = to_category(self.category)

    def apply_changes(self, changes: Mapping[str, Any]) -> None:
        """Apply a partial update. Only keys present in `changes` are modified."""
        unknown = set(changes) - UPDATABLE_FIELDS
        if unknown:
            raise InvalidTaskError(f"Unknown task fields: {', '.join(sorted(unknown))}")
        if "title" in changes:
            self.title = normalize_title(changes["title"])
        if "description" in changes:
            self.description = normalize_description(changes["description"])
        if "is_completed" in changes:
            self.is_completed = require_completion_flag(changes["is_completed"])
        if "category" in changes:
            self.category = to_category(changes["category"])


@dataclass(frozen=True)
class CategorySummary:
    category: TaskCategory
    total: int
    completed: int
```

- [ ] **Step 4: Run entity tests**

Run: `cd app/backend && python -m pytest tests/unit/test_task_entities.py -q`
Expected: `13 passed`.

- [ ] **Step 5: Implement `app/backend/tasks/ports.py`**

```python
"""What the task use cases need from storage. Implementations live in tasks/adapters.py."""

from typing import Optional, Protocol

from tasks.entities import CategorySummary, Task, TaskCategory


class TaskRepository(Protocol):
    def list_for_user(
        self,
        user_id: int,
        *,
        completed: Optional[bool],
        category: Optional[TaskCategory],
        limit: int,
        offset: int,
    ) -> list[Task]:
        """Tasks of one user: incomplete first, then newest first."""
        ...

    def get_for_user(self, user_id: int, task_id: int) -> Optional[Task]: ...

    def add(self, task: Task) -> Task:
        """Persist a new task and return it with id and timestamps set."""
        ...

    def save(self, task: Task) -> Task:
        """Persist changes to an existing task and return the stored state."""
        ...

    def delete(self, task: Task) -> None: ...

    def summarize_by_category(self, user_id: int) -> list[CategorySummary]:
        """Counts for categories that have at least one task (uncategorised tasks excluded)."""
        ...
```

- [ ] **Step 6: Write the fake repository**: `app/backend/tests/unit/fakes.py`

```python
from dataclasses import replace
from typing import Optional

from tasks.entities import CategorySummary, Task, TaskCategory


class InMemoryTaskRepository:
    """TaskRepository test double; returns copies so callers can't mutate stored state."""

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id = 1

    def list_for_user(self, user_id, *, completed, category, limit, offset) -> list[Task]:
        matching = [
            task
            for task in self._tasks.values()
            if task.user_id == user_id
            and (completed is None or task.is_completed == completed)
            and (category is None or task.category == category)
        ]
        return [replace(task) for task in matching[offset: offset + limit]]

    def get_for_user(self, user_id: int, task_id: int) -> Optional[Task]:
        task = self._tasks.get(task_id)
        return replace(task) if task and task.user_id == user_id else None

    def add(self, task: Task) -> Task:
        stored = replace(task, id=self._next_id)
        self._tasks[stored.id] = stored
        self._next_id += 1
        return replace(stored)

    def save(self, task: Task) -> Task:
        self._tasks[task.id] = replace(task)
        return replace(task)

    def delete(self, task: Task) -> None:
        self._tasks.pop(task.id, None)

    def summarize_by_category(self, user_id: int) -> list[CategorySummary]:
        summaries = []
        for category in TaskCategory:
            tasks = [t for t in self._tasks.values() if t.user_id == user_id and t.category == category]
            if tasks:
                done = sum(1 for t in tasks if t.is_completed)
                summaries.append(CategorySummary(category=category, total=len(tasks), completed=done))
        return summaries
```

- [ ] **Step 7: Write failing service tests**: `app/backend/tests/unit/test_task_service.py`

```python
import pytest

from tasks.entities import CategorySummary, InvalidTaskError, TaskCategory, TaskNotFoundError
from tasks.services import TaskService
from tests.unit.fakes import InMemoryTaskRepository

OWNER_ID = 1
STRANGER_ID = 2


@pytest.fixture
def service():
    return TaskService(InMemoryTaskRepository())


def test_create_task_should_return_stored_task_with_id(service):
    task = service.create_task(OWNER_ID, title=" Essay ", category=TaskCategory.UNIVERSITY)
    assert task.id is not None
    assert task.title == "Essay"
    assert service.get_task(OWNER_ID, task.id).category is TaskCategory.UNIVERSITY


def test_create_task_should_reject_blank_title(service):
    with pytest.raises(InvalidTaskError):
        service.create_task(OWNER_ID, title="  ")


def test_get_task_should_hide_other_users_tasks(service):
    task = service.create_task(OWNER_ID, title="Private")
    with pytest.raises(TaskNotFoundError):
        service.get_task(STRANGER_ID, task.id)


def test_list_tasks_should_filter_by_completion_and_category(service):
    service.create_task(OWNER_ID, title="A", category=TaskCategory.FINNISH, is_completed=True)
    service.create_task(OWNER_ID, title="B", category=TaskCategory.FINNISH)
    service.create_task(OWNER_ID, title="C", category=TaskCategory.GENERAL, is_completed=True)
    titles = [t.title for t in service.list_tasks(OWNER_ID, completed=True, category=TaskCategory.FINNISH)]
    assert titles == ["A"]


def test_update_task_should_apply_partial_changes(service):
    task = service.create_task(OWNER_ID, title="Old", description="keep")
    updated = service.update_task(OWNER_ID, task.id, {"title": "New"})
    assert (updated.title, updated.description) == ("New", "keep")


def test_update_task_should_persist_marking_incomplete(service):
    task = service.create_task(OWNER_ID, title="Done", is_completed=True)
    service.update_task(OWNER_ID, task.id, {"is_completed": False})
    assert service.get_task(OWNER_ID, task.id).is_completed is False


def test_update_task_should_reject_other_users_task(service):
    task = service.create_task(OWNER_ID, title="Mine")
    with pytest.raises(TaskNotFoundError):
        service.update_task(STRANGER_ID, task.id, {"title": "Hacked"})


def test_delete_task_should_remove_task(service):
    task = service.create_task(OWNER_ID, title="Temp")
    service.delete_task(OWNER_ID, task.id)
    with pytest.raises(TaskNotFoundError):
        service.get_task(OWNER_ID, task.id)


def test_summarize_categories_should_zero_fill_every_category_in_order(service):
    service.create_task(OWNER_ID, title="A", category=TaskCategory.GENERAL, is_completed=True)
    service.create_task(OWNER_ID, title="B", category=TaskCategory.GENERAL)
    assert service.summarize_categories(OWNER_ID) == [
        CategorySummary(TaskCategory.UNIVERSITY, total=0, completed=0),
        CategorySummary(TaskCategory.FINNISH, total=0, completed=0),
        CategorySummary(TaskCategory.GENERAL, total=2, completed=1),
    ]
```

- [ ] **Step 8: Run to verify failure**

Run: `cd app/backend && python -m pytest tests/unit/test_task_service.py -q`
Expected: collection error, `No module named 'tasks.services'`.

- [ ] **Step 9: Implement `app/backend/tasks/services.py`**

```python
"""Task use cases. Depends only on entities and the TaskRepository port."""

from typing import Any, Mapping, Optional

from tasks.entities import CategorySummary, Task, TaskCategory, TaskNotFoundError
from tasks.ports import TaskRepository

DEFAULT_PAGE_SIZE = 50


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def list_tasks(
        self,
        user_id: int,
        *,
        completed: Optional[bool] = None,
        category: Optional[TaskCategory] = None,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> list[Task]:
        return self._repository.list_for_user(
            user_id, completed=completed, category=category, limit=limit, offset=offset
        )

    def get_task(self, user_id: int, task_id: int) -> Task:
        task = self._repository.get_for_user(user_id, task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def create_task(
        self,
        user_id: int,
        *,
        title: str,
        description: Optional[str] = None,
        category: Optional[TaskCategory] = None,
        is_completed: bool = False,
    ) -> Task:
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            is_completed=is_completed,
        )
        return self._repository.add(task)

    def update_task(self, user_id: int, task_id: int, changes: Mapping[str, Any]) -> Task:
        task = self.get_task(user_id, task_id)
        task.apply_changes(changes)
        return self._repository.save(task)

    def delete_task(self, user_id: int, task_id: int) -> None:
        self._repository.delete(self.get_task(user_id, task_id))

    def summarize_categories(self, user_id: int) -> list[CategorySummary]:
        """One summary per category (zero-filled), in TaskCategory declaration order."""
        found = {s.category: s for s in self._repository.summarize_by_category(user_id)}
        return [found.get(c, CategorySummary(category=c, total=0, completed=0)) for c in TaskCategory]
```

- [ ] **Step 10: Run all unit tests**

Run: `cd app/backend && python -m pytest tests/unit -q`
Expected: `22 passed`.

- [ ] **Step 11: agentlog.** Append an entry. WHAT: the tasks domain (`entities.py`, `ports.py`, `services.py`) with unit tests. WHY: rules.md Lich architecture; business rules (title normalisation, partial updates including un-completing, category validation, per-user isolation) now live in one testable place instead of in route bodies. Docs for the tasks module are written in Task 3, once the adapter and endpoints exist.

- [ ] **Step 12: Commit**

```bash
git add app/backend/tasks/entities.py app/backend/tasks/ports.py app/backend/tasks/services.py app/backend/tests/unit
git commit -m "feat(backend): task domain entity, repository port and service

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Task persistence and HTTP: ORM, adapter, DTOs, routes (API-tested)

**Files:**
- Modify: `app/backend/tasks/models.py`, `app/backend/tasks/schemas.py`, `app/backend/tasks/routes.py`, `app/backend/main.py` (add domain error handlers)
- Create: `app/backend/tasks/adapters.py`, `app/backend/tasks/dependencies.py`
- Test: `app/backend/tests/api/test_tasks_api.py`
- Docs: `docs/features/backend/tasks.md`, `docs/architecture/backend-architecture.md`

**Interfaces:**
- Consumes: everything Task 2 produces. It also uses `get_authenticated_user` from `auth.jwt_auth` (returns a `UsersModel` with `.id`) and `get_db` from `core.database`.
- Produces the HTTP contract that the frontend (Task 6) relies on. All paths are under `/todo` and need `Authorization: Bearer <access>`:
  - `GET /todo/tasks?limit=1..100 (default 50)&offset>=0 (default 0)&completed=bool&category=<cat>` → 200 `[TaskResponse]`
  - `GET /todo/tasks/summary` → 200 `[{"category": str, "total": int, "completed": int}]`, one entry per category in the order university, finnish, general
  - `GET /todo/tasks/{id}` → 200 `TaskResponse` or 404
  - `POST /todo/tasks` with body `{"title": str, "description"?: str|null, "category"?: cat|null, "is_completed"?: bool}` → **201** `TaskResponse`
  - `PATCH /todo/tasks/{id}` with any subset of those fields (`null` clears description or category) → 200 `TaskResponse`
  - `DELETE /todo/tasks/{id}` → 204
  - `TaskResponse` = `{"id", "title", "description", "category", "is_completed", "created_date", "updated_date"}`
  - Errors use the body `{"error": true, "status_code": int, "detail": str|list}`. Unknown or foreign ids return 404 with `detail="Task not found"`. Domain rule violations return 422 with a user-safe `detail` string.

- [ ] **Step 1: Write the failing API tests**: `app/backend/tests/api/test_tasks_api.py`

```python
TASKS_URL = "/todo/tasks"


def create(client, **fields):
    payload = {"title": "Write essay", **fields}
    response = client.post(TASKS_URL, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_tasks_should_require_authentication(anonymous_client):
    assert anonymous_client.get(TASKS_URL).status_code in (401, 403)


def test_create_task_should_return_201_with_defaults(auth_client):
    task = create(auth_client, category="university")
    assert task["title"] == "Write essay"
    assert task["category"] == "university"
    assert task["is_completed"] is False
    assert task["description"] is None


def test_create_task_should_reject_whitespace_title(auth_client):
    response = auth_client.post(TASKS_URL, json={"title": "   "})
    assert response.status_code == 422
    assert auth_client.get(TASKS_URL).json() == []


def test_create_task_should_reject_unknown_category(auth_client):
    assert auth_client.post(TASKS_URL, json={"title": "Cook", "category": "cooking"}).status_code == 422


def test_create_task_should_reject_unknown_fields(auth_client):
    assert auth_client.post(TASKS_URL, json={"title": "T", "user_id": 99}).status_code == 422


def test_list_tasks_should_include_first_task_by_default(auth_client):
    first = create(auth_client, title="First")
    assert [t["id"] for t in auth_client.get(TASKS_URL).json()] == [first["id"]]


def test_list_tasks_should_filter_by_category_and_completion(auth_client):
    create(auth_client, title="Verbs", category="finnish", is_completed=True)
    create(auth_client, title="Nouns", category="finnish")
    create(auth_client, title="Sketch", category="general", is_completed=True)
    response = auth_client.get(TASKS_URL, params={"category": "finnish", "completed": "true"})
    assert [t["title"] for t in response.json()] == ["Verbs"]


def test_list_tasks_should_reject_limit_over_100(auth_client):
    assert auth_client.get(TASKS_URL, params={"limit": 101}).status_code == 422


def test_get_task_should_return_404_for_other_users_task(auth_client, other_client):
    task = create(auth_client)
    response = other_client.get(f"{TASKS_URL}/{task['id']}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_patch_task_should_update_only_given_fields(auth_client):
    task = create(auth_client, description="keep me", category="general")
    response = auth_client.patch(f"{TASKS_URL}/{task['id']}", json={"title": "Renamed"})
    assert response.status_code == 200
    body = response.json()
    assert (body["title"], body["description"], body["category"]) == ("Renamed", "keep me", "general")


def test_patch_task_should_persist_marking_incomplete(auth_client):
    task = create(auth_client, is_completed=True)
    auth_client.patch(f"{TASKS_URL}/{task['id']}", json={"is_completed": False})
    assert auth_client.get(f"{TASKS_URL}/{task['id']}").json()["is_completed"] is False


def test_patch_task_should_clear_description_and_category_with_null(auth_client):
    task = create(auth_client, description="d", category="finnish")
    body = auth_client.patch(f"{TASKS_URL}/{task['id']}", json={"description": None, "category": None}).json()
    assert body["description"] is None and body["category"] is None


def test_patch_task_should_reject_null_title(auth_client):
    task = create(auth_client)
    assert auth_client.patch(f"{TASKS_URL}/{task['id']}", json={"title": None}).status_code == 422


def test_patch_task_should_return_404_for_other_users_task(auth_client, other_client):
    task = create(auth_client)
    assert other_client.patch(f"{TASKS_URL}/{task['id']}", json={"title": "Mine now"}).status_code == 404


def test_delete_task_should_return_204_then_404(auth_client):
    task = create(auth_client)
    assert auth_client.delete(f"{TASKS_URL}/{task['id']}").status_code == 204
    assert auth_client.get(f"{TASKS_URL}/{task['id']}").status_code == 404


def test_summary_should_count_per_category_zero_filled(auth_client):
    create(auth_client, title="Verbs", category="finnish", is_completed=True)
    create(auth_client, title="Nouns", category="finnish")
    create(auth_client, title="No category")
    assert auth_client.get(f"{TASKS_URL}/summary").json() == [
        {"category": "university", "total": 0, "completed": 0},
        {"category": "finnish", "total": 2, "completed": 1},
        {"category": "general", "total": 0, "completed": 0},
    ]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd app/backend && python -m pytest tests/api/test_tasks_api.py -q`
Expected: many FAILs. For example, create returns 200 instead of 201, `category` is unknown, and `/summary` returns 422.

- [ ] **Step 3: Replace `app/backend/tasks/models.py`**

```python
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from core.database import Base
from tasks.entities import TITLE_MAX_LENGTH, TaskCategory


def _enum_values(enum_cls: type[TaskCategory]) -> list[str]:
    """Store enum *values* ("finnish"), not member names ("FINNISH")."""
    return [member.value for member in enum_cls]


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(TITLE_MAX_LENGTH), nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    category = Column(
        SqlEnum(TaskCategory, name="task_category", values_callable=_enum_values),
        nullable=True,
    )
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("UsersModel", back_populates="tasks", uselist=False)
```

- [ ] **Step 4: Create `app/backend/tasks/adapters.py`**

```python
"""SQLAlchemy implementation of the TaskRepository port."""

from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from tasks.entities import CategorySummary, Task, TaskCategory, TaskNotFoundError
from tasks.models import TaskModel


def _to_entity(row: TaskModel) -> Task:
    return Task(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        description=row.description,
        is_completed=row.is_completed,
        category=row.category,
        created_date=row.created_date,
        updated_date=row.updated_date,
    )


class SqlAlchemyTaskRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(
        self,
        user_id: int,
        *,
        completed: Optional[bool],
        category: Optional[TaskCategory],
        limit: int,
        offset: int,
    ) -> list[Task]:
        query = self._db.query(TaskModel).filter(TaskModel.user_id == user_id)
        if completed is not None:
            query = query.filter(TaskModel.is_completed == completed)
        if category is not None:
            query = query.filter(TaskModel.category == category)
        rows = (
            query.order_by(TaskModel.is_completed, TaskModel.created_date.desc(), TaskModel.id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [_to_entity(row) for row in rows]

    def get_for_user(self, user_id: int, task_id: int) -> Optional[Task]:
        row = self._find(user_id, task_id)
        return _to_entity(row) if row else None

    def add(self, task: Task) -> Task:
        row = TaskModel(
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            is_completed=task.is_completed,
            category=task.category,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return _to_entity(row)

    def save(self, task: Task) -> Task:
        row = self._find(task.user_id, task.id)
        if row is None:
            raise TaskNotFoundError(task.id)
        row.title = task.title
        row.description = task.description
        row.is_completed = task.is_completed
        row.category = task.category
        self._db.commit()
        self._db.refresh(row)
        return _to_entity(row)

    def delete(self, task: Task) -> None:
        row = self._find(task.user_id, task.id)
        if row is not None:
            self._db.delete(row)
            self._db.commit()

    def summarize_by_category(self, user_id: int) -> list[CategorySummary]:
        completed_count = func.sum(case((TaskModel.is_completed.is_(True), 1), else_=0))
        rows = (
            self._db.query(TaskModel.category, func.count(TaskModel.id), completed_count)
            .filter(TaskModel.user_id == user_id, TaskModel.category.isnot(None))
            .group_by(TaskModel.category)
            .all()
        )
        return [
            CategorySummary(category=category, total=total, completed=int(done or 0))
            for category, total, done in rows
        ]

    def _find(self, user_id: int, task_id: Optional[int]) -> Optional[TaskModel]:
        return self._db.query(TaskModel).filter_by(user_id=user_id, id=task_id).one_or_none()
```

- [ ] **Step 5: Create `app/backend/tasks/dependencies.py`**

```python
"""Composition root for the tasks module: wires the SQLAlchemy adapter into the service."""

from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from tasks.adapters import SqlAlchemyTaskRepository
from tasks.services import TaskService


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(SqlAlchemyTaskRepository(db))
```

- [ ] **Step 6: Replace `app/backend/tasks/schemas.py`**

```python
"""HTTP DTOs for the tasks API. Shape/length validation happens here, domain rules in entities."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from tasks.entities import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH, TaskCategory


class TaskCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=TITLE_MAX_LENGTH, description="Title of the task")
    description: Optional[str] = Field(None, max_length=DESCRIPTION_MAX_LENGTH, description="Optional details")
    category: Optional[TaskCategory] = Field(None, description="Optional category")
    is_completed: bool = Field(False, description="Completion status of the task")


class TaskUpdateSchema(BaseModel):
    """Partial update: only fields present in the request body are changed; null clears optional fields."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, min_length=1, max_length=TITLE_MAX_LENGTH)
    description: Optional[str] = Field(None, max_length=DESCRIPTION_MAX_LENGTH)
    category: Optional[TaskCategory] = None
    is_completed: Optional[bool] = None


class TaskResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique identifier of the object")
    title: str
    description: Optional[str]
    category: Optional[TaskCategory]
    is_completed: bool
    created_date: datetime = Field(..., description="Creation date and time of the object")
    updated_date: datetime = Field(..., description="Updating date and time of the object")


class CategorySummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: TaskCategory
    total: int
    completed: int
```

- [ ] **Step 7: Replace `app/backend/tasks/routes.py`**

This is a thin HTTP layer. The routes are sync `def` because SQLAlchemy is synchronous here, so FastAPI runs them in a threadpool instead of blocking the event loop.

```python
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Response, status

from auth.jwt_auth import get_authenticated_user
from tasks.dependencies import get_task_service
from tasks.entities import Task, TaskCategory
from tasks.schemas import (
    CategorySummarySchema,
    TaskCreateSchema,
    TaskResponseSchema,
    TaskUpdateSchema,
)
from tasks.services import DEFAULT_PAGE_SIZE, TaskService
from users.models import UsersModel

router = APIRouter(tags=["tasks"], prefix="/todo")

MAX_PAGE_SIZE = 100


@router.get("/tasks", response_model=list[TaskResponseSchema])
def list_tasks(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Page size"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    category: Optional[TaskCategory] = Query(None, description="Filter by category"),
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> list[Task]:
    return service.list_tasks(user.id, completed=completed, category=category, limit=limit, offset=offset)


# Declared before /tasks/{task_id} so "summary" is not parsed as an id.
@router.get("/tasks/summary", response_model=list[CategorySummarySchema])
def summarize_tasks(
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
):
    return service.summarize_categories(user.id)


@router.get("/tasks/{task_id}", response_model=TaskResponseSchema)
def retrieve_task(
    task_id: int = Path(..., gt=0),
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> Task:
    return service.get_task(user.id, task_id)


@router.post("/tasks", response_model=TaskResponseSchema, status_code=status.HTTP_201_CREATED)
def create_task(
    request: TaskCreateSchema,
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> Task:
    return service.create_task(user.id, **request.model_dump())


@router.patch("/tasks/{task_id}", response_model=TaskResponseSchema)
def update_task(
    request: TaskUpdateSchema,
    task_id: int = Path(..., gt=0),
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> Task:
    return service.update_task(user.id, task_id, request.model_dump(exclude_unset=True))


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int = Path(..., gt=0),
    service: TaskService = Depends(get_task_service),
    user: UsersModel = Depends(get_authenticated_user),
) -> Response:
    service.delete_task(user.id, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 8: Map domain errors to HTTP in `app/backend/main.py`.** Add this import next to the other imports:

```python
from tasks.entities import InvalidTaskError, TaskNotFoundError
```

Then append these handlers at the end of the file:

```python
@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
    return error_response(status.HTTP_404_NOT_FOUND, "Task not found")


@app.exception_handler(InvalidTaskError)
async def invalid_task_handler(request: Request, exc: InvalidTaskError):
    return error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
```

- [ ] **Step 9: Run the whole backend suite**

Run: `cd app/backend && python -m pytest -q`
Expected: all pass (22 unit, 16 task API and 4 users API tests). If `test_tasks_should_require_authentication` fails, record the actual code (FastAPI 0.115 `HTTPBearer` returns 403 when the header is missing). The test accepts 401 or 403 on purpose.

- [ ] **Step 10: Docs.** Write two files:
  - `docs/features/backend/tasks.md`: use the rules.md **Backend Module** template (`## 1. Purpose` through `## 10. Future Improvements`, in order). It must cover: entities (`Task`, `TaskCategory`, `CategorySummary`, and each rule with its limit: title 1–150 after trimming, description ≤500 with blank stored as null, fixed categories); service use cases; the `TaskRepository` port; `SqlAlchemyTaskRepository` (ordering: incomplete first, then newest); the full endpoint table from this task's **Interfaces** block, including status codes and the error body; where validation happens (DTO shape/lengths, then entity rules); the security model (every query is scoped by `user_id` from the JWT, and foreign ids give 404 rather than 403 so ids can't be enumerated); the testing strategy (unit tests with `InMemoryTaskRepository`, API tests with per-test SQLite); and future improvements (pagination in the UI, user-defined categories).
  - `docs/architecture/backend-architecture.md`: the module layout, the Lich layering applied to `tasks` (with an ASCII dependency diagram: routes → dependencies → services → ports ← adapters → models, and entities used by all), why `users`/`auth` weren't restructured (the agreed scope), the flat import convention, the error-body format, and configuration via `core/config.py`.

- [ ] **Step 11: agentlog.** Append an entry. WHAT: the `category` column, `user_id` made NOT NULL and indexed, a real `onupdate` for `updated_date`, the adapter, the composition root, new DTOs, `PATCH` replacing `PUT`, `/tasks/summary`, create returning 201, `offset` defaulting to 0, and domain error handlers. WHY: `offset=1` hid each user's first task; `PUT` required every field and ignored falsy values, so tasks could never be un-completed; `server_onupdate` never updated the timestamp; the UI needs categories and counts.

- [ ] **Step 12: Commit**

```bash
git add app/backend docs/features/backend/tasks.md docs/architecture/backend-architecture.md
git commit -m "feat(backend): task categories, partial updates, summary endpoint via Lich layers

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Auth hardening (JWT validation, input rules, unique usernames)

**Files:**
- Modify: `app/backend/auth/jwt_auth.py` (full replacement), `app/backend/users/schemas.py`, `app/backend/users/models.py:26` (username column), `app/backend/users/routes.py` (refresh endpoint)
- Test: `app/backend/tests/unit/test_jwt_auth.py`, `app/backend/tests/api/test_users_api.py` (extend)
- Docs: `docs/features/backend/auth.md`, `docs/troubleshooting/backend.md`

**Interfaces:**
- Consumes: `settings.JWT_SECRET_KEY`, `UsersModel`, and `get_db`.
- Produces (the names are unchanged, so existing importers keep working):
  - `generate_access_token(user_id: int, expire_in: int = ACCESS_TOKEN_TTL_SECONDS) -> str`
  - `generate_refresh_token(user_id: int, expire_in: int = REFRESH_TOKEN_TTL_SECONDS) -> str`
  - `decode_access_token(token: str) -> int`, which raises an `HTTPException` 401
  - `decode_refresh_token(token: str) -> int`, which raises an `HTTPException` 401
  - `get_authenticated_user(...) -> UsersModel`, which never returns `None`
  - Register rules: username is 3–250 characters after trimming and is stored lowercase; password is 8–128 characters.
  - Every auth failure returns 401 with `detail="Authentication failed"` and the header `WWW-Authenticate: Bearer`.
  - `POST /users/refresh_token` with `{"token": refresh}` returns 200 `{"access_token": str}`, or 401.

- [ ] **Step 1: Write the failing unit tests**: `app/backend/tests/unit/test_jwt_auth.py`

```python
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from auth.jwt_auth import (
    decode_access_token,
    decode_refresh_token,
    generate_access_token,
    generate_refresh_token,
)
from core.config import settings


def assert_rejected(decode, token):
    with pytest.raises(HTTPException) as caught:
        decode(token)
    assert caught.value.status_code == 401
    assert caught.value.detail == "Authentication failed"


def test_decode_access_token_should_return_user_id():
    assert decode_access_token(generate_access_token(7)) == 7


def test_decode_refresh_token_should_return_user_id():
    assert decode_refresh_token(generate_refresh_token(7)) == 7


def test_decode_access_token_should_reject_refresh_token():
    assert_rejected(decode_access_token, generate_refresh_token(7))


def test_decode_access_token_should_reject_expired_token():
    assert_rejected(decode_access_token, generate_access_token(7, expire_in=-1))


def test_decode_access_token_should_reject_foreign_signature():
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {"type": "access", "user_id": 7, "iat": now, "exp": now + timedelta(minutes=5)},
        "not-" + settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    assert_rejected(decode_access_token, forged)


def test_decode_access_token_should_reject_missing_user_id():
    now = datetime.now(timezone.utc)
    token = jwt.encode({"type": "access", "exp": now + timedelta(minutes=5)}, settings.JWT_SECRET_KEY, algorithm="HS256")
    assert_rejected(decode_access_token, token)


def test_decode_access_token_should_reject_garbage():
    assert_rejected(decode_access_token, "not-a-jwt")
```

- [ ] **Step 2: Extend `app/backend/tests/api/test_users_api.py`.** Append:

```python
from auth.jwt_auth import generate_refresh_token
from users.models import UsersModel


def register(client, username="newuser", password="secret1234", confirm=None):
    return client.post(
        "/users/register",
        json={"username": username, "password": password, "confirm_password": confirm or password},
    )


def test_register_should_reject_short_password(anonymous_client):
    assert register(anonymous_client, password="short").status_code == 422


def test_register_should_reject_short_username(anonymous_client):
    assert register(anonymous_client, username=" ab ").status_code == 422


def test_register_should_not_echo_password_on_mismatch(anonymous_client):
    response = register(anonymous_client, password="secret1234", confirm="different99")
    assert response.status_code == 422
    assert "secret1234" not in response.text and "different99" not in response.text


def test_register_should_reject_case_insensitive_duplicate(anonymous_client, user):
    assert register(anonymous_client, username=user.username.upper()).status_code == 409


def test_register_should_store_username_lowercase_and_trimmed(anonymous_client, db_session):
    register(anonymous_client, username="  NewUser ")
    assert db_session.query(UsersModel).filter_by(username="newuser").one_or_none() is not None


def test_refresh_token_should_issue_working_access_token(anonymous_client, user):
    response = anonymous_client.post("/users/refresh_token", json={"token": generate_refresh_token(user.id)})
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert anonymous_client.get("/todo/tasks", headers=headers).status_code == 200


def test_access_with_refresh_token_should_return_401(anonymous_client, user):
    headers = {"Authorization": f"Bearer {generate_refresh_token(user.id)}"}
    assert anonymous_client.get("/todo/tasks", headers=headers).status_code == 401


def test_token_of_deleted_user_should_return_401(auth_client, user, db_session):
    db_session.delete(user)
    db_session.commit()
    response = auth_client.get("/todo/tasks")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication failed"


def test_refresh_for_deleted_user_should_return_401(anonymous_client, user, db_session):
    token = generate_refresh_token(user.id)
    db_session.delete(user)
    db_session.commit()
    assert anonymous_client.post("/users/refresh_token", json={"token": token}).status_code == 401
```

Move the new imports to the top of the file, next to the existing one.

- [ ] **Step 3: Run to verify failure**

Run: `cd app/backend && python -m pytest tests/unit/test_jwt_auth.py tests/api/test_users_api.py -q`
Expected: an ImportError for `decode_access_token`. After a temporary stub, several API tests fail: 201 instead of 422, a 500 or a crash on the deleted-user token, and so on.

- [ ] **Step 4: Replace `app/backend/auth/jwt_auth.py`**

```python
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from users.models import UsersModel

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_SECONDS = 15 * 60
REFRESH_TOKEN_TTL_SECONDS = 24 * 60 * 60
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

security = HTTPBearer()


def _authentication_failed() -> HTTPException:
    # One generic message for every failure so callers can't probe why a token was rejected.
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _generate_token(user_id: int, token_type: str, expire_in: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "type": token_type,
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expire_in),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _decode_token(token: str, expected_type: str) -> int:
    """Validate signature, expiry (PyJWT), token type and user_id; return the user id."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "type", "user_id"]},
        )
    except jwt.PyJWTError:
        raise _authentication_failed() from None
    user_id = payload["user_id"]
    if payload["type"] != expected_type or not isinstance(user_id, int) or isinstance(user_id, bool):
        raise _authentication_failed()
    return user_id


def generate_access_token(user_id: int, expire_in: int = ACCESS_TOKEN_TTL_SECONDS) -> str:
    return _generate_token(user_id, ACCESS_TOKEN_TYPE, expire_in)


def generate_refresh_token(user_id: int, expire_in: int = REFRESH_TOKEN_TTL_SECONDS) -> str:
    return _generate_token(user_id, REFRESH_TOKEN_TYPE, expire_in)


def decode_access_token(token: str) -> int:
    return _decode_token(token, ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> int:
    return _decode_token(token, REFRESH_TOKEN_TYPE)


def find_active_user(db: Session, user_id: int) -> UsersModel:
    user_obj = db.query(UsersModel).filter_by(id=user_id, is_active=True).one_or_none()
    if user_obj is None:
        raise _authentication_failed()
    return user_obj


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UsersModel:
    return find_active_user(db, decode_access_token(credentials.credentials))
```

- [ ] **Step 5: Replace `app/backend/users/schemas.py`**

```python
from pydantic import BaseModel, Field, field_validator

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 250
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class UserLoginSchema(BaseModel):
    username: str = Field(..., max_length=USERNAME_MAX_LENGTH, description="username of the user")
    password: str = Field(..., max_length=PASSWORD_MAX_LENGTH, description="user password")


class UserRegisterSchema(BaseModel):
    username: str = Field(..., max_length=USERNAME_MAX_LENGTH, description="username of the user")
    password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH, description="user password"
    )
    confirm_password: str = Field(..., description="confirm user password")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, username: str) -> str:
        cleaned = username.strip().lower()
        if len(cleaned) < USERNAME_MIN_LENGTH:
            raise ValueError(f"username must be at least {USERNAME_MIN_LENGTH} characters")
        return cleaned

    @field_validator("confirm_password")
    @classmethod
    def check_passwords_match(cls, confirm_password, validation):
        if not confirm_password == validation.data.get("password"):
            raise ValueError("password doesn't match")
        return confirm_password


class UserRefreshTokenSchema(BaseModel):
    token: str = Field(..., description="refresh token of the user")
```

- [ ] **Step 6: Make usernames unique.** In `app/backend/users/models.py`, change the username column to:

```python
    username = Column(String(250), nullable=False, unique=True, index=True)
```

- [ ] **Step 7: Update `app/backend/users/routes.py`.** Change the imports block to:

```python
from auth.jwt_auth import (
    decode_refresh_token,
    find_active_user,
    generate_access_token,
    generate_refresh_token,
)
```

Next, in `user_login`, change the lookup to `filter_by(username=request.username.strip().lower())`. In `user_register`, use `request.username` directly, since the schema already normalises it. Replace both occurrences of `request.username.lower()` there with `request.username`. Finally, replace `user_refresh_token` with:

```python
@router.post("/refresh_token")
async def user_refresh_token(
    request: UserRefreshTokenSchema, db: Session = Depends(get_db)
):
    user_obj = find_active_user(db, decode_refresh_token(request.token))
    access_token = generate_access_token(user_obj.id)
    return JSONResponse(content={"access_token": access_token})
```

- [ ] **Step 8: Run the backend suite**

Run: `cd app/backend && python -m pytest -q`
Expected: all pass, with no `datetime.utcnow` deprecation warnings from `jwt_auth.py`.

- [ ] **Step 9: Docs.** Write two files:
  - `docs/features/backend/auth.md`: use the Backend Module template. Cover the register/login/refresh endpoints (request and response bodies, status codes 201/202/200/401/409/422), the token types and lifetimes (access 15 minutes, refresh 24 hours, HS256, secret from `JWT_SECRET_KEY`), the validation rules (username 3–250 characters, trimmed and lowercased, unique; password 8–128 characters), and the security model (a generic 401 detail, the deleted/inactive-user check on both access and refresh, submitted input never echoed in 422 responses, passwords hashed with bcrypt). Under Future Improvements, list refresh-token rotation/revocation (the `tokens` table is currently written on login but never read) and rate limiting on login.
  - `docs/troubleshooting/backend.md`: one entry per symptom, each as **symptom → cause → fix**. Cover: "401 Authentication failed right after login" (clock skew or a changed `JWT_SECRET_KEY`); "422 on register" (the password/username rules); "Task not found for a task I can see" (it belongs to another user); "tests pick up my real DB" (they can't, because `tests/conftest.py` overrides the env); "`ModuleNotFoundError: backend`" (use flat imports).

- [ ] **Step 10: agentlog.** Append an entry. WHAT: `jwt_auth` rewritten, register validation, unique username, refresh checks that the user exists. WHY: a token for a deleted user returned `None` and later crashed with a 500; the manual expiry check compared naive UTC against local time; error details leaked exception text; there were no password rules; the username uniqueness check could race.

- [ ] **Step 11: Commit**

```bash
git add app/backend docs/features/backend/auth.md docs/troubleshooting/backend.md
git commit -m "fix(auth): strict JWT validation, generic 401s, register rules, unique usernames

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Alembic migrations, health endpoint, backend container

**Files:**
- Create: `app/backend/alembic.ini`, `app/backend/migrations/env.py`, `app/backend/migrations/script.py.mako`, `app/backend/migrations/versions/0001_initial_schema.py`
- Create: `app/backend/health/__init__.py` (empty), `app/backend/health/routes.py`
- Modify: `app/backend/main.py` (include the health router), `Dockerfile.backend`
- Create: `.dockerignore`
- Test: `app/backend/tests/integration/test_migrations.py`, `app/backend/tests/api/test_health_api.py`
- Docs: `docs/runbooks/backend/backend.md`

**Interfaces:**
- Consumes: `Base` from `core.database`; the models in `users.models` and `tasks.models`; `settings.SQLALCHEMY_DATABASE_URL`.
- Produces: `GET /health`, which returns 200 `{"status": "ok"}`, or 503 when the DB is unreachable. Alembic revision id `"0001_initial_schema"`. The backend image runs `alembic upgrade head` and then uvicorn on port 8000, as a non-root user, with a Docker HEALTHCHECK against `/health`.

- [ ] **Step 1: Write the failing tests.** First, `app/backend/tests/integration/test_migrations.py`:

```python
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

import tasks.models  # noqa: F401  (register tables)
import users.models  # noqa: F401
from core.database import Base

BACKEND_DIR = Path(__file__).resolve().parents[2]


def alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_migrations_should_match_orm_models(tmp_path):
    url = f"sqlite:///{tmp_path / 'schema.db'}"
    command.upgrade(alembic_config(url), "head")
    with create_engine(url).connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert differences == []


def test_migrations_should_downgrade_to_empty_schema(tmp_path):
    url = f"sqlite:///{tmp_path / 'schema.db'}"
    config = alembic_config(url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    assert inspect(create_engine(url)).get_table_names() == ["alembic_version"]
```

Then `app/backend/tests/api/test_health_api.py`:

```python
def test_health_should_return_ok_when_database_reachable(anonymous_client):
    response = anonymous_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run to verify failure**

Run: `cd app/backend && python -m pytest tests/integration tests/api/test_health_api.py -q`
Expected: the migrations tests fail because there's no `alembic.ini`, and the health test gets a 404.

- [ ] **Step 3: Create `app/backend/alembic.ini`**

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
# sqlalchemy.url is intentionally empty: env.py reads it from core.config.settings (i.e. .env).
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 4: Create `app/backend/migrations/env.py`**

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import tasks.models  # noqa: F401  (register tables on Base.metadata)
import users.models  # noqa: F401
from core.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

if not config.get_main_option("sqlalchemy.url"):
    from core.config import settings

    # ConfigParser treats "%" as interpolation; URL-encoded passwords contain "%".
    config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URL.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 5: Create `app/backend/migrations/script.py.mako`**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 6: Create `app/backend/migrations/versions/0001_initial_schema.py`**

```python
"""initial schema: users, tokens, tasks (with category)

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

task_category = sa.Enum("university", "finnish", "general", name="task_category")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=250), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_date", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_date", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("created_date", sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False),
        sa.Column("category", task_category, nullable=True),
        sa.Column("created_date", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_date", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_tasks_user_id"), "tasks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_user_id"), table_name="tasks")
    op.drop_table("tasks")
    task_category.drop(op.get_bind(), checkfirst=True)  # Postgres keeps the enum type otherwise
    op.drop_table("tokens")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
```

- [ ] **Step 7: Create `app/backend/health/routes.py`**

```python
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.database import get_db

logger = logging.getLogger("todo.health")

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Liveness + DB connectivity probe used by the Docker healthcheck."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Health check failed: database unreachable")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    return {"status": "ok"}
```

In `app/backend/main.py`, add `from health.routes import router as health_routes` to the imports and `app.include_router(health_routes)` after the other `include_router` calls.

- [ ] **Step 8: Run the backend suite**

Run: `cd app/backend && python -m pytest -q`
Expected: all pass.

If `test_migrations_should_match_orm_models` reports differences, read each one. Fix any genuine mismatch in the migration, never in the test. The single allowed exception is an artefact caused purely by SQLite lacking a native enum type (for example, a type comparison between `VARCHAR(10)` and `Enum`). In that case, leave the test unchanged. Pass `compare_type=False` only inside the test's `MigrationContext.configure(connection, opts={"compare_type": False})`, and add a one-line comment explaining why. Report it as a concern in your summary.

- [ ] **Step 9: Create `.dockerignore`** in the repo root

```
.git
.github
.env
.remember
**/__pycache__
**/*.pyc
**/.pytest_cache
app/backend/tests
app/frontend/tests
app/frontend/storage
postgres
docs
agentlog.md
```

- [ ] **Step 10: Replace `Dockerfile.backend`**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

COPY app/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --uid 1000 --no-create-home --shell /usr/sbin/nologin appuser
COPY --chown=appuser:appuser app/backend .
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

# Apply pending migrations, then serve. `exec` makes uvicorn PID 1 so it receives SIGTERM.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
```

- [ ] **Step 11: Verify the image builds.** The full compose run happens in Task 8.

Run: `cd /mnt/c/Users/SepehrMaadani/Documents/oldProjects/fast_API/todo && docker build -f Dockerfile.backend -t todo-backend:plan-check . 2>&1 | tail -3`
Expected: `naming to docker.io/library/todo-backend:plan-check` (or equivalent) and no errors.

- [ ] **Step 12: Docs.** Write `docs/runbooks/backend/backend.md` using the rules.md **Runbook** template (`## 1. Purpose` through `## 9. Change History`). Cover:
  - How to Run: local tests, and running the API locally with `SQLALCHEMY_DATABASE_URL`/`JWT_SECRET_KEY` exported (`cd app/backend && uvicorn main:app`).
  - Deploy: the container runs `alembic upgrade head` on every start.
  - Health Checks: `/health`, 200 or 503.
  - Monitoring: stdout logs and `docker logs backend`.
  - Debugging: `docker exec backend alembic current` and `alembic history`.
  - Migrations how-to: `alembic revision --autogenerate -m "<msg>"` run inside `app/backend`, then review the generated file and commit it.
  - Disaster Recovery: `pg_dump` and restore commands for the `db` container, and `alembic downgrade -1` for a bad migration.
  - Ownership.
  - Change History, with this task's entry.

- [ ] **Step 13: agentlog.** Append an entry. WHAT: Alembic setup, the initial migration, `/health`, the non-root backend image with HEALTHCHECK, migrate-on-start, `--reload` dropped, `.dockerignore`. WHY: Postgres had **no tables** (nothing ever created the schema); rules.md requires healthchecks and non-root containers; `--reload` was pointless without a source mount and unsafe in production.

- [ ] **Step 14: Commit**

```bash
git add app/backend Dockerfile.backend .dockerignore docs/runbooks/backend/backend.md
git commit -m "feat(backend): alembic migrations, /health, non-root image with healthcheck

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Frontend data layer: config, ApiClient, auth and task services (unit-tested)

**Files:**
- Modify: `app/frontend/requirements.txt`
- Create: `app/frontend/requirements-dev.txt`, `app/frontend/pytest.ini`
- Create: `app/frontend/config.py`, `app/frontend/api/__init__.py` (empty), `app/frontend/api/client.py`
- Create: `app/frontend/features/__init__.py`, `app/frontend/features/auth/__init__.py`, `app/frontend/features/tasks/__init__.py` (all empty)
- Create: `app/frontend/features/auth/validation.py`, `app/frontend/features/auth/service.py`
- Create: `app/frontend/features/tasks/models.py`, `app/frontend/features/tasks/service.py`
- Test: `app/frontend/tests/__init__.py`, `app/frontend/tests/unit/__init__.py` (empty), `tests/unit/test_api_client.py`, `tests/unit/test_auth.py`, `tests/unit/test_task_models.py`, `tests/unit/test_task_service.py`
- Modify: `.github/workflows/CI.yml` (add a `frontend-tests` job)

**Interfaces:**
- Consumes: the HTTP contract from Task 3 (tasks) and Task 4 (auth). The login response is 202 `{"access_token", "refresh_token", "detail"}`. Register returns 201. The error body is `{"error", "status_code", "detail"}`.
- Produces (used by Task 7):
  - `config.load_settings() -> FrontendSettings(api_base_url: str, request_timeout_seconds: float)`
  - `api.client.ApiError(status_code: int, message: str)`, where `.message` is always safe to show to users
  - `api.client.AuthenticationError(ApiError)`
  - `api.client.ApiClient(base_url, timeout, transport=None)` with `.is_authenticated`, `.set_tokens(access, refresh)`, `.clear_tokens()`, `await .request(method, path, *, json=None, params=None, authenticated=True) -> Any`, and `await .close()`
  - `features.auth.validation.validate_login(username, password) -> dict[str, str]` and `validate_registration(username, password, confirm_password) -> dict[str, str]`, where the keys are `"username"`, `"password"` and `"confirm_password"`
  - `features.auth.service.AuthService(client)` with `.is_authenticated`, `.username: str | None`, `await .login(username, password)`, `await .register(username, password, confirm_password)` (which also logs in), and `.logout()`
  - `features.tasks.models`: `CATEGORIES: tuple[str, ...]`, `CATEGORY_LABELS: dict[str, str]`, `TITLE_MAX_LENGTH = 150`, `DESCRIPTION_MAX_LENGTH = 500`, the dataclasses `Task(id, title, description, category, is_completed)` and `CategorySummary(category, total, completed)` (with `.progress: float` and `.label: str`), and `TaskDraft(title, description, category)` (with `.validate() -> dict[str, str]` and `.to_payload() -> dict`)
  - `features.tasks.service.TaskService(client)`: `await list_tasks() -> list[Task]`, `get_task(task_id) -> Task`, `create_task(draft) -> Task`, `update_task(task_id, draft) -> Task`, `set_completed(task_id, completed: bool) -> Task`, `delete_task(task_id) -> None`, `category_summary() -> list[CategorySummary]`

- [ ] **Step 1: Dependencies and test config**

Set `app/frontend/requirements.txt` to:

```
flet[web]==1.0.3
httpx==0.28.1
```

Create `app/frontend/requirements-dev.txt`:

```
httpx==0.28.1
pytest==8.3.5
```

It deliberately doesn't include flet: the unit tests cover code that never imports flet, and CI stays fast.

Create `app/frontend/pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 2: Write the failing ApiClient tests**: `app/frontend/tests/unit/test_api_client.py`

```python
import asyncio
import json

import httpx
import pytest

from api.client import GENERIC_ERROR_MESSAGE, NETWORK_ERROR_MESSAGE, ApiClient, ApiError, AuthenticationError

BASE_URL = "http://api.test"


def make_client(handler) -> ApiClient:
    return ApiClient(BASE_URL, timeout=5, transport=httpx.MockTransport(handler))


def run(coroutine):
    return asyncio.run(coroutine)


def test_request_should_send_bearer_token():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json=[])

    client = make_client(handler)
    client.set_tokens("access-1", "refresh-1")
    assert run(client.request("GET", "/todo/tasks")) == []
    assert seen["auth"] == "Bearer access-1"


def test_request_should_raise_authentication_error_without_token_and_skip_network():
    def handler(request):
        raise AssertionError("no request expected")

    with pytest.raises(AuthenticationError):
        run(make_client(handler).request("GET", "/todo/tasks"))


def test_request_should_refresh_once_and_retry_on_401():
    calls = []

    def handler(request):
        calls.append((request.url.path, request.headers.get("Authorization")))
        if request.url.path == "/users/refresh_token":
            assert json.loads(request.content) == {"token": "refresh-1"}
            return httpx.Response(200, json={"access_token": "access-2"})
        if request.headers["Authorization"] == "Bearer access-1":
            return httpx.Response(401, json={"detail": "Authentication failed"})
        return httpx.Response(200, json={"ok": True})

    client = make_client(handler)
    client.set_tokens("access-1", "refresh-1")
    assert run(client.request("GET", "/todo/tasks")) == {"ok": True}
    assert [path for path, _ in calls] == ["/todo/tasks", "/users/refresh_token", "/todo/tasks"]
    assert calls[-1][1] == "Bearer access-2"


def test_request_should_clear_tokens_when_refresh_fails():
    def handler(request):
        return httpx.Response(401, json={"detail": "Authentication failed"})

    client = make_client(handler)
    client.set_tokens("access-1", "refresh-1")
    with pytest.raises(AuthenticationError) as caught:
        run(client.request("GET", "/todo/tasks"))
    assert client.is_authenticated is False
    assert "log in" in caught.value.message.lower()


def test_request_should_map_network_failure_to_friendly_error():
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    client = make_client(handler)
    client.set_tokens("a", "r")
    with pytest.raises(ApiError) as caught:
        run(client.request("GET", "/todo/tasks"))
    assert caught.value.message == NETWORK_ERROR_MESSAGE
    assert "boom" not in caught.value.message


def test_request_should_hide_server_error_details():
    def handler(request):
        return httpx.Response(500, json={"detail": "psycopg2.OperationalError: secret-host"})

    client = make_client(handler)
    client.set_tokens("a", "r")
    with pytest.raises(ApiError) as caught:
        run(client.request("GET", "/todo/tasks"))
    assert caught.value.message == GENERIC_ERROR_MESSAGE


def test_request_should_surface_backend_detail_for_client_errors():
    def handler(request):
        return httpx.Response(409, json={"error": True, "status_code": 409, "detail": "username already exists"})

    with pytest.raises(ApiError) as caught:
        run(make_client(handler).request("POST", "/users/register", json={}, authenticated=False))
    assert (caught.value.status_code, caught.value.message) == (409, "username already exists")


def test_request_should_use_friendly_message_for_validation_lists():
    def handler(request):
        return httpx.Response(422, json={"detail": [{"loc": ["body", "title"], "msg": "too short"}]})

    client = make_client(handler)
    client.set_tokens("a", "r")
    with pytest.raises(ApiError) as caught:
        run(client.request("POST", "/todo/tasks", json={}))
    assert caught.value.message == "Please check the form and try again."


def test_request_should_say_item_missing_on_404():
    def handler(request):
        return httpx.Response(404, json={"detail": "Task not found"})

    client = make_client(handler)
    client.set_tokens("a", "r")
    with pytest.raises(ApiError) as caught:
        run(client.request("GET", "/todo/tasks/5"))
    assert caught.value.message == "That item no longer exists."


def test_request_should_return_none_for_204():
    client = make_client(lambda request: httpx.Response(204))
    client.set_tokens("a", "r")
    assert run(client.request("DELETE", "/todo/tasks/1")) is None
```

- [ ] **Step 3: Run to verify failure**

Run: `cd app/frontend && python -m pytest tests/unit/test_api_client.py -q`
Expected: `ModuleNotFoundError: No module named 'api'`.

- [ ] **Step 4: Implement `app/frontend/config.py`**

```python
import os
from dataclasses import dataclass

DEFAULT_API_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class FrontendSettings:
    api_base_url: str
    request_timeout_seconds: float


def load_settings() -> FrontendSettings:
    """Read frontend configuration from the environment (see .env.example)."""
    base_url = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("API_BASE_URL must start with http:// or https://")
    timeout = float(os.getenv("API_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    if timeout <= 0:
        raise ValueError("API_TIMEOUT_SECONDS must be positive")
    return FrontendSettings(api_base_url=base_url, request_timeout_seconds=timeout)
```

- [ ] **Step 5: Implement `app/frontend/api/client.py`**

```python
"""HTTP client for the Todo API. One instance per Flet session.

Tokens live only in this object's memory on the Flet server: they never reach the browser.
Every error raised to callers carries a message that is safe to show to users.
"""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = "Something went wrong. Please try again."
NETWORK_ERROR_MESSAGE = "Can't reach the server. Check your connection and try again."
SESSION_EXPIRED_MESSAGE = "Your session has expired. Please log in again."
LOGIN_REQUIRED_MESSAGE = "Please log in to continue."
VALIDATION_MESSAGE = "Please check the form and try again."
NOT_FOUND_MESSAGE = "That item no longer exists."
REFRESH_PATH = "/users/refresh_token"


class ApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class AuthenticationError(ApiError):
    """The session is missing or expired; the user must log in again."""


def _user_message(response: httpx.Response) -> str:
    if response.status_code >= 500:
        return GENERIC_ERROR_MESSAGE
    if response.status_code == 404:
        return NOT_FOUND_MESSAGE
    try:
        detail = response.json().get("detail")
    except (ValueError, AttributeError):
        detail = None
    if isinstance(detail, str) and detail:
        return detail  # backend 4xx string details are written for end users
    if response.status_code == 422:
        return VALIDATION_MESSAGE
    return GENERIC_ERROR_MESSAGE


class ApiClient:
    def __init__(
        self,
        base_url: str,
        timeout: float,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self._http = httpx.AsyncClient(base_url=base_url, timeout=timeout, transport=transport)
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    def set_tokens(self, access_token: str, refresh_token: str) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token

    def clear_tokens(self) -> None:
        self._access_token = None
        self._refresh_token = None

    async def close(self) -> None:
        await self._http.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[dict[str, Any]] = None,
        authenticated: bool = True,
    ) -> Any:
        response = await self._send(method, path, json=json, params=params, authenticated=authenticated)
        if response.status_code == 401 and authenticated and await self._refresh_access_token():
            response = await self._send(method, path, json=json, params=params, authenticated=True)
        return self._parse(response, authenticated)

    async def _send(self, method, path, *, json, params, authenticated) -> httpx.Response:
        headers = {}
        if authenticated:
            if self._access_token is None:
                raise AuthenticationError(401, LOGIN_REQUIRED_MESSAGE)
            headers["Authorization"] = f"Bearer {self._access_token}"
        try:
            return await self._http.request(method, path, json=json, params=params, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning("API request failed: %s %s (%s)", method, path, type(exc).__name__)
            raise ApiError(0, NETWORK_ERROR_MESSAGE) from None

    async def _refresh_access_token(self) -> bool:
        if self._refresh_token is None:
            return False
        try:
            response = await self._http.post(REFRESH_PATH, json={"token": self._refresh_token})
        except httpx.HTTPError as exc:
            logger.warning("Token refresh failed (%s)", type(exc).__name__)
            return False
        if response.status_code != 200:
            self.clear_tokens()
            return False
        self._access_token = response.json()["access_token"]
        return True

    def _parse(self, response: httpx.Response, authenticated: bool) -> Any:
        if response.status_code == 204:
            return None
        if response.is_success:
            return response.json()
        if response.status_code == 401 and authenticated:
            self.clear_tokens()
            raise AuthenticationError(401, SESSION_EXPIRED_MESSAGE)
        logger.info("API returned %s for %s %s", response.status_code, response.request.method, response.request.url.path)
        raise ApiError(response.status_code, _user_message(response))
```

- [ ] **Step 6: Run the ApiClient tests**

Run: `cd app/frontend && python -m pytest tests/unit/test_api_client.py -q`
Expected: `10 passed`.

- [ ] **Step 7: Write the failing auth tests**: `app/frontend/tests/unit/test_auth.py`

```python
import asyncio
import json

import httpx

from api.client import ApiClient
from features.auth.service import AuthService
from features.auth.validation import validate_login, validate_registration


def test_validate_login_should_require_both_fields():
    assert set(validate_login("  ", "")) == {"username", "password"}


def test_validate_login_should_accept_filled_fields():
    assert validate_login("sara", "anything") == {}


def test_validate_registration_should_check_lengths_and_match():
    errors = validate_registration("ab", "short", "other")
    assert set(errors) == {"username", "password", "confirm_password"}


def test_validate_registration_should_accept_valid_input():
    assert validate_registration(" sara ", "secret1234", "secret1234") == {}


def test_login_should_store_tokens_and_username():
    def handler(request):
        assert json.loads(request.content) == {"username": "sara", "password": "secret1234"}
        return httpx.Response(202, json={"access_token": "a", "refresh_token": "r", "detail": "ok"})

    auth = AuthService(ApiClient("http://api.test", 5, transport=httpx.MockTransport(handler)))
    asyncio.run(auth.login(" Sara ", "secret1234"))
    assert auth.is_authenticated and auth.username == "sara"


def test_register_should_log_in_after_creating_account():
    paths = []

    def handler(request):
        paths.append(request.url.path)
        if request.url.path == "/users/register":
            return httpx.Response(201, json={"detail": "User registered successfully"})
        return httpx.Response(202, json={"access_token": "a", "refresh_token": "r"})

    auth = AuthService(ApiClient("http://api.test", 5, transport=httpx.MockTransport(handler)))
    asyncio.run(auth.register("sara", "secret1234", "secret1234"))
    assert paths == ["/users/register", "/users/login"]
    assert auth.is_authenticated


def test_logout_should_forget_session():
    auth = AuthService(ApiClient("http://api.test", 5, transport=httpx.MockTransport(lambda r: httpx.Response(500))))
    auth._client.set_tokens("a", "r")
    auth.logout()
    assert not auth.is_authenticated and auth.username is None
```

- [ ] **Step 8: Implement `app/frontend/features/auth/validation.py`**

```python
"""Client-side checks mirroring the backend rules, so users get instant feedback."""

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 250
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def validate_login(username: str, password: str) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not username.strip():
        errors["username"] = "Enter your username."
    if not password:
        errors["password"] = "Enter your password."
    return errors


def validate_registration(username: str, password: str, confirm_password: str) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not USERNAME_MIN_LENGTH <= len(username.strip()) <= USERNAME_MAX_LENGTH:
        errors["username"] = f"Use {USERNAME_MIN_LENGTH} to {USERNAME_MAX_LENGTH} characters."
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        errors["password"] = f"Use at least {PASSWORD_MIN_LENGTH} characters."
    if confirm_password != password:
        errors["confirm_password"] = "Passwords don't match."
    return errors
```

- [ ] **Step 9: Implement `app/frontend/features/auth/service.py`**

```python
from typing import Optional

from api.client import ApiClient


class AuthService:
    """Login/register/logout for one Flet session."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client
        self._username: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return self._client.is_authenticated

    @property
    def username(self) -> Optional[str]:
        return self._username if self.is_authenticated else None

    async def login(self, username: str, password: str) -> None:
        normalized = username.strip().lower()
        data = await self._client.request(
            "POST",
            "/users/login",
            json={"username": normalized, "password": password},
            authenticated=False,
        )
        self._client.set_tokens(data["access_token"], data["refresh_token"])
        self._username = normalized

    async def register(self, username: str, password: str, confirm_password: str) -> None:
        await self._client.request(
            "POST",
            "/users/register",
            json={"username": username.strip(), "password": password, "confirm_password": confirm_password},
            authenticated=False,
        )
        await self.login(username, password)

    def logout(self) -> None:
        self._client.clear_tokens()
        self._username = None
```

- [ ] **Step 10: Write the failing task model and service tests.** First, `app/frontend/tests/unit/test_task_models.py`:

```python
from features.tasks.models import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH, CategorySummary, Task, TaskDraft


def test_task_from_api_should_map_fields():
    task = Task.from_api({"id": 3, "title": "T", "description": None, "category": "finnish",
                          "is_completed": True, "created_date": "x", "updated_date": "y"})
    assert task == Task(id=3, title="T", description=None, category="finnish", is_completed=True)


def test_draft_validate_should_require_title():
    assert "title" in TaskDraft(title="   ", description="", category=None).validate()


def test_draft_validate_should_limit_lengths():
    errors = TaskDraft(title="x" * (TITLE_MAX_LENGTH + 1), description="d" * (DESCRIPTION_MAX_LENGTH + 1),
                       category=None).validate()
    assert set(errors) == {"title", "description"}


def test_draft_validate_should_reject_unknown_category():
    assert "category" in TaskDraft(title="T", description="", category="cooking").validate()


def test_draft_to_payload_should_trim_and_null_blank_description():
    payload = TaskDraft(title="  Essay ", description="   ", category="university").to_payload()
    assert payload == {"title": "Essay", "description": None, "category": "university"}


def test_summary_progress_should_handle_empty_category():
    assert CategorySummary(category="finnish", total=0, completed=0).progress == 0.0
    assert CategorySummary(category="finnish", total=4, completed=1).progress == 0.25
    assert CategorySummary(category="finnish", total=4, completed=1).label == "Finnish"
```

Then `app/frontend/tests/unit/test_task_service.py`:

```python
import asyncio
import json

import httpx

from api.client import ApiClient
from features.tasks.models import TaskDraft
from features.tasks.service import TaskService

TASK_JSON = {"id": 1, "title": "Essay", "description": None, "category": "university",
             "is_completed": False, "created_date": "2026-09-30T10:00:00", "updated_date": "2026-09-30T10:00:00"}


def service_with(handler) -> TaskService:
    client = ApiClient("http://api.test", 5, transport=httpx.MockTransport(handler))
    client.set_tokens("a", "r")
    return TaskService(client)


def test_list_tasks_should_request_max_page_and_map_tasks():
    def handler(request):
        assert request.url.path == "/todo/tasks" and request.url.params["limit"] == "100"
        return httpx.Response(200, json=[TASK_JSON])

    tasks = asyncio.run(service_with(handler).list_tasks())
    assert [t.title for t in tasks] == ["Essay"]


def test_create_task_should_post_draft_payload():
    def handler(request):
        assert request.method == "POST"
        assert json.loads(request.content) == {"title": "Essay", "description": None, "category": "university"}
        return httpx.Response(201, json=TASK_JSON)

    task = asyncio.run(service_with(handler).create_task(TaskDraft("Essay", "", "university")))
    assert task.id == 1


def test_update_task_should_patch_draft_payload():
    def handler(request):
        assert (request.method, request.url.path) == ("PATCH", "/todo/tasks/1")
        return httpx.Response(200, json=TASK_JSON)

    asyncio.run(service_with(handler).update_task(1, TaskDraft("Essay", "", None)))


def test_set_completed_should_patch_only_completion():
    def handler(request):
        assert json.loads(request.content) == {"is_completed": False}
        return httpx.Response(200, json=TASK_JSON)

    asyncio.run(service_with(handler).set_completed(1, False))


def test_delete_task_should_send_delete():
    def handler(request):
        assert (request.method, request.url.path) == ("DELETE", "/todo/tasks/1")
        return httpx.Response(204)

    assert asyncio.run(service_with(handler).delete_task(1)) is None


def test_category_summary_should_map_rows():
    def handler(request):
        assert request.url.path == "/todo/tasks/summary"
        return httpx.Response(200, json=[{"category": "finnish", "total": 2, "completed": 1}])

    [summary] = asyncio.run(service_with(handler).category_summary())
    assert (summary.category, summary.progress) == ("finnish", 0.5)
```

- [ ] **Step 11: Implement `app/frontend/features/tasks/models.py`**

```python
"""Frontend view of tasks. Mirrors the backend contract; no flet imports here."""

from dataclasses import dataclass
from typing import Any, Mapping, Optional

TITLE_MAX_LENGTH = 150
DESCRIPTION_MAX_LENGTH = 500
CATEGORIES: tuple[str, ...] = ("university", "finnish", "general")
CATEGORY_LABELS: dict[str, str] = {"university": "University", "finnish": "Finnish", "general": "general"}


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    is_completed: bool

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "Task":
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            description=data.get("description"),
            category=data.get("category"),
            is_completed=bool(data["is_completed"]),
        )


@dataclass(frozen=True)
class CategorySummary:
    category: str
    total: int
    completed: int

    @property
    def progress(self) -> float:
        return self.completed / self.total if self.total else 0.0

    @property
    def label(self) -> str:
        return CATEGORY_LABELS.get(self.category, self.category.title())

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "CategorySummary":
        return cls(category=str(data["category"]), total=int(data["total"]), completed=int(data["completed"]))


@dataclass(frozen=True)
class TaskDraft:
    """What the task form collects; validated before it is sent."""

    title: str
    description: str
    category: Optional[str]

    def validate(self) -> dict[str, str]:
        errors: dict[str, str] = {}
        title = self.title.strip()
        if not title:
            errors["title"] = "Give your task a title."
        elif len(title) > TITLE_MAX_LENGTH:
            errors["title"] = f"Keep the title under {TITLE_MAX_LENGTH} characters."
        if len(self.description.strip()) > DESCRIPTION_MAX_LENGTH:
            errors["description"] = f"Keep the description under {DESCRIPTION_MAX_LENGTH} characters."
        if self.category is not None and self.category not in CATEGORIES:
            errors["category"] = "Choose a category from the list."
        return errors

    def to_payload(self) -> dict[str, Any]:
        return {
            "title": self.title.strip(),
            "description": self.description.strip() or None,
            "category": self.category,
        }
```

- [ ] **Step 12: Implement `app/frontend/features/tasks/service.py`**

```python
from api.client import ApiClient
from features.tasks.models import CategorySummary, Task, TaskDraft

TASKS_PATH = "/todo/tasks"
PAGE_SIZE = 100  # backend maximum; one page is plenty for a personal todo list


class TaskService:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def list_tasks(self) -> list[Task]:
        rows = await self._client.request("GET", TASKS_PATH, params={"limit": PAGE_SIZE})
        return [Task.from_api(row) for row in rows]

    async def get_task(self, task_id: int) -> Task:
        return Task.from_api(await self._client.request("GET", f"{TASKS_PATH}/{task_id}"))

    async def create_task(self, draft: TaskDraft) -> Task:
        return Task.from_api(await self._client.request("POST", TASKS_PATH, json=draft.to_payload()))

    async def update_task(self, task_id: int, draft: TaskDraft) -> Task:
        return Task.from_api(await self._client.request("PATCH", f"{TASKS_PATH}/{task_id}", json=draft.to_payload()))

    async def set_completed(self, task_id: int, completed: bool) -> Task:
        data = await self._client.request("PATCH", f"{TASKS_PATH}/{task_id}", json={"is_completed": completed})
        return Task.from_api(data)

    async def delete_task(self, task_id: int) -> None:
        await self._client.request("DELETE", f"{TASKS_PATH}/{task_id}")

    async def category_summary(self) -> list[CategorySummary]:
        rows = await self._client.request("GET", f"{TASKS_PATH}/summary")
        return [CategorySummary.from_api(row) for row in rows]
```

- [ ] **Step 13: Run all frontend tests**

Run: `cd app/frontend && python -m pytest -q`
Expected: `29 passed` (10 client, 7 auth, 6 model and 6 service tests).

- [ ] **Step 14: Add the CI job.** Append this job to `.github/workflows/CI.yml` under `jobs:`:

```yaml
  frontend-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    defaults:
      run:
        working-directory: app/frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: app/frontend/requirements-dev.txt
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run tests
        run: python -m pytest --disable-warnings -v
```

- [ ] **Step 15: agentlog.** Append an entry. WHAT: the frontend data layer (`config.py`, `ApiClient`, `AuthService`, `TaskService`, models and validation) with unit tests, plus the CI job. WHY: the UI was entirely mock data. This layer is the only place that talks HTTP. It keeps JWTs server-side in memory to satisfy the rules.md "no tokens in browser storage" rule, and it converts every failure into a user-safe message. Docs for this layer are written in Task 7 together with the UI flows.

- [ ] **Step 16: Commit**

```bash
git add app/frontend .github/workflows/CI.yml
git commit -m "feat(frontend): API client with token refresh, auth and task services

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Frontend UI: login/register, home with real data, task form, router

**Files:**
- Create: `app/frontend/shared/__init__.py` (empty), `app/frontend/shared/theme.py`, `app/frontend/shared/ui.py`
- Create: `app/frontend/features/auth/views.py`, `app/frontend/features/tasks/home_view.py`, `app/frontend/features/tasks/form_view.py`, `app/frontend/router.py`
- Rewrite: `app/frontend/main.py`
- Delete: `app/frontend/custom_checkbox.py`, `app/frontend/mock.py`
- Docs: `docs/features/frontend/auth.md`, `docs/features/frontend/tasks.md`, `docs/architecture/frontend-architecture.md`, `docs/runbooks/frontend/frontend.md`, `docs/troubleshooting/frontend.md`

**Interfaces:**
- Consumes: everything Task 6 produces.
- Produces these routes: `/login`, `/register`, `/` (home), `/tasks/new`, `/tasks/<id>`. Unknown routes redirect to `/`. Signed-out users are redirected to `/login`, and signed-in users on `/login` or `/register` go to `/`.

**Verification note:** the flet views can't be unit-tested reliably. A fake flet session doesn't mount controls, which was found in-session. Verification here is a build smoke check (Step 9) plus the end-to-end check in Task 8.

- [ ] **Step 1: Create `app/frontend/shared/theme.py`**

```python
"""Design tokens for the app (colors and sizes). Change the look here, not in views."""

BG = "#FF7ED4"      # outer page and cards
FG = "#6420AA"      # main panel
PINK = "#FF3EA5"    # accents, progress, primary actions
TEXT = "white"
MUTED = "white70"
TRACK = "white12"

CATEGORY_COLORS = {"university": "#F26B0F", "finnish": "#FCC737", "general": "#E73879"}
UNCATEGORIZED_COLOR = "#7E1891"

PANEL_WIDTH = 400
PANEL_HEIGHT = 850
DRAWER_PANEL_WIDTH = 120
AVATAR_IMAGE = "images/ghand.jpg"
```

- [ ] **Step 2: Create `app/frontend/shared/ui.py`**

```python
"""Small UI helpers shared by all features."""

import flet as ft

from api.client import ApiError, AuthenticationError

LOGIN_ROUTE = "/login"


def navigate(page: ft.Page, route: str) -> None:
    """Navigate from any handler (sync or async) without blocking it."""
    page.run_task(page.push_route, route)


def show_message(page: ft.Page, message: str) -> None:
    page.show_dialog(ft.SnackBar(content=ft.Text(message), show_close_icon=True))


def report_error(page: ft.Page, error: ApiError) -> None:
    """Show a user-safe message; send the user to login if their session ended."""
    show_message(page, error.message)
    if isinstance(error, AuthenticationError):
        navigate(page, LOGIN_ROUTE)
```

- [ ] **Step 3: Create `app/frontend/features/auth/views.py`**

```python
import flet as ft

from api.client import ApiError
from features.auth.service import AuthService
from features.auth.validation import USERNAME_MAX_LENGTH, validate_login, validate_registration
from shared import theme
from shared.ui import navigate, show_message


def _auth_view(route: str, heading: str, subheading: str, controls: list[ft.Control]) -> ft.View:
    card = ft.Container(
        width=360,
        padding=24,
        border_radius=24,
        bgcolor=theme.BG,
        content=ft.Column(
            tight=True,
            spacing=16,
            controls=[
                ft.Text(heading, size=28, weight=ft.FontWeight.W_700, color=theme.TEXT),
                ft.Text(subheading, color=theme.MUTED),
                *controls,
            ],
        ),
    )
    return ft.View(
        route=route,
        bgcolor=theme.FG,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[card],
    )


def _username_field() -> ft.TextField:
    return ft.TextField(label="Username", autofocus=True, max_length=USERNAME_MAX_LENGTH)


def _password_field(label: str = "Password") -> ft.TextField:
    return ft.TextField(label=label, password=True, can_reveal_password=True)


def build_login_view(page: ft.Page, auth: AuthService) -> ft.View:
    username = _username_field()
    password = _password_field()
    submit = ft.Button(content="Log in", icon=ft.Icons.LOGIN)

    async def log_in(_=None) -> None:
        errors = validate_login(username.value or "", password.value or "")
        username.error = errors.get("username")
        password.error = errors.get("password")
        if errors:
            page.update()
            return
        submit.disabled = True
        page.update()
        try:
            await auth.login(username.value, password.value)
        except ApiError as exc:
            submit.disabled = False
            page.update()
            show_message(page, exc.message)
            return
        await page.push_route("/")

    submit.on_click = log_in
    password.on_submit = log_in
    return _auth_view(
        "/login",
        "Welcome back",
        "Log in to see your tasks.",
        [
            username,
            password,
            submit,
            ft.TextButton(content="New here? Create an account", on_click=lambda _: navigate(page, "/register")),
        ],
    )


def build_register_view(page: ft.Page, auth: AuthService) -> ft.View:
    username = _username_field()
    password = _password_field()
    confirm = _password_field("Confirm password")
    submit = ft.Button(content="Create account", icon=ft.Icons.PERSON_ADD)

    async def register(_=None) -> None:
        errors = validate_registration(username.value or "", password.value or "", confirm.value or "")
        username.error = errors.get("username")
        password.error = errors.get("password")
        confirm.error = errors.get("confirm_password")
        if errors:
            page.update()
            return
        submit.disabled = True
        page.update()
        try:
            await auth.register(username.value, password.value, confirm.value)
        except ApiError as exc:
            submit.disabled = False
            page.update()
            show_message(page, exc.message)
            return
        await page.push_route("/")

    submit.on_click = register
    confirm.on_submit = register
    return _auth_view(
        "/register",
        "Create your account",
        "It takes ten seconds.",
        [
            username,
            password,
            confirm,
            submit,
            ft.TextButton(content="Already have an account? Log in", on_click=lambda _: navigate(page, "/login")),
        ],
    )
```

- [ ] **Step 4: Create `app/frontend/features/tasks/form_view.py`**

```python
from typing import Optional

import flet as ft

from api.client import ApiError
from features.tasks.models import CATEGORIES, CATEGORY_LABELS, DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH, Task, TaskDraft
from features.tasks.service import TaskService
from shared import theme
from shared.ui import navigate, report_error, show_message

NO_CATEGORY = "none"


def build_task_form_view(page: ft.Page, tasks: TaskService, task: Optional[Task]) -> ft.View:
    """Create (task=None) or edit an existing task."""
    is_edit = task is not None
    title = ft.TextField(
        label="Title", value=task.title if task else "", max_length=TITLE_MAX_LENGTH, autofocus=True
    )
    description = ft.TextField(
        label="Description (optional)",
        value=(task.description or "") if task else "",
        multiline=True,
        min_lines=3,
        max_lines=6,
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    category = ft.Dropdown(
        label="Category",
        value=(task.category if task and task.category else NO_CATEGORY),
        options=[ft.dropdown.Option(key=NO_CATEGORY, text="No category")]
        + [ft.dropdown.Option(key=key, text=CATEGORY_LABELS[key]) for key in CATEGORIES],
    )
    save = ft.Button(content="Save changes" if is_edit else "Add task", icon=ft.Icons.CHECK)

    def read_draft() -> TaskDraft:
        chosen = None if category.value in (None, NO_CATEGORY) else category.value
        return TaskDraft(title=title.value or "", description=description.value or "", category=chosen)

    async def submit(_=None) -> None:
        draft = read_draft()
        errors = draft.validate()
        title.error = errors.get("title")
        description.error = errors.get("description")
        category.error_text = errors.get("category")
        if errors:
            page.update()
            return
        save.disabled = True
        page.update()
        try:
            if task is None:
                await tasks.create_task(draft)
            else:
                await tasks.update_task(task.id, draft)
        except ApiError as exc:
            save.disabled = False
            page.update()
            report_error(page, exc)
            return
        show_message(page, "Task saved." if is_edit else "Task added.")
        await page.push_route("/")

    async def delete_confirmed(_=None) -> None:
        page.pop_dialog()
        try:
            await tasks.delete_task(task.id)
        except ApiError as exc:
            report_error(page, exc)
            return
        show_message(page, "Task deleted.")
        await page.push_route("/")

    def confirm_delete(_=None) -> None:
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Delete this task?"),
                content=ft.Text("This can't be undone."),
                actions=[
                    ft.TextButton(content="Cancel", on_click=lambda _: page.pop_dialog()),
                    ft.TextButton(content="Delete", on_click=delete_confirmed),
                ],
            )
        )

    save.on_click = submit
    title.on_submit = submit
    actions: list[ft.Control] = [save]
    if is_edit:
        actions.append(ft.OutlinedButton(content="Delete", icon=ft.Icons.DELETE_OUTLINE, on_click=confirm_delete))

    header = ft.Row(
        controls=[
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT, tooltip="Back to tasks",
                          on_click=lambda _: navigate(page, "/")),
            ft.Text("Edit task" if is_edit else "New task", size=24, weight=ft.FontWeight.W_700, color=theme.TEXT),
        ]
    )
    return ft.View(
        route=f"/tasks/{task.id}" if is_edit else "/tasks/new",
        bgcolor=theme.FG,
        padding=20,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                width=theme.PANEL_WIDTH,
                content=ft.Column(spacing=16, controls=[header, title, description, category, ft.Row(actions)]),
            )
        ],
    )
```

- [ ] **Step 5: Create `app/frontend/features/tasks/home_view.py`**

```python
from typing import Optional

import flet as ft

from api.client import ApiError, AuthenticationError
from features.auth.service import AuthService
from features.tasks.models import CategorySummary, Task
from features.tasks.service import TaskService
from shared import theme
from shared.ui import navigate, report_error

EMPTY_ALL = "No tasks yet. Tap + to add your first one."
EMPTY_FILTERED = "No tasks in this category yet."


class HomeView:
    """Main screen: slide-out profile drawer, category cards with progress, and the task list."""

    def __init__(self, page: ft.Page, auth: AuthService, tasks: TaskService) -> None:
        self._page = page
        self._auth = auth
        self._tasks = tasks
        self._all_tasks: list[Task] = []
        self._summaries: list[CategorySummary] = []
        self._selected_category: Optional[str] = None
        self._load_error: Optional[str] = None
        self._categories_row = ft.Row(scroll=ft.ScrollMode.AUTO)
        self._task_list = ft.Column(height=400, spacing=10, scroll=ft.ScrollMode.AUTO)
        self._main_panel = self._build_main_panel()

    async def build(self) -> ft.View:
        """Load data, then return the view. AuthenticationError propagates to the router."""
        await self._load()
        self._render()
        return ft.View(route="/", padding=0, bgcolor=theme.BG, controls=[self._build_layout()])

    # ---- data -------------------------------------------------------------------------

    async def _load(self) -> None:
        try:
            self._all_tasks = await self._tasks.list_tasks()
            self._summaries = await self._tasks.category_summary()
            self._load_error = None
        except AuthenticationError:
            raise
        except ApiError as exc:
            self._load_error = exc.message

    async def _reload(self, _=None) -> None:
        try:
            await self._load()
        except AuthenticationError as exc:
            report_error(self._page, exc)
            return
        self._render()
        self._page.update()

    # ---- rendering --------------------------------------------------------------------

    def _render(self) -> None:
        self._categories_row.controls = [self._category_card(summary) for summary in self._summaries]
        if self._load_error:
            self._task_list.controls = [
                ft.Text(self._load_error, color=theme.TEXT),
                ft.Button(content="Try again", icon=ft.Icons.REFRESH, on_click=self._reload),
            ]
            return
        visible = [t for t in self._all_tasks if self._selected_category in (None, t.category)]
        if visible:
            self._task_list.controls = [self._task_row(task) for task in visible]
        else:
            empty = EMPTY_FILTERED if self._selected_category else EMPTY_ALL
            self._task_list.controls = [ft.Text(empty, color=theme.MUTED)]

    def _category_card(self, summary: CategorySummary) -> ft.Control:
        selected = summary.category == self._selected_category

        def toggle_filter(_=None) -> None:
            self._selected_category = None if selected else summary.category
            self._render()
            self._page.update()

        return ft.Container(
            border_radius=20,
            bgcolor=theme.BG,
            border=ft.Border.all(2, theme.TEXT) if selected else None,
            width=170,
            height=110,
            padding=15,
            ink=True,
            tooltip=f"Show only {summary.label} tasks" if not selected else "Show all tasks",
            on_click=toggle_filter,
            content=ft.Column(
                controls=[
                    ft.Text(f"{summary.total} tasks", color=theme.MUTED),
                    ft.Text(summary.label, size=18, weight=ft.FontWeight.W_600, color=theme.TEXT),
                    ft.ProgressBar(value=summary.progress, color=theme.PINK, bgcolor=theme.TRACK,
                                   bar_height=5, border_radius=20),
                ]
            ),
        )

    def _task_row(self, task: Task) -> ft.Control:
        accent = theme.CATEGORY_COLORS.get(task.category or "", theme.UNCATEGORIZED_COLOR)
        checkbox = ft.Checkbox(
            value=task.is_completed,
            shape=ft.CircleBorder(),
            active_color=theme.PINK,
            check_color=theme.TEXT,
            border_side=ft.BorderSide(2, accent),
            tooltip="Mark as not done" if task.is_completed else "Mark as done",
            semantics_label=f"{task.title}, {'done' if task.is_completed else 'not done'}",
        )

        async def toggle_done(_=None) -> None:
            try:
                await self._tasks.set_completed(task.id, bool(checkbox.value))
            except ApiError as exc:
                checkbox.value = task.is_completed
                self._page.update()
                report_error(self._page, exc)
                return
            await self._reload()

        def open_editor(_=None) -> None:
            navigate(self._page, f"/tasks/{task.id}")

        checkbox.on_change = toggle_done
        return ft.Container(
            height=70,
            width=theme.PANEL_WIDTH,
            bgcolor=theme.BG,
            border_radius=25,
            padding=ft.Padding.only(left=12, right=4),
            content=ft.Row(
                controls=[
                    checkbox,
                    ft.Container(
                        expand=True,
                        on_click=open_editor,
                        content=ft.Text(
                            task.title,
                            size=17,
                            weight=ft.FontWeight.W_300,
                            color=theme.MUTED if task.is_completed else theme.TEXT,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ),
                    ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, icon_color=theme.TEXT, tooltip="Edit task",
                                  on_click=open_editor),
                ]
            ),
        )

    # ---- layout -----------------------------------------------------------------------

    def _build_layout(self) -> ft.Control:
        return ft.Container(
            width=theme.PANEL_WIDTH,
            height=theme.PANEL_HEIGHT,
            bgcolor=theme.BG,
            border_radius=35,
            content=ft.Stack(
                controls=[
                    self._build_profile_panel(),
                    ft.Row(alignment=ft.MainAxisAlignment.END, controls=[self._main_panel]),
                ]
            ),
        )

    def _build_main_panel(self) -> ft.Container:
        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.IconButton(icon=ft.Icons.MENU, icon_color=theme.TEXT, tooltip="Open menu",
                              on_click=self._open_drawer),
                ft.IconButton(icon=ft.Icons.REFRESH, icon_color=theme.TEXT, tooltip="Refresh",
                              on_click=self._reload),
            ],
        )
        return ft.Container(
            width=theme.PANEL_WIDTH,
            height=theme.PANEL_HEIGHT,
            bgcolor=theme.FG,
            border_radius=35,
            animate=ft.Animation(600, ft.AnimationCurve.DECELERATE),
            animate_scale=ft.Animation(400, ft.AnimationCurve.DECELERATE),
            padding=ft.Padding.only(top=50, left=20, right=20, bottom=5),
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(height=20),
                    ft.Text(f"What's up, {self._auth.username}!", size=30, weight=ft.FontWeight.W_700,
                            color=theme.TEXT),
                    ft.Text("CATEGORIES", color=theme.MUTED),
                    ft.Container(padding=ft.Padding.only(top=10, bottom=20), content=self._categories_row),
                    ft.Text("TASKS", color=theme.MUTED),
                    ft.Stack(
                        controls=[
                            self._task_list,
                            ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=theme.PINK, tooltip="Add task",
                                                    bottom=2, right=20,
                                                    on_click=lambda _: navigate(self._page, "/tasks/new")),
                        ]
                    ),
                ]
            ),
        )

    def _build_profile_panel(self) -> ft.Control:
        def log_out(_=None) -> None:
            self._auth.logout()
            navigate(self._page, "/login")

        return ft.Container(
            width=theme.PANEL_WIDTH,
            height=theme.PANEL_HEIGHT,
            bgcolor=theme.BG,
            border_radius=35,
            padding=ft.Padding.only(left=40, top=60, right=200),
            content=ft.Column(
                spacing=16,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT, tooltip="Close menu",
                                  on_click=self._close_drawer),
                    ft.CircleAvatar(foreground_image_src=theme.AVATAR_IMAGE, radius=45),
                    ft.Text(self._auth.username or "", size=24, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.TextButton(content="Log out", icon=ft.Icons.LOGOUT, on_click=log_out),
                ],
            ),
        )

    def _open_drawer(self, _=None) -> None:
        self._main_panel.width = theme.DRAWER_PANEL_WIDTH
        self._main_panel.scale = ft.Scale(0.8, alignment=ft.Alignment.CENTER_RIGHT)
        self._main_panel.border_radius = ft.BorderRadius.only(top_left=35, bottom_left=35)
        self._main_panel.update()

    def _close_drawer(self, _=None) -> None:
        self._main_panel.width = theme.PANEL_WIDTH
        self._main_panel.scale = ft.Scale(1, alignment=ft.Alignment.CENTER_RIGHT)
        self._main_panel.border_radius = 35
        self._main_panel.update()
```

- [ ] **Step 6: Create `app/frontend/router.py`**

```python
import re
from typing import Optional

import flet as ft

from api.client import ApiError, AuthenticationError
from features.auth.service import AuthService
from features.auth.views import build_login_view, build_register_view
from features.tasks.form_view import build_task_form_view
from features.tasks.home_view import HomeView
from features.tasks.service import TaskService
from shared.ui import show_message

HOME_ROUTE = "/"
LOGIN_ROUTE = "/login"
REGISTER_ROUTE = "/register"
NEW_TASK_ROUTE = "/tasks/new"
PUBLIC_ROUTES = frozenset({LOGIN_ROUTE, REGISTER_ROUTE})
EDIT_TASK_ROUTE = re.compile(r"^/tasks/(?P<task_id>[1-9][0-9]{0,9})$")


class Router:
    """Maps page.route to a view and enforces the signed-in guard."""

    def __init__(self, page: ft.Page, auth: AuthService, tasks: TaskService) -> None:
        self._page = page
        self._auth = auth
        self._tasks = tasks

    async def handle_route_change(self, _event: Optional[ft.RouteChangeEvent] = None) -> None:
        route = self._page.route or HOME_ROUTE
        redirect = self._guard(route)
        if redirect:
            await self._page.push_route(redirect)
            return
        try:
            view = await self._build_view(route)
        except AuthenticationError as exc:
            self._auth.logout()
            show_message(self._page, exc.message)
            await self._page.push_route(LOGIN_ROUTE)
            return
        if view is None:
            await self._page.push_route(HOME_ROUTE)
            return
        self._page.views.clear()
        self._page.views.append(view)
        self._page.update()

    def _guard(self, route: str) -> Optional[str]:
        if route not in PUBLIC_ROUTES and not self._auth.is_authenticated:
            return LOGIN_ROUTE
        if route in PUBLIC_ROUTES and self._auth.is_authenticated:
            return HOME_ROUTE
        return None

    async def _build_view(self, route: str) -> Optional[ft.View]:
        """Return the view for `route`, or None to send the user home."""
        if route == LOGIN_ROUTE:
            return build_login_view(self._page, self._auth)
        if route == REGISTER_ROUTE:
            return build_register_view(self._page, self._auth)
        if route == NEW_TASK_ROUTE:
            return build_task_form_view(self._page, self._tasks, task=None)
        match = EDIT_TASK_ROUTE.match(route)
        if match:
            return await self._build_edit_view(int(match["task_id"]))
        if route == HOME_ROUTE:
            return await HomeView(self._page, self._auth, self._tasks).build()
        return None

    async def _build_edit_view(self, task_id: int) -> Optional[ft.View]:
        try:
            task = await self._tasks.get_task(task_id)
        except AuthenticationError:
            raise
        except ApiError as exc:
            show_message(self._page, exc.message)
            return None
        return build_task_form_view(self._page, self._tasks, task=task)
```

- [ ] **Step 7: Rewrite `app/frontend/main.py`**

```python
import logging

import flet as ft

from api.client import ApiClient
from config import load_settings
from features.auth.service import AuthService
from features.tasks.service import TaskService
from router import Router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def main(page: ft.Page) -> None:
    """One call per browser session: each session gets its own ApiClient (and tokens)."""
    settings = load_settings()
    client = ApiClient(settings.api_base_url, settings.request_timeout_seconds)
    router = Router(page, AuthService(client), TaskService(client))

    async def close_client(_=None) -> None:
        await client.close()

    page.title = "Todo"
    page.window.width = 420
    page.window.height = 870
    page.on_close = close_client
    page.on_route_change = router.handle_route_change
    await router.handle_route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets", view=ft.AppView.WEB_BROWSER)
```

- [ ] **Step 8: Delete the replaced files**

```bash
cd /mnt/c/Users/SepehrMaadani/Documents/oldProjects/fast_API/todo
git rm -q app/frontend/custom_checkbox.py app/frontend/mock.py
```

- [ ] **Step 9: Build smoke check.** Every module imports, and every view builds its control tree under flet 1.0.3. Build a throwaway venv that has flet, in the controller's scratchpad; don't use the project venv. `SCRATCH` is the session scratchpad path that the controller gives you.

```bash
python3 -m venv "$SCRATCH/fv" && "$SCRATCH/fv/bin/pip" install -q "flet[web]==1.0.3" "httpx==0.28.1"
cd app/frontend && "$SCRATCH/fv/bin/python" - <<'EOF'
import asyncio, flet as ft
from flet.messaging.session import Session
from flet.messaging.connection import Connection
from flet.pubsub.pubsub_hub import PubSubHub
from api.client import ApiClient
from features.auth.service import AuthService
from features.auth.views import build_login_view, build_register_view
from features.tasks.form_view import build_task_form_view
from features.tasks.models import Task
from features.tasks.service import TaskService
import main, router  # noqa: F401  (import check; ft.run is guarded by __main__)

class FakeConn(Connection):
    def __init__(self):
        super().__init__(); self.pubsubhub = PubSubHub()
    def send_message(self, message): pass

async def go():
    session = Session(FakeConn()); page = session.page
    auth = AuthService(ApiClient("http://x", 1)); tasks = TaskService(ApiClient("http://x", 1))
    for view in (build_login_view(page, auth), build_register_view(page, auth),
                 build_task_form_view(page, tasks, None),
                 build_task_form_view(page, tasks, Task(1, "T", None, "finnish", True))):
        page.views.clear(); page.views.append(view); page.update()
    print("views build ok")
asyncio.run(go())
EOF
```

Expected: `views build ok` with no traceback. A `HomeView` needs a live API, so it's verified in Task 8.

- [ ] **Step 10: Run the frontend unit tests again**

Run: `cd app/frontend && python -m pytest -q`
Expected: `29 passed`.

- [ ] **Step 11: Docs.** Use the rules.md templates exactly.
  - `docs/features/frontend/auth.md` (Frontend Feature template, 11 sections). UI/UX flow: login → home; register → auto-login → home; the logout path; redirect rules. Data flow: view → `AuthService` → `ApiClient` → `/users/*`. Validation on both client (`validation.py`) and server. Security: tokens only in server-side session memory, one `ApiClient` per session, generic messages. Edge cases: wrong password, duplicate username, backend down, session expiry.
  - `docs/features/frontend/tasks.md` (Frontend Feature template). The home view with category cards (filter toggle), the list (incomplete first), the checkbox toggle (optimistic revert on error), and edit via row or pencil. The form's create and edit modes, with delete confirmation. State logic (`HomeView` fields, `_reload` after mutations). Edge cases: empty states, a foreign or missing id (message, then home), network errors. Testing: unit tests for models and service, plus the manual E2E checklist from Task 8.
  - `docs/architecture/frontend-architecture.md`. The folder map (`api/`, `features/<f>/{service,views,models,validation}`, `shared/`, `config.py`, `router.py`, `main.py`). The dependency rules: views → services → `ApiClient`; `shared` never imports `features`; no HTTP outside `api/`. How rules.md's React/Next structure was adapted to Flet (server-side Python UI). The session model (the Flet server calls the API over the Docker network, so the browser never talks to the API). The flet 1.0 API notes from Global Constraints.
  - `docs/runbooks/frontend/frontend.md` (Runbook template). Local run: `API_BASE_URL=http://localhost:8000 python main.py` from `app/frontend` with flet installed. Env vars: `API_BASE_URL`, `API_TIMEOUT_SECONDS`, `FLET_*`. Health: HTTP 200 on `:3000/`. Logs: `docker logs frontend`.
  - `docs/troubleshooting/frontend.md`. Each entry as symptom → cause → fix: "Can't reach the server" (wrong `API_BASE_URL` or backend unhealthy); `ImportError ... from 'flet'` (0.x API names, see the Global Constraints list); "stuck on login after restart" (tokens are in memory by design, so log in again); a blank page on `:3000` (check `FLET_SERVER_IP=0.0.0.0`).

- [ ] **Step 12: agentlog.** Append an entry. WHAT: the login/register views, `HomeView` backed by the API (real categories, counts, progress, filter, toggle, edit and add), the task form (create, edit, delete with confirmation), the router with its auth guard, `main.py` reduced to bootstrap, and `CustomCheckBox` replaced by an accessible `ft.Checkbox`. WHY: the user asked for fully functional task features stored in the DB; the old UI used hardcoded mock data. `ft.Checkbox` supports keyboard and semantics, as rules.md requires.

- [ ] **Step 13: Commit**

```bash
git add -A app/frontend docs/features/frontend docs/architecture/frontend-architecture.md docs/runbooks/frontend docs/troubleshooting/frontend.md
git commit -m "feat(frontend): login/register, API-backed home, task create/edit/delete

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Compose, env files, frontend container, end-to-end verification, system docs

**Files:**
- Modify: `docker-compose.yml` (full replacement), `Dockerfile.frontend`, `README.md`
- Create: `.env.example`
- Controller only: update the local `.env` (remove `DATABASE_URL`, add `CORS_ORIGINS` and `API_BASE_URL`)
- Docs: `docs/features/infra/docker-compose.md`, `docs/architecture/infra-architecture.md`, `docs/architecture/system-overview.md`, `docs/runbooks/infra/docker-compose.md`, `docs/troubleshooting/infra.md`, and an update to `docs/onboarding/dev-setup.md`

**Interfaces:**
- Consumes: the backend image behaviour from Task 5 (migrations on start, `/health`) and the frontend `API_BASE_URL` from Task 6.
- Produces: `docker compose up -d --build` brings up `db`, `backend` and `frontend`, all healthy. The UI is at `http://localhost:3000`. The API and Postgres are bound to `127.0.0.1` only.

- [ ] **Step 1: Create `.env.example`**

```dotenv
# ---- PostgreSQL (db container) ----
POSTGRES_USER=todo
POSTGRES_PASSWORD=change-me
POSTGRES_DB=todo

# ---- Backend ----
# SQLAlchemy URL. Host "db" is the compose service name. URL-encode special characters in the password.
SQLALCHEMY_DATABASE_URL=postgresql://todo:change-me@db:5432/todo
# Secret for signing JWTs. Generate one with:
#   python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY=change-me
# JSON list of browser origins allowed by CORS. The Flet UI calls the API server-side, so [] is fine.
CORS_ORIGINS=[]

# ---- Frontend ----
# Where the Flet server reaches the API (compose service name inside Docker).
API_BASE_URL=http://backend:8000
```

- [ ] **Step 2: Controller updates the local `.env`.** Never print it.

```bash
cd /mnt/c/Users/SepehrMaadani/Documents/oldProjects/fast_API/todo
sed -i '/^DATABASE_URL=/d' .env
grep -q '^CORS_ORIGINS=' .env || echo 'CORS_ORIGINS=[]' >> .env
grep -q '^API_BASE_URL=' .env || echo 'API_BASE_URL=http://backend:8000' >> .env
sed 's/=.*/=<set>/' .env   # show keys only
```

Expected keys: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `SQLALCHEMY_DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `API_BASE_URL`.

- [ ] **Step 3: Replace `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:15-alpine
    container_name: db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:?set POSTGRES_USER in .env}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}
      POSTGRES_DB: ${POSTGRES_DB:?set POSTGRES_DB in .env}
    ports:
      - "127.0.0.1:5432:5432"   # local tooling only; never exposed on the LAN
    volumes:
      - postgres_data:/var/lib/postgresql/data:rw
    networks:
      - internal_net
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \"$${POSTGRES_USER}\" -d \"$${POSTGRES_DB}\""]
      interval: 10s
      timeout: 5s
      start_period: 30s
      retries: 5

  # smtp4dev: #  just for testing mail server
  #   image: rnwood/smtp4dev:v3
  #   restart: always
  #   ports:
  #     - '5000:80'
  #     - '2525:25'
  #     - '143:143'
  #   volumes:
  #       - smtp4dev-data:/smtp4dev

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: backend
    restart: unless-stopped
    environment:
      SQLALCHEMY_DATABASE_URL: ${SQLALCHEMY_DATABASE_URL:?set SQLALCHEMY_DATABASE_URL in .env}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:?set JWT_SECRET_KEY in .env}
      CORS_ORIGINS: ${CORS_ORIGINS:-[]}
    ports:
      - "127.0.0.1:8000:8000"   # Swagger for local development; the UI talks to it internally
    depends_on:
      db:
        condition: service_healthy
    networks:
      - internal_net
      - public_net
    security_opt:
      - no-new-privileges:true

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: frontend
    restart: unless-stopped
    environment:
      API_BASE_URL: ${API_BASE_URL:-http://backend:8000}
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - public_net
    security_opt:
      - no-new-privileges:true

networks:
  internal_net:
    driver: bridge
    internal: true   # db has no route outside this network
  public_net:
    driver: bridge

volumes:
  postgres_data:
```

- [ ] **Step 4: Replace `Dockerfile.frontend`**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLET_FORCE_WEB_SERVER=true \
    FLET_SERVER_PORT=3000 \
    FLET_SERVER_IP=0.0.0.0

WORKDIR /app

COPY app/frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --uid 1000 --no-create-home --shell /usr/sbin/nologin appuser
COPY --chown=appuser:appuser app/frontend .
USER appuser

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:3000/', timeout=4).status == 200 else 1)"

CMD ["python", "main.py"]
```

- [ ] **Step 5: Validate the compose file and bring the stack up**

```bash
cd /mnt/c/Users/SepehrMaadani/Documents/oldProjects/fast_API/todo
docker compose config --quiet && echo "compose ok"
docker compose up -d --build 2>&1 | tail -5
```

Then wait until all three services report healthy, polling with a 3-minute cap:

```bash
for i in $(seq 1 36); do s=$(docker compose ps --format '{{.Name}}={{.Health}}' | tr '\n' ' '); echo "$s"; case "$s" in *starting*|*unhealthy*) sleep 5;; *) break;; esac; done
```

Expected: `backend=healthy db=healthy frontend=healthy`. If anything is unhealthy, run `docker compose logs <service> --tail 50` and fix it before continuing.

- [ ] **Step 6: Verify the schema and API end to end.** Run this from the host; it uses only the Python stdlib.

```bash
docker exec backend alembic current   # expected: 0001_initial_schema (head)
python3 - <<'EOF'
import json, urllib.request, uuid
BASE = "http://127.0.0.1:8000"
def call(method, path, body=None, token=None, expect=200):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req) as r: status, data = r.status, r.read()
    except urllib.error.HTTPError as e: status, data = e.code, e.read()
    assert status == expect, (method, path, status, data)
    return json.loads(data) if data else None
user = f"e2e{uuid.uuid4().hex[:8]}"
call("GET", "/health")
call("POST", "/users/register", {"username": user, "password": "secret1234", "confirm_password": "secret1234"}, expect=201)
tok = call("POST", "/users/login", {"username": user, "password": "secret1234"}, expect=202)["access_token"]
t = call("POST", "/todo/tasks", {"title": "E2E task", "category": "finnish"}, tok, expect=201)
call("PATCH", f"/todo/tasks/{t['id']}", {"is_completed": True}, tok)
assert call("GET", "/todo/tasks/summary", token=tok)[1] == {"category": "finnish", "total": 1, "completed": 1}
call("PATCH", f"/todo/tasks/{t['id']}", {"is_completed": False}, tok)
assert call("GET", f"/todo/tasks/{t['id']}", token=tok)["is_completed"] is False
print("API e2e ok; task id", t["id"], "user", user)
EOF
```

Expected: `API e2e ok`.

- [ ] **Step 7: Verify persistence across restarts**

```bash
docker compose restart backend db && sleep 20
docker exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "select count(*) from tasks where title = '"'"'E2E task'"'"'"'
```

Expected: `1`. The task created in Step 6 survived the restart.

- [ ] **Step 8: Verify the containers run as non-root**

```bash
docker exec backend id -u; docker exec frontend id -u
```

Expected: `1000` twice.

- [ ] **Step 9: Browser check.** The controller asks the user to run this if no browser automation is available. Open `http://localhost:3000` and go through the list below. Every item must work.
  1. You're redirected to the login screen. Choose "Create an account" and register `demo` / `secret1234`. You land on home and see "What's up, demo!".
  2. Home shows three category cards, each with 0 tasks, and the text "No tasks yet. Tap + to add your first one."
  3. Tap +, enter a title, pick Finnish, and choose Add task. You see "Task added.", the task appears, and the Finnish card shows 1 task.
  4. Tick the checkbox: the Finnish progress bar fills. Untick it: the bar empties. Reload the page: you're asked to log in again (tokens live in memory by design). Log in, and the state has persisted.
  5. Tap the task, change the title, clear the category, and save. The list updates.
  6. Tap the task, choose Delete, then confirm Delete. The task is gone and "Task deleted." shows.
  7. Tap a category card: the list filters. Tap it again: all tasks show.
  8. Menu, then Log out: you're back on the login screen.
  9. Run `docker compose stop backend`, then tap Refresh on home. You see "Can't reach the server…" and no crash. Run `docker compose start backend`, then Try again.

- [ ] **Step 10: Docs**
  - `docs/features/infra/docker-compose.md` (Infra template, 9 sections). The services, the networks (`internal_net` is internal-only; the db is never on `public_net`), the volume, and the inputs table listing every `.env` variable with its purpose. Security rules: non-root users, `no-new-privileges`, localhost-bound ports, secrets only via `.env`. Deployment steps, rollback (redeploy the previous image or tag; `alembic downgrade -1`), and monitoring (healthchecks, `docker compose ps`).
  - `docs/architecture/infra-architecture.md`. A container diagram (ASCII) showing browser → `frontend:3000` → `backend:8000` → `db:5432`, with the networks marked, and the reasoning for each hardening choice.
  - `docs/architecture/system-overview.md`. A one-page overview: the components, the request flow for "tick a task" from the browser to Postgres and back, where auth happens, where the config comes from, and links to every other doc.
  - `docs/runbooks/infra/docker-compose.md` (Runbook template). Covers `up`/`down`/`logs`/`ps`, rotating `JWT_SECRET_KEY` (all users get logged out), and backup and restore with `pg_dump`/`psql` into `postgres_data`.
  - `docs/troubleshooting/infra.md`. Entries: `set X in .env` errors (copy `.env.example`); a service stuck in `starting` (check its logs); the backend is unhealthy because of the DB URL (the host must be `db` and special characters must be URL-encoded); a port already in use.
  - Update `docs/onboarding/dev-setup.md` with `## First Run` (`cp .env.example .env`, edit the secrets, `docker compose up -d --build`, open `http://localhost:3000`) and `## Running Frontend Tests`.
  - `README.md`: fix the stack description (PostgreSQL rather than SQLite, and the Flet web UI), add Quick start (the three commands) and a link to `docs/architecture/system-overview.md`. Leave the other sections unchanged.

- [ ] **Step 11: agentlog.** Append an entry. WHAT: compose hardening (explicit per-service env, localhost-bound DB and API, internal network, `no-new-privileges`, frontend waits for a healthy backend), the non-root frontend image with HEALTHCHECK, `.env.example`, the `.env` cleanup (duplicate `DATABASE_URL` removed; `CORS_ORIGINS` and `API_BASE_URL` added), and the system docs. WHY: the user asked for env-driven configuration; rules.md infra rules call for least privilege, healthchecks and strict networking; and the earlier `env_file: .env` gave every container every secret.

- [ ] **Step 12: Commit**

```bash
git add docker-compose.yml Dockerfile.frontend .env.example README.md docs
git status --short | grep -F '.env' | grep -v '.env.example' && echo "STOP: .env staged" || true
git commit -m "feat(infra): hardened compose with healthchecks, env-driven config, system docs

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review (done while writing)

- **Spec coverage:**
  - Decision 1 → Tasks 2–4.
  - Decision 2 → Tasks 6–7.
  - Decision 3 → Tasks 2, 3 and 7.
  - Decision 4 → Task 5.
  - Decision 5 → Tasks 1 and 8.
  - Decision 6: register, login and logout (Tasks 4, 6, 7); list, filter, create, edit, complete and delete (Tasks 3, 6, 7); persistence (Task 8, Step 7).
  - rules.md: agentlog is in every task; the docs tree is spread across Tasks 1, 3, 4, 5, 7 and 8; non-root images, healthchecks and strict networks are in Tasks 5 and 8; the no-browser-token rule is in Task 6.
- **Placeholder scan:** code steps contain full code. Doc steps list the required sections and facts rather than prose, which is deliberate: the prose follows the rules.md templates.
- **Type consistency:**
  - `TaskService.update_task(user_id, task_id, changes)` (backend) and `TaskService.update_task(task_id, draft)` (frontend) are different classes in different apps, and both are intentional.
  - The frontend `CategorySummary.label` and `.progress` are used in `home_view`.
  - `report_error` and `navigate`/`show_message` come from `shared.ui`.
  - `find_active_user` is defined in Task 4 and used by `users/routes.py`.
- **Review Focus:** all six items have pinning tests or verification steps, listed above.
