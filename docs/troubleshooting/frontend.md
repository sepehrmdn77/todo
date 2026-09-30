# Frontend Troubleshooting

## "Can't reach the server"
- Symptom: snackbar says the server can't be reached on login or when loading tasks.
- Cause: `API_BASE_URL` is wrong for where the frontend runs, or the backend is unhealthy.
- Fix: check `API_BASE_URL` (inside Docker use the backend service name, not `localhost`) and `GET /health` on the backend; `docker logs backend`.

## `ImportError ... from 'flet'`
- Symptom: import fails for a name such as `ElevatedButton`.
- Cause: code written for flet 0.x; this project pins flet 1.0.3.
- Fix: use the 1.0 names (`ft.Button(content=...)`, `ft.Icons`, `ft.Padding.only`, ...). See the Flet 1.0 notes in `docs/architecture/frontend-architecture.md`.

## Stuck on login after restart
- Symptom: after a restart or reload you are asked to log in again.
- Cause: tokens are kept in server-side session memory by design.
- Fix: log in again.

## Blank page on :3000
- Symptom: browser shows nothing.
- Cause: the Flet server is bound to localhost inside the container.
- Fix: set `FLET_SERVER_IP=0.0.0.0` and check `docker logs frontend`.
