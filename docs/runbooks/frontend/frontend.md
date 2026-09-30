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

### On an iPhone/iPad with the Flet iOS app (dev only, same Wi-Fi)
1. Start the dev service (profile `ios`, target `ios` in `Dockerfile.frontend`; runs `flet run --ios` with hot reload on port 8551):
   ```bash
   docker compose --profile ios up -d --build frontend-ios
   ```
2. Find the host's LAN IP (Windows: `ipconfig` → Wi-Fi IPv4, e.g. `192.168.1.50`).
3. **Docker Engine inside WSL2 (NAT networking) only:** the phone cannot reach WSL directly. In an *admin* PowerShell on Windows, forward the port and open the firewall (re-run the `portproxy` line after a reboot, the WSL IP changes; get it with `wsl hostname -I`):
   ```powershell
   netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8551 connectaddress=<WSL-IP> connectport=8551
   New-NetFirewallRule -DisplayName "Flet iOS dev 8551" -Direction Inbound -Protocol TCP -LocalPort 8551 -Action Allow -Profile Private
   ```
   Docker Desktop publishes ports on the Windows host already; skip this step there.
4. In the **Flet** app (App Store), add/open the URL `http://<LAN-IP>:8551/app/main.py`, or scan a QR code of `flet://flet-host/<URL-encoded that URL>` with the iPhone Camera.
   The QR code printed in `docker logs frontend-ios` contains the *container* IP (172.x) and does not work from a phone.
5. Stop it when done: `docker compose --profile ios stop frontend-ios`. Remove the forwarding with `netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8551`.

## 3. How to Deploy
Through docker compose (see the compose runbook/Task 8). The container must set `FLET_SERVER_IP=0.0.0.0` and `API_BASE_URL` to the backend service address on the Docker network.

## 4. Health Checks
HTTP 200 on `:3000/`. The dev `frontend-ios` service: HTTP 200 on `:8551/app/main.py` (Docker HEALTHCHECK).

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
- 2026-09-30: Added the dev-only `frontend-ios` service (`flet run --ios`, port 8551) for testing in the Flet iOS app on the LAN.
