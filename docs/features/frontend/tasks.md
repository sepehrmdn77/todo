# Tasks (Frontend Feature Doc)

## 1. Overview
The home screen and the task form. Code lives in `app/frontend/features/tasks/` (`models.py`, `service.py`, `home_view.py`, `form_view.py`). All data comes from the backend API; nothing is mocked.

## 2. UI/UX Flow
- Home (`/`): profile drawer behind the main panel, category cards (count and progress bar), and the task list (incomplete first, as returned by the API).
- Tapping a category card filters the list; tapping it again clears the filter.
- The checkbox toggles completion. On error it reverts and shows a message.
- Tap the row or the pencil icon to edit (`/tasks/<id>`). The + button opens `/tasks/new`.
- Form: title, description, category (or "No category"). Edit mode also has Delete with a confirmation dialog. After saving or deleting the user returns to `/`.

## 3. Data Flow
View -> `TaskService` -> `ApiClient` -> backend `/todo/tasks`. `TaskDraft.validate()` checks input before the call; `to_payload()` builds the request body.

## 4. Components
`HomeView` (class), `build_task_form_view(page, tasks, task)`, `CategorySummary` cards, `ft.Checkbox` rows (keyboard and semantics support), shared helpers in `shared/ui.py` and tokens in `shared/theme.py`.

## 5. Services/API
`TaskService`: `list_tasks`, `category_summary`, `get_task`, `create_task`, `update_task`, `set_completed`, `delete_task`. Errors are `ApiError`; `AuthenticationError` ends the session.

## 6. Hooks
None in Flet. Handlers are closures or methods bound to control events.

## 7. State Logic
`HomeView` fields: `_all_tasks`, `_summaries`, `_selected_category`, `_load_error`. `_load` fetches tasks and summaries; `_render` rebuilds controls from the fields; `_reload` (load + render + update) runs after every mutation and on refresh. Filtering is client-side over `_all_tasks`.

## 8. Edge Cases
- Empty list: "No tasks yet..." or, with a filter, "No tasks in this category yet."
- Load error: message with a "Try again" button.
- Foreign or missing id on `/tasks/<id>`: message, then redirect home. Non-numeric or out-of-range ids redirect home.
- Network errors on save or delete: message, buttons re-enabled, form kept.
- Session expiry during any call: message and redirect to `/login`.

## 9. Security Considerations
Ownership is enforced by the backend (foreign ids behave as missing). Text is rendered as plain `ft.Text`, never HTML. Field lengths are limited on both sides. No tokens are stored in the browser.

## 10. Testing Strategy
Unit tests for models and `TaskService` with a fake transport. Views: build smoke check under flet 1.0.3 plus the manual end-to-end checklist from the full-stack wiring plan (Task 8).

## 11. Future Improvements
Due dates, search, drag-to-reorder, optimistic list updates without full reload, pagination beyond the default page size.
