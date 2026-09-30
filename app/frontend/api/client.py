"""HTTP client for the Todo API. One instance per Flet session.

Tokens live only in this object's memory on the Flet server: they never reach the browser.
Every error raised to callers carries a message that is safe to show to users.
"""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = "Something went wrong. Please try again."
NETWORK_ERROR_MESSAGE = "Can't reach the server. Check your connection and try again."
SESSION_EXPIRED_MESSAGE = "Your session has expired. Please log in again."
LOGIN_REQUIRED_MESSAGE = "Please log in to continue."
VALIDATION_MESSAGE = "Please check the form and try again."
NOT_FOUND_MESSAGE = "That item no longer exists."
REFRESH_PATH = "/users/refresh_token"


class ApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class AuthenticationError(ApiError):
    """The session is missing or expired; the user must log in again."""


def _user_message(response: httpx.Response) -> str:
    if response.status_code >= 500:
        return GENERIC_ERROR_MESSAGE
    if response.status_code == 404:
        return NOT_FOUND_MESSAGE
    try:
        detail = response.json().get("detail")
    except (ValueError, AttributeError):
        detail = None
    if isinstance(detail, str) and detail:
        return detail  # backend 4xx string details are written for end users
    if response.status_code == 422:
        return VALIDATION_MESSAGE
    return GENERIC_ERROR_MESSAGE


class ApiClient:
    def __init__(
        self,
        base_url: str,
        timeout: float,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self._http = httpx.AsyncClient(base_url=base_url, timeout=timeout, transport=transport)
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    def set_tokens(self, access_token: str, refresh_token: str) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token

    def clear_tokens(self) -> None:
        self._access_token = None
        self._refresh_token = None

    async def close(self) -> None:
        await self._http.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[dict[str, Any]] = None,
        authenticated: bool = True,
    ) -> Any:
        response = await self._send(method, path, json=json, params=params, authenticated=authenticated)
        if response.status_code == 401 and authenticated and await self._refresh_access_token():
            response = await self._send(method, path, json=json, params=params, authenticated=True)
        return self._parse(response, authenticated)

    async def _send(self, method, path, *, json, params, authenticated) -> httpx.Response:
        headers = {}
        if authenticated:
            if self._access_token is None:
                raise AuthenticationError(401, LOGIN_REQUIRED_MESSAGE)
            headers["Authorization"] = f"Bearer {self._access_token}"
        try:
            return await self._http.request(method, path, json=json, params=params, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning("API request failed: %s %s (%s)", method, path, type(exc).__name__)
            raise ApiError(0, NETWORK_ERROR_MESSAGE) from None

    async def _refresh_access_token(self) -> bool:
        if self._refresh_token is None:
            return False
        try:
            response = await self._http.post(REFRESH_PATH, json={"token": self._refresh_token})
        except httpx.HTTPError as exc:
            logger.warning("Token refresh failed (%s)", type(exc).__name__)
            return False
        if response.status_code != 200:
            self.clear_tokens()
            return False
        self._access_token = response.json()["access_token"]
        return True

    def _parse(self, response: httpx.Response, authenticated: bool) -> Any:
        if response.status_code == 204:
            return None
        if response.is_success:
            return response.json()
        if response.status_code == 401 and authenticated:
            self.clear_tokens()
            raise AuthenticationError(401, SESSION_EXPIRED_MESSAGE)
        logger.info("API returned %s for %s %s", response.status_code, response.request.method, response.request.url.path)
        raise ApiError(response.status_code, _user_message(response))
