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

The root `.env` is created from `.env.example`, which arrives in Task 8 of the full-stack wiring plan. Never commit `.env`.

## Running Backend Tests

```bash
cd app/backend && python -m pytest -q
```

- Tests set their own environment in `tests/conftest.py`, so no database or secrets are needed.
- Layout: `tests/unit` (no DB or network), `tests/api` (FastAPI client with an in-memory SQLite DB per test), `tests/integration`.

## Import Convention

Imports are flat from `app/backend` and `app/frontend`, for example `from tasks.services import TaskService` or `from api.client import ApiClient`. Never write `from backend.x import ...`. The apps run with their own directory as the root (in containers, in `pytest.ini` via `pythonpath = .`, and in CI via `working-directory`), so mixing `backend.*` prefixes with flat imports only works through PYTHONPATH tricks.
