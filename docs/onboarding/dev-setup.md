# Developer Setup

## Prerequisites

- Python 3.12
- Docker and Docker Compose

## Repository Layout

- `app/backend`: FastAPI backend (tasks, users, auth, pages, core)
- `app/frontend`: Flet frontend
- `docs`: runbooks, features, architecture and onboarding documents
- `Dockerfile.backend` / `Dockerfile.frontend`: container images for each app
- `docker-compose.yml`: local stack (backend, frontend, PostgreSQL)

## Configuration

The root `.env` is created from `.env.example`. Never commit `.env`.

## First Run

```bash
cp .env.example .env            # then edit the secrets (single-quote values containing $)
docker compose up -d --build
```

Open `http://localhost:3000`. The API is at `http://127.0.0.1:8000/docs`. See `docs/runbooks/infra/docker-compose.md` for day-to-day operation.

## Running Backend Tests

```bash
cd app/backend && python -m pytest -q
```

- Tests set their own environment in `tests/conftest.py`, so no database or secrets are needed.
- Layout: `tests/unit` (no DB or network), `tests/api` (FastAPI client with an in-memory SQLite DB per test), `tests/integration`.

## Running Frontend Tests

```bash
cd app/frontend && python -m pytest -q
```

- Needs `httpx==0.28.1` and `pytest==8.3.5`. Do not install `flet` into the backend test venv.
- Unit tests use no network.

## Import Convention

Imports are flat from `app/backend` and `app/frontend`, for example `from tasks.services import TaskService` or `from api.client import ApiClient`. Never write `from backend.x import ...`. The apps run with their own directory as the root (in containers, in `pytest.ini` via `pythonpath = .`, and in CI via `working-directory`), so mixing `backend.*` prefixes with flat imports only works through PYTHONPATH tricks.
