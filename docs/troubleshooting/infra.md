# Infra Troubleshooting

## `set X in .env` error on `docker compose up`
- Symptom: compose stops with `set POSTGRES_PASSWORD in .env` (or similar).
- Cause: the variable is missing from `.env`.
- Fix: `cp .env.example .env` and fill in every value.

## A service is stuck in `starting`
- Symptom: `docker compose ps` shows `starting` for a long time, or dependants never start.
- Cause: the healthcheck is failing.
- Fix: `docker compose logs <service> --tail 50`. The backend waits for db, and the frontend waits for the backend.

## Backend unhealthy because of the DB URL
- Symptom: backend logs show connection or authentication errors.
- Cause: the host in `SQLALCHEMY_DATABASE_URL` is not `db`, the credentials do not match `POSTGRES_*`, or special characters in the password are not URL-encoded.
- Fix: use `postgresql://USER:PASSWORD@db:5432/DBNAME` and percent-encode special characters. Note that the db only applies `POSTGRES_PASSWORD` when the volume is first created.

## Register or login returns 500 (bcrypt)
- Symptom: backend logs show `ValueError: password cannot be longer than 72 bytes` from `passlib/handlers/bcrypt.py`.
- Cause: bcrypt 5.x is incompatible with passlib 1.7.4.
- Fix: keep `passlib[bcrypt]==1.7.4` and `bcrypt==4.0.1` pinned in `app/backend/requirements.txt`, then `docker compose up -d --build backend`.

## Compose warns `The "xyz" variable is not set`
- Symptom: a warning naming a fragment of a secret.
- Cause: a `$` inside a `.env` value is treated as variable interpolation.
- Fix: single-quote the value in `.env` (for example `JWT_SECRET_KEY='abc$def'`), or write `$$`. Then recreate the affected service.

## Port already in use
- Symptom: `bind: address already in use` for 3000, 8000 or 5432.
- Cause: another process (often a local Postgres or an old container) owns the port.
- Fix: stop that process or container, or change the host side of the `ports` mapping in `docker-compose.yml`.
