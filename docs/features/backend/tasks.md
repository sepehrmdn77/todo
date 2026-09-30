# Tasks (Backend Module Doc)

## 1. Purpose
The `tasks` module lets an authenticated user keep a personal to-do list. Each task has a title, optional description, optional category (university, finnish, general) and a completion flag. The module also reports per-category counts for the UI. It follows the Lich layering: pure domain in the centre, a port for persistence, a SQLAlchemy adapter, and thin HTTP routes.

## 2. Entities
Defined in `app/backend/tasks/entities.py` (pure Python, no ORM or HTTP imports).

- `Task`: `id`, `user_id`, `title`, `description`, `is_completed`, `category`, `created_date`, `updated_date`. Rules are enforced on construction and in `apply_changes`.
  - Title: trimmed, then 1-150 characters (`TITLE_MAX_LENGTH`).
  - Description: trimmed, at most 500 characters (`DESCRIPTION_MAX_LENGTH`); a blank description is stored as `null`.
  - Category: one of the fixed `TaskCategory` values, or `null`.
  - `is_completed`: must be a real boolean.
- `TaskCategory`: enum with `university`, `finnish`, `general`.
- `CategorySummary`: `category`, `total`, `completed`.
- Errors: `InvalidTaskError` (rule violation, message is user-safe) and `TaskNotFoundError` (missing or foreign task).

## 3. Services (Use Cases)
`TaskService` (`tasks/services.py`) depends only on entities and the `TaskRepository` port:

- `list_tasks(user_id, completed, category, limit, offset)` (default page size 50)
- `get_task(user_id, task_id)`: raises `TaskNotFoundError` when absent
- `create_task(user_id, ...)`
- `update_task(user_id, task_id, changes)`: partial update; only supplied fields change, `null` clears description or category
- `delete_task(user_id, task_id)`
- `summarize_categories(user_id)`: one entry per category, zero-filled, in order university, finnish, general

## 4. Ports
`TaskRepository` (`tasks/ports.py`) is the persistence contract: `list_for_user`, `get_for_user`, `add`, `save`, `delete`, `summarize_by_category`. Every method takes the owning `user_id` (or a task carrying it). `list_for_user` must return incomplete tasks first, then newest first.

## 5. Adapters
`SqlAlchemyTaskRepository` (`tasks/adapters.py`) implements the port on a SQLAlchemy `Session` using `TaskModel` (`tasks/models.py`).

- Ordering: `is_completed` ascending (incomplete first), then `created_date` descending, then `id` descending.
- Every query filters on `user_id`.
- Category is stored as an enum by value (`"finnish"`), nullable. Migration `0002_rename_painting_category` renamed the stored value `painting` to `general` (`ALTER TYPE ... RENAME VALUE` on PostgreSQL, a row `UPDATE` on other dialects); `0001` is unchanged because it was already applied.
- `updated_date` is refreshed through SQLAlchemy `onupdate`.
- `user_id` is NOT NULL, indexed, and cascades on user delete.
- `tasks/dependencies.py` is the composition root: `get_task_service` builds `TaskService(SqlAlchemyTaskRepository(db))`.

## 6. API Endpoints
All paths are under `/todo` and require `Authorization: Bearer <access>`.

| Method | Path | Body / query | Success |
|---|---|---|---|
| GET | `/todo/tasks` | `limit` 1-100 (default 50), `offset` >= 0 (default 0), `completed` bool, `category` | 200 list of `TaskResponse` |
| GET | `/todo/tasks/summary` | none | 200 `[{"category", "total", "completed"}]`, one per category |
| GET | `/todo/tasks/{id}` | none | 200 `TaskResponse` |
| POST | `/todo/tasks` | `{"title", "description"?, "category"?, "is_completed"?}` | 201 `TaskResponse` |
| PATCH | `/todo/tasks/{id}` | any subset of the POST fields | 200 `TaskResponse` |
| DELETE | `/todo/tasks/{id}` | none | 204 |

`TaskResponse` = `{"id", "title", "description", "category", "is_completed", "created_date", "updated_date"}`.

Error body for every failure: `{"error": true, "status_code": int, "detail": str | list}`.

- 401/403: missing or invalid token.
- 404: unknown or foreign id, `detail="Task not found"`.
- 422: request shape errors (`detail` is a list) or domain rule violations (`detail` is a user-safe string).

## 7. Validation Rules
Validation happens in two steps.

1. DTO (`tasks/schemas.py`): shape and lengths. Unknown fields are rejected (`extra="forbid"`), so a client cannot send `user_id`. Title 1-150 characters, description at most 500, category must be a known value, `limit` 1-100, `offset` 0 to 2147483647, path id > 0. `PATCH` with `"title": null` is rejected.
2. Entity rules: trimming, blank title rejection (e.g. `"   "`), control characters rejected (titles: any character below code 32; descriptions: the same except newline, carriage return and tab; NUL would otherwise crash PostgreSQL with a 500), blank description becomes `null`, category and boolean checks. Violations raise `InvalidTaskError`, mapped to 422 in `main.py`.

## 8. Security Model
- Authentication: every route depends on `get_authenticated_user` (JWT).
- Authorization: every query is scoped by the `user_id` from the token, never from the request body.
- Foreign ids return 404, not 403, so ids cannot be enumerated.
- Error messages are user-safe; no request bodies or tokens are logged.

## 9. Testing Strategy
- Unit tests (`tests/unit`) cover entities and `TaskService` with `InMemoryTaskRepository`; no DB or network.
- API tests (`tests/api/test_tasks_api.py`) drive the real app with a per-test SQLite schema and cover auth, create defaults, validation, filters, per-user isolation, partial update, un-completing, delete and summary.

## 10. Future Improvements
- Pagination controls in the UI (the UI currently fetches every page of tasks; the API supports `limit` and `offset`).
- User-defined categories instead of the fixed set.
- Data migration for existing databases: the initial Alembic revision (`0001_initial_schema`) creates the full schema on an empty database only; future schema changes go in new revisions (see `docs/runbooks/backend/backend.md`).
