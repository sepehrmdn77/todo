# Runbook — Frontend (Flet)

## 1. Purpose
The Flet web UI for the todo app, served on port 3000. It calls the backend API server-side; the browser never talks to the API.

## 2. How to Run
Tests (no flet needed):
```bash
cd app/frontend
python -m pytest -q
```
Local run with flet installed (`pip install "flet[web]==1.0.3" httpx==0.28.1`):
```bash
cd app/frontend
API_BASE_URL=http://localhost:8000 python main.py
```
Environment variables: `API_BASE_URL` (backend base URL), `API_TIMEOUT_SECONDS` (request timeout), and the `FLET_*` server settings (for example `FLET_SERVER_IP`, `FLET_SERVER_PORT`).

## 3. How to Deploy
Through docker compose (see the compose runbook/Task 8). The container must set `FLET_SERVER_IP=0.0.0.0` and `API_BASE_URL` to the backend service address on the Docker network.

## 4. Health Checks
HTTP 200 on `:3000/`.

## 5. Monitoring
Logs go to stdout: `docker logs frontend`. Passwords, tokens and request bodies are never logged.

## 6. Debugging
See `docs/troubleshooting/frontend.md`. Quick checks: backend `/health`, the `API_BASE_URL` value inside the container, and browser console for blank pages.

## 7. Disaster Recovery
The frontend is stateless (tokens are in session memory). Restart or redeploy the container; users log in again. Data lives in PostgreSQL behind the backend.

## 8. Ownership
Owner: repository maintainer (sepehrmdn77).

## 9. Change History
- 2026-09-30: Initial runbook with API-backed UI, router and auth guard.
