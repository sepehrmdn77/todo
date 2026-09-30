# Docker Compose Stack

## 1. Purpose
Runs the whole todo app locally with one command: PostgreSQL (`db`), the FastAPI API (`backend`) and the Flet web UI (`frontend`). Configuration comes only from `.env`, and each service gets only the variables it needs.

## 2. Architecture
- **db**: `postgres:15-alpine`, data in the named volume `postgres_data`. Attached only to `internal_net`. Published on `127.0.0.1:5432` for local tooling.
- **backend**: built from `Dockerfile.backend`. Runs Alembic migrations on start, then serves on port 8000 (published on `127.0.0.1:8000`). Attached to `internal_net` (to reach db) and `public_net` (to be reached by the frontend). Waits for a healthy db.
- **frontend**: built from `Dockerfile.frontend`. Flet web server on port 3000 (published on all interfaces). Attached only to `public_net`. Waits for a healthy backend. Calls the API server-side at `API_BASE_URL`.
- **Networks**: `internal_net` and `public_net` are separate bridge networks. The db is isolated by network membership (it is never on `public_net`, so the frontend cannot reach it) and by its localhost-only port binding. `internal_net` is deliberately not `internal: true`, because Docker does not publish ports for containers that sit only on an internal network. As a consequence the db container has outbound internet egress.
- **Volume**: `postgres_data` holds the database files and survives `docker compose down`.

See [infra architecture](../../architecture/infra-architecture.md).

## 3. Inputs (Variables)
All variables live in the root `.env` (copy from `.env.example`).

| Variable | Used by | Purpose |
|---|---|---|
| `POSTGRES_USER` | db | Database superuser name |
| `POSTGRES_PASSWORD` | db | Database password |
| `POSTGRES_DB` | db | Database name created on first start |
| `SQLALCHEMY_DATABASE_URL` | backend | Connection URL. Host must be `db`. URL-encode special characters in the password |
| `JWT_SECRET_KEY` | backend | Secret used to sign access and refresh tokens |
| `CORS_ORIGINS` | backend | JSON list of allowed browser origins (default `[]`) |
| `API_BASE_URL` | frontend | Where the Flet server reaches the API (default `http://backend:8000`) |

Values containing `$` must be single-quoted in `.env`, otherwise compose tries to interpolate them.

## 4. Outputs
- UI: `http://localhost:3000`
- API and Swagger: `http://127.0.0.1:8000` (`/health`, `/docs`)
- Postgres: `127.0.0.1:5432`
- Healthy status for all three services in `docker compose ps`

## 5. Security Rules
- Backend and frontend containers run as non-root (uid 1000).
- Every service sets `no-new-privileges:true`.
- The db and API ports are bound to `127.0.0.1` only.
- Secrets exist only in `.env` (never committed) and are passed per service, not through a blanket `env_file`.
- Required variables fail fast with `set X in .env` messages.
- `docker compose config` prints resolved secrets; use `--quiet` when validating.

## 6. Deployment Steps
1. `cp .env.example .env` and set real secrets.
2. `docker compose config --quiet`
3. `docker compose up -d --build`
4. Wait for `docker compose ps` to show all services healthy.
5. Open `http://localhost:3000`.

## 7. Rollback
- Redeploy the previous image or git tag: `git checkout <tag> && docker compose up -d --build`.
- Schema: `docker exec backend alembic downgrade -1` before rolling back to code that predates the migration.
- Never run `docker compose down -v` unless you intend to delete all data.

## 8. Monitoring & Alerts
- Healthchecks: db via `pg_isready`, backend via `/health`, frontend via HTTP GET on `/`.
- `docker compose ps` shows the health state; `docker compose logs <service> --tail 50` shows details.
- No external alerting is configured yet.

## 9. Change History
- 2026-09-30: hardened compose (per-service env, localhost ports, separate networks, `no-new-privileges`, healthchecks), non-root frontend image, `.env.example`.
