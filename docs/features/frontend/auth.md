# Auth (Frontend Feature Doc)

## 1. Overview
Login, registration and logout for the Flet UI. Code lives in `app/frontend/features/auth/` (`service.py`, `validation.py`, `views.py`). JWTs are held only in the server-side Flet session, never in browser storage.

## 2. UI/UX Flow
- Signed-out user opens any route: redirected to `/login`.
- Login: username + password, then `/`. Enter in the password field submits.
- Register: username, password, confirm password. On success the account is created, the user is logged in automatically and sent to `/`. If account creation works but the automatic login fails, the error is shown and the user stays on the register screen.
- Logout: "Log out" in the profile drawer on the home screen clears the tokens and goes to `/login`.
- Signed-in user opening `/login` or `/register` is redirected to `/`.
- Session expiry: the router logs out, shows the message and goes to `/login`.

## 3. Data Flow
View -> `AuthService` -> `ApiClient` -> backend `/users/*`. The view validates input first (`validation.py`), disables the submit button while the call runs, and shows `ApiError.message` in a snackbar on failure. The backend validates again; client validation is only for fast feedback.

## 4. Components
- `build_login_view(page, auth)` and `build_register_view(page, auth)` in `views.py`, sharing a centred card layout.
- `shared/ui.py` helpers: `navigate`, `show_message`.

## 5. Services/API
`AuthService`: `is_authenticated`, `username`, `login`, `register`, `logout`. Uses `/users/login`, `/users/register` and token refresh through `ApiClient`. Every failure becomes an `ApiError` with a user-safe message.

## 6. Hooks
Flet has no hooks. Equivalent behaviour is in event handlers (`on_click`, `on_submit`) and the router's `page.on_route_change`.

## 7. State Logic
State is the `ApiClient` token pair, one client per browser session (created in `main.py`). Field errors live on the `TextField.error` property; the submit button's `disabled` flag prevents double submits.

## 8. Edge Cases
- Wrong password: generic "invalid credentials" style message from the backend, no hint which field was wrong.
- Duplicate username: backend conflict message shown, form stays filled.
- Backend down or timing out: "Can't reach the server" style message, button re-enabled.
- Session expiry: refresh fails, the user is sent to `/login` with a message.
- Page reload or server restart: tokens are lost by design; log in again.

## 9. Security Considerations
- Tokens only in server-side session memory; one `ApiClient` per session so sessions never share tokens.
- Passwords and tokens are never logged.
- Error messages are generic; raw server text is not displayed.
- The browser never calls the API directly.

## 10. Testing Strategy
Unit tests cover `validation.py`, `AuthService` and `ApiClient` (no network). Views are checked by a build smoke check under flet 1.0.3 and by the manual end-to-end checklist.

## 11. Future Improvements
Persist sessions safely across restarts, rate-limit feedback, password reveal policy, account deletion.
