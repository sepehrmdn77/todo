# Runbook — Docker Compose Stack

## 1. Purpose
Operate the local stack (`db`, `backend`, `frontend`): start, stop, inspect, rotate the JWT secret, and back up or restore the database.

## 2. How to Run
```bash
cp .env.example .env          # first time only, then edit the secrets
docker compose up -d --build  # start
docker compose ps             # status and health
docker compose logs backend --tail 50
docker compose down           # stop and remove containers (keeps postgres_data)
```
Never use `docker compose down -v` unless you want to delete the database.

## 3. How to Deploy
1. `git pull`
2. `docker compose config --quiet`
3. `docker compose up -d --build` (the backend runs Alembic migrations on start)
4. Confirm `docker compose ps` shows all services healthy.

## 4. Health Checks
- `docker compose ps` shows `healthy` for all three services.
- `curl http://127.0.0.1:8000/health`
- `docker exec backend alembic current` shows `0001_initial_schema (head)` or later.

## 5. Monitoring
Health state and logs via `docker compose ps` and `docker compose logs -f <service>`. No external monitoring yet.

## 6. Debugging
- Service stuck in `starting`: read its logs. See [infra troubleshooting](../../troubleshooting/infra.md).
- Open a SQL shell: `docker exec -it db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'`
- Rotate `JWT_SECRET_KEY`: generate a new value with `python -c "import secrets; print(secrets.token_urlsafe(64))"`, put it in `.env` (single-quote it if it contains `$`), then `docker compose up -d backend`. All existing tokens become invalid, so every user is logged out.

## 7. Disaster Recovery
Backup (`--clean --if-exists` makes the dump drop existing objects first, so it restores into an already-migrated database):
```bash
docker exec db sh -c 'pg_dump --clean --if-exists -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
```
Restore into a running db. Stop the backend first so nothing writes during the restore:
```bash
docker compose stop backend
docker exec -i db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backup.sql
docker compose start backend
```
Store backups outside the repo; they contain user data and password hashes.

## 8. Ownership
Project maintainer (sepehrmdn77).

## 9. Change History
- 2026-09-30: initial runbook.
