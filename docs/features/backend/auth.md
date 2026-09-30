# Auth (Backend Module Doc)

## 1. Purpose
Registers users, logs them in, and protects routes with JWT bearer tokens. Short-lived access tokens call the API; longer-lived refresh tokens mint new access tokens.

## 2. Entities
- `UsersModel` (`users` table): `id`, `username` (String 250, unique, indexed, stored lowercase), `password` (bcrypt hash), `is_active`, timestamps.
- `TokenModel` (`tokens` table): written on login but never read (see Future Improvements).
- JWT payload: `type` (`access` or `refresh`), `user_id` (int), `iat`, `exp`.

## 3. Services (Use Cases)
Auth is a thin module without a separate service layer; the logic lives in `auth/jwt_auth.py` and `users/routes.py`.
- `generate_access_token` / `generate_refresh_token`: sign an HS256 token with `JWT_SECRET_KEY`. Access lives 15 minutes, refresh 24 hours.
- `decode_access_token` / `decode_refresh_token`: verify signature, expiry, required claims (`exp`, `type`, `user_id`), the expected token type and an integer `user_id`. They return the user id or raise 401.
- `find_active_user`: loads an active user by id or raises 401.
- `get_authenticated_user`: FastAPI dependency; decodes the bearer access token and returns the active `UsersModel`. It never returns `None`.

## 4. Ports
None. Auth reads users directly through the SQLAlchemy session (`get_db`).

## 5. Adapters
- PyJWT for token signing and validation.
- passlib `CryptContext` (bcrypt) for password hashing.
- SQLAlchemy session for user lookup.

## 6. API Endpoints
| Method and path | Request | Success | Errors |
|---|---|---|---|
| `POST /users/register` | `{"username", "password", "confirm_password"}` | 201 `{"detail": "User registered successfully"}` | 409 username exists, 422 validation |
| `POST /users/login` | `{"username", "password"}` | 202 `{"detail", "access_token", "refresh_token"}` | 401 invalid username or password, 422 |
| `POST /users/refresh_token` | `{"token": "<refresh token>"}` | 200 `{"access_token"}` | 401 |

Protected routes expect `Authorization: Bearer <access token>`. Every token failure returns 401 with `detail="Authentication failed"` and header `WWW-Authenticate: Bearer`.

## 7. Validation Rules
- Username: 3 to 250 characters after trimming; stored lowercase; unique (enforced by a DB unique index, checked case-insensitively). Login lookup trims and lowercases too.
- Password: 8 to 128 characters; `confirm_password` must match.
- Refresh token body is a required string.

## 8. Security Model
- Generic 401 detail for every failure, so callers cannot tell expired from forged from wrong-type tokens.
- Access tokens are rejected on refresh and refresh tokens on access (token type check).
- Deleted or inactive users are rejected on both access and refresh.
- 422 responses never echo submitted input (passwords included).
- Passwords are hashed with bcrypt; tokens and passwords are never logged.
- Secret comes from `JWT_SECRET_KEY`; algorithm is pinned to HS256.

## 9. Testing Strategy
- Unit (`tests/unit/test_jwt_auth.py`): round-trips, wrong type, expired, foreign signature, missing claim, garbage. No DB or network.
- API (`tests/api/test_users_api.py`): register rules, case-insensitive duplicates, normalisation, login, refresh, deleted-user 401s.

## 10. Future Improvements
- Refresh-token rotation and revocation: the `tokens` table is currently written on login but never read.
- Rate limiting on login.
