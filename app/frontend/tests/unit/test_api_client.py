import asyncio
import json

import httpx
import pytest

from api.client import GENERIC_ERROR_MESSAGE, NETWORK_ERROR_MESSAGE, ApiClient, ApiError, AuthenticationError

BASE_URL = "http://api.test"


def make_client(handler) -> ApiClient:
    return ApiClient(BASE_URL, timeout=5, transport=httpx.MockTransport(handler))


def run(coroutine):
    return asyncio.run(coroutine)


def test_request_should_send_bearer_token():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json=[])

    client = make_client(handler)
    client.set_tokens("access-1", "refresh-1")
    assert run(client.request("GET", "/todo/tasks")) == []
    assert seen["auth"] == "Bearer access-1"


def test_request_should_raise_authentication_error_without_token_and_skip_network():
    def handler(request):
        raise AssertionError("no request expected")

    with pytest.raises(AuthenticationError):
        run(make_client(handler).request("GET", "/todo/tasks"))


def test_request_should_refresh_once_and_retry_on_401():
    calls = []

    def handler(request):
        calls.append((request.url.path, request.headers.get("Authorization")))
        if request.url.path == "/users/refresh_token":
            assert json.loads(request.content) == {"token": "refresh-1"}
            return httpx.Response(200, json={"access_token": "access-2"})
        if request.headers["Authorization"] == "Bearer access-1":
            return httpx.Response(401, json={"detail": "Authentication failed"})
        return httpx.Response(200, json={"ok": True})

    client = make_client(handler)
    client.set_tokens("access-1", "refresh-1")
    assert run(client.request("GET", "/todo/tasks")) == {"ok": True}
    assert [path for path, _ in calls] == ["/todo/tasks", "/users/refresh_token", "/todo/tasks"]
    assert calls[-1][1] == "Bearer access-2"


def test_request_should_clear_tokens_when_refresh_fails():
    def handler(request):
        return httpx.Response(401, json={"detail": "Authentication failed"})

    client = make_client(handler)
    client.set_tokens("access-1", "refresh-1")
    with pytest.raises(AuthenticationError) as caught:
        run(client.request("GET", "/todo/tasks"))
    assert client.is_authenticated is False
    assert "log in" in caught.value.message.lower()


def test_request_should_map_network_failure_to_friendly_error():
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    client = make_client(handler)
    client.set_tokens("a", "r")
    with pytest.raises(ApiError) as caught:
        run(client.request("GET", "/todo/tasks"))
    assert caught.value.message == NETWORK_ERROR_MESSAGE
    assert "boom" not in caught.value.message


def test_request_should_hide_server_error_details():
    def handler(request):
        return httpx.Response(500, json={"detail": "psycopg2.OperationalError: secret-host"})

    client = make_client(handler)
    client.set_tokens("a", "r")
    with pytest.raises(ApiError) as caught:
        run(client.request("GET", "/todo/tasks"))
    assert caught.value.message == GENERIC_ERROR_MESSAGE


def test_request_should_surface_backend_detail_for_client_errors():
    def handler(request):
        return httpx.Response(409, json={"error": True, "status_code": 409, "detail": "username already exists"})

    with pytest.raises(ApiError) as caught:
        run(make_client(handler).request("POST", "/users/register", json={}, authenticated=False))
    assert (caught.value.status_code, caught.value.message) == (409, "username already exists")


def test_request_should_use_friendly_message_for_validation_lists():
    def handler(request):
        return httpx.Response(422, json={"detail": [{"loc": ["body", "title"], "msg": "too short"}]})

    client = make_client(handler)
    client.set_tokens("a", "r")
    with pytest.raises(ApiError) as caught:
        run(client.request("POST", "/todo/tasks", json={}))
    assert caught.value.message == "Please check the form and try again."


def test_request_should_say_item_missing_on_404():
    def handler(request):
        return httpx.Response(404, json={"detail": "Task not found"})

    client = make_client(handler)
    client.set_tokens("a", "r")
    with pytest.raises(ApiError) as caught:
        run(client.request("GET", "/todo/tasks/5"))
    assert caught.value.message == "That item no longer exists."


def test_request_should_return_none_for_204():
    client = make_client(lambda request: httpx.Response(204))
    client.set_tokens("a", "r")
    assert run(client.request("DELETE", "/todo/tasks/1")) is None
