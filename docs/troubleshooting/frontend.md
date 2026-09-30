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

## Flet iOS app can't connect to `frontend-ios`
- Symptom: the Flet app spins or reports it can't reach `http://<LAN-IP>:8551/app/main.py`.
- Cause: the phone isn't on the same network, the QR code from `docker logs frontend-ios` was used (it has the container's 172.x IP), or Docker runs inside WSL2 with NAT networking so port 8551 isn't reachable from the LAN.
- Fix: use the host's LAN IP; on WSL2 add the `netsh interface portproxy` rule and firewall rule from `docs/runbooks/frontend/frontend.md` (re-run the portproxy after reboot, the WSL IP changes); check `curl http://<LAN-IP>:8551/app/main.py` from another machine.

## `PermissionError: '/app/.flet'` in `frontend-ios`
- Cause: `flet run` writes its storage under `/app/.flet` but runs as the non-root `appuser`.
- Fix: the `ios` stage creates `/app/.flet` owned by `appuser`; rebuild with `docker compose --profile ios up -d --build frontend-ios`.
