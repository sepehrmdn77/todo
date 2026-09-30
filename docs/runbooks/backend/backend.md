# Runbook — Backend (FastAPI + Alembic)

## 1. Purpose

The FastAPI backend serves the todo API (auth, tasks) on port 8000 and owns the PostgreSQL schema through Alembic migrations. The schema is created only by migrations (revision `0001_initial_schema`); nothing else creates tables.

## 2. How to Run

Tests (SQLite, no external services):

```bash
cd app/backend
python -m pytest -q
```

Run the API locally against a database:

```bash
export SQLALCHEMY_DATABASE_URL="postgresql://<user>:<password>@localhost:5432/<db>"
export JWT_SECRET_KEY="<random secret>"
cd app/backend
alembic upgrade head
uvicorn main:app
```

Creating a new migration after changing ORM models (run inside `app/backend`):

```bash
alembic revision --autogenerate -m "<message>"
```

Review the generated file in `migrations/versions/` (autogenerate misses some changes, such as enum edits and server defaults), run `python -m pytest tests/integration -q`, then commit the file.

## 3. How to Deploy

Build the image from the repo root: `docker build -f Dockerfile.backend -t todo-backend .`

The container runs as the non-root user `appuser` and executes `alembic upgrade head` on every start, then uvicorn on port 8000 (`exec`, so uvicorn is PID 1 and receives SIGTERM). If the migration fails, the container exits and the API does not start.

## 4. Health Checks

`GET /health` returns `200 {"status": "ok"}` when the database answers `SELECT 1`, and `503` when it is unreachable. The image has a Docker `HEALTHCHECK` that calls it every 15 s (30 s start period, 3 retries). Check state with `docker inspect --format '{{.State.Health.Status}}' backend`.

## 5. Monitoring

The service logs to stdout/stderr only: `docker logs -f backend`. Passwords, tokens and request bodies are never logged. A failing health check logs `Health check failed: database unreachable` with the exception.

## 6. Debugging

- Current revision: `docker exec backend alembic current`
- Revision history: `docker exec backend alembic history`
- Container will not start: read `docker logs backend`; a migration error appears before uvicorn starts.
- Health is 503: check that the `db` container is healthy and that `SQLALCHEMY_DATABASE_URL` points at it.

## 7. Disaster Recovery

Backup the database (`db` container):

```bash
docker exec db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup.sql
```

Restore into an empty database:

```bash
docker exec -i db psql -U "$POSTGRES_USER" "$POSTGRES_DB" < backup.sql
```

Bad migration: roll back one revision with `docker exec backend alembic downgrade -1`, then deploy a fixed revision. Note that the container re-applies `upgrade head` on restart, so ship the fix (or an image without the bad revision) before restarting.

## 8. Ownership

Owner: Sepehr Maadani (sepehrmaadani98@gmail.com).

## 9. Change History

- 2026-09-30: Added Alembic (`0001_initial_schema`), `/health`, non-root backend image with HEALTHCHECK and migrate-on-start, dropped `--reload`, added `.dockerignore`.
