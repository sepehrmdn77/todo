# System Overview

## Components
- **frontend**: Flet web UI (`app/frontend`). Holds JWTs in server memory only, never in the browser.
- **backend**: FastAPI (`app/backend`) with users, auth and tasks modules, SQLAlchemy and Alembic.
- **db**: PostgreSQL 15 with the `postgres_data` volume.
- **compose**: wires them together with healthchecks and two networks.

## Request flow: ticking a task
1. The user clicks the checkbox in the browser; the Flet client sends the event over its websocket to the frontend server.
2. The frontend `TaskService` calls `PATCH http://backend:8000/todo/tasks/{id}` with `{"is_completed": true}` and the `Authorization: Bearer` access token held in memory (the client refreshes the token once on a 401).
3. The backend validates the JWT (auth happens here, in a dependency on every `/todo` route), loads the task scoped to the user id, updates it and commits to Postgres.
4. The response returns through the same path, and the frontend refreshes the list and progress bars and pushes the new UI state to the browser.

## Where auth happens
Login and registration are backend endpoints (`/users/login`, `/users/register`). Token validation is in the backend only; the frontend just stores and forwards tokens server-side.

## Where config comes from
Everything comes from the root `.env` (template: `.env.example`), passed per service by `docker-compose.yml`. See the [compose feature doc](../features/infra/docker-compose.md).

## Documentation map
- Architecture: [backend](backend-architecture.md), [frontend](frontend-architecture.md), [infra](infra-architecture.md)
- Features: [backend auth](../features/backend/auth.md), [backend tasks](../features/backend/tasks.md), [frontend auth](../features/frontend/auth.md), [frontend tasks](../features/frontend/tasks.md), [infra compose](../features/infra/docker-compose.md)
- Runbooks: [backend](../runbooks/backend/backend.md), [frontend](../runbooks/frontend/frontend.md), [infra](../runbooks/infra/docker-compose.md)
- Troubleshooting: [backend](../troubleshooting/backend.md), [frontend](../troubleshooting/frontend.md), [infra](../troubleshooting/infra.md)
- Onboarding: [dev setup](../onboarding/dev-setup.md)
