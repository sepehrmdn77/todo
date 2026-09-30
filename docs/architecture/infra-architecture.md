# Infra Architecture

## Container diagram

```
  Browser
     |  http://localhost:3000
     v
+-------------------+        public_net        +-------------------+
| frontend :3000    | -----------------------> | backend :8000     |
| Flet web, uid 1000|   API_BASE_URL           | FastAPI, uid 1000 |
+-------------------+   http://backend:8000    +---------+---------+
                                                         |
                                     internal_net        | postgresql://db:5432
                                                         v
                                               +-------------------+
                                               | db :5432          |
                                               | postgres:15       |
                                               +---------+---------+
                                                         |
                                                  volume postgres_data

 backend is on public_net + internal_net; db only on internal_net; frontend only on public_net.
 Host ports: 3000 (all interfaces), 127.0.0.1:8000, 127.0.0.1:5432.
```

## Reasoning
- **Two networks**: the frontend can reach the backend but never the db. The db is reachable only by services on `internal_net` (the backend) and from the host loopback. `internal: true` is not used, because Docker then cannot publish the db port to the host.
- **Localhost-bound ports**: the API and Postgres are for local tooling only and must not be exposed on the LAN. Only the UI is public.
- **Per-service environment**: a blanket `env_file` gave every container every secret. Now the frontend never sees the DB password or JWT secret.
- **Non-root and `no-new-privileges`**: limits the impact of a container compromise.
- **Healthchecks and `depends_on: service_healthy`**: the start order is db, backend (runs migrations), frontend, so nothing starts against a missing dependency.
- **Named volume**: data survives container recreation.
