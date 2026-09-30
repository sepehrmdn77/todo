# Frontend Architecture

## Folder map
```
app/frontend/
  main.py          bootstrap only: settings, ApiClient, Router
  router.py        page.route -> view, signed-in guard
  config.py        env settings (API_BASE_URL, API_TIMEOUT_SECONDS)
  api/             ApiClient, ApiError (the only place that does HTTP)
  features/<f>/    service.py, views.py, models.py, validation.py
  shared/          theme.py (design tokens), ui.py (navigate, messages)
  tests/unit/
```

## Dependency rules
- views -> services -> `ApiClient`. Views never build HTTP requests.
- No HTTP outside `api/`.
- `shared` never imports from `features`.
- Imports are flat from `app/frontend` (`from api.client import ApiClient`).

## Adapting rules.md to Flet
rules.md describes a React/Next layout (components, hooks, services). Flet is server-side Python UI, so: components become view builders or view classes, hooks become event handlers and the router, services stay services, and `shared/` holds tokens and helpers.

## Session model
The Flet server runs the UI and calls the backend over the Docker network; the browser only talks to Flet. `main()` runs once per browser session and creates its own `ApiClient`, so JWTs live in that session's memory only and are never sent to browser storage. `page.on_close` closes the client.

## Routes
`/login`, `/register`, `/`, `/tasks/new`, `/tasks/<id>`. Unknown routes go to `/`; signed-out users go to `/login`; signed-in users on `/login` or `/register` go to `/`.

## Flet 1.0 API notes
Flet 1.0 is not 0.x: `ft.Button(content=...)` (no `ElevatedButton`), `ft.Icons.X`, `ft.Padding.only`, `ft.BorderRadius.only`, `ft.Alignment.CENTER`, `ft.Scale`, `ft.Animation`, async `page.push_route`, `page.run_task`, `page.show_dialog` / `page.pop_dialog`, `ft.View(route=..., controls=[...])` with keyword arguments only, `TextField(error=...)`, `Dropdown(on_select=...)`. Pinned: `flet[web]==1.0.3`.
