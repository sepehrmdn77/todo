import asyncio
import json

import httpx

from api.client import ApiClient
from features.auth.service import AuthService
from features.auth.validation import validate_login, validate_registration


def test_validate_login_should_require_both_fields():
    assert set(validate_login("  ", "")) == {"username", "password"}


def test_validate_login_should_accept_filled_fields():
    assert validate_login("sara", "anything") == {}


def test_validate_registration_should_check_lengths_and_match():
    errors = validate_registration("ab", "short", "other")
    assert set(errors) == {"username", "password", "confirm_password"}


def test_validate_registration_should_accept_valid_input():
    assert validate_registration(" sara ", "secret1234", "secret1234") == {}


def test_login_should_store_tokens_and_username():
    def handler(request):
        assert json.loads(request.content) == {"username": "sara", "password": "secret1234"}
        return httpx.Response(202, json={"access_token": "a", "refresh_token": "r", "detail": "ok"})

    auth = AuthService(ApiClient("http://api.test", 5, transport=httpx.MockTransport(handler)))
    asyncio.run(auth.login(" Sara ", "secret1234"))
    assert auth.is_authenticated and auth.username == "sara"


def test_register_should_log_in_after_creating_account():
    paths = []

    def handler(request):
        paths.append(request.url.path)
        if request.url.path == "/users/register":
            return httpx.Response(201, json={"detail": "User registered successfully"})
        return httpx.Response(202, json={"access_token": "a", "refresh_token": "r"})

    auth = AuthService(ApiClient("http://api.test", 5, transport=httpx.MockTransport(handler)))
    asyncio.run(auth.register("sara", "secret1234", "secret1234"))
    assert paths == ["/users/register", "/users/login"]
    assert auth.is_authenticated


def test_logout_should_forget_session():
    auth = AuthService(ApiClient("http://api.test", 5, transport=httpx.MockTransport(lambda r: httpx.Response(500))))
    auth._client.set_tokens("a", "r")
    auth.logout()
    assert not auth.is_authenticated and auth.username is None
