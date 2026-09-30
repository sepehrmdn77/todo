from typing import Optional

from api.client import ApiClient


class AuthService:
    """Login/register/logout for one Flet session."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client
        self._username: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return self._client.is_authenticated

    @property
    def username(self) -> Optional[str]:
        return self._username if self.is_authenticated else None

    async def login(self, username: str, password: str) -> None:
        normalized = username.strip().lower()
        data = await self._client.request(
            "POST",
            "/users/login",
            json={"username": normalized, "password": password},
            authenticated=False,
        )
        self._client.set_tokens(data["access_token"], data["refresh_token"])
        self._username = normalized

    async def register(self, username: str, password: str, confirm_password: str) -> None:
        await self._client.request(
            "POST",
            "/users/register",
            json={"username": username.strip(), "password": password, "confirm_password": confirm_password},
            authenticated=False,
        )
        await self.login(username, password)

    def logout(self) -> None:
        self._client.clear_tokens()
        self._username = None
