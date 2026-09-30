# Backend Architecture

## Module layout
```
app/backend/
  main.py            app factory, routers, error handlers
  core/              config.py (settings), database.py (engine, Base, get_db)
  auth/              JWT helpers, get_authenticated_user
  users/             users module (legacy layout, unchanged)
  pages/             server-rendered pages
  tasks/
    entities.py      domain: Task, TaskCategory, CategorySummary, errors
    ports.py         TaskRepository protocol
    services.py      TaskService use cases
    adapters.py      SqlAlchemyTaskRepository
    models.py        SQLAlchemy TaskModel
    schemas.py       HTTP DTOs
    dependencies.py  composition root (get_task_service)
    routes.py        thin FastAPI routes
  tests/unit|api|integration
```

## Lich layering applied to `tasks`
```
routes -> dependencies -> services -> ports <- adapters -> models
   \            \             \          \         \          /
    +------------+-------------+----------+---------+--------+
                              entities
                  (used by every layer, imports nothing)
```
- Routes translate HTTP to service calls and back; no business logic.
- Dependencies wire the concrete adapter into the service.
- Services hold use cases and depend only on entities and the port.
- Adapters implement the port using models; the domain never sees SQLAlchemy.

## Scope: why `users` and `auth` were not restructured
The agreed scope for this work is the tasks feature. `users` and `auth` keep their current layout and behaviour; `tasks` consumes them only through `get_authenticated_user`. Restructuring them is a separate change.

## Flat import convention
All backend imports are flat from `app/backend`, for example `from tasks.services import TaskService`. There is no `backend.` prefix.

## Error-body format
Every error response, including framework, validation and domain errors, is `{"error": true, "status_code": int, "detail": str | list}`, built by `error_response` in `main.py`. `TaskNotFoundError` maps to 404 with `"Task not found"`, `InvalidTaskError` to 422 with its message. Validation errors drop `input` and `ctx` so submitted secrets are never echoed.

## Configuration
Settings live in `core/config.py` (`settings`), loaded from the environment, including `CORS_ORIGINS`. No secrets are hardcoded or logged.
