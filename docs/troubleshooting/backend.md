# Backend Troubleshooting

## 401 "Authentication failed" right after login
- Symptom: a request with a fresh access token returns 401.
- Cause: clock skew between client and server (token looks expired), `JWT_SECRET_KEY` changed after the token was issued, or the user was deleted or deactivated.
- Fix: sync the clock, log in again after any secret change, and confirm the user still exists and is active.

## 422 on register
- Symptom: `POST /users/register` returns 422.
- Cause: username shorter than 3 characters after trimming (or over 250), password outside 8 to 128 characters, or `confirm_password` mismatch.
- Fix: adjust the input to the rules. The response intentionally does not echo what you sent.

## "Task not found" for a task I can see
- Symptom: GET/PATCH/DELETE on a task id returns 404 although the task exists.
- Cause: the task belongs to a different user; tasks are isolated per user.
- Fix: authenticate as the owner of the task.

## Tests pick up my real DB
- Symptom: worry that pytest touches the development database.
- Cause: it cannot; `tests/conftest.py` overrides the environment before the app loads.
- Fix: none needed. If data looks wrong, check that you are running from `app/backend`.

## `ModuleNotFoundError: backend`
- Symptom: import fails with `No module named 'backend'`.
- Cause: the code uses flat imports rooted at `app/backend` (for example `from tasks.services import TaskService`).
- Fix: change the import to the flat form and run commands from `app/backend`.
