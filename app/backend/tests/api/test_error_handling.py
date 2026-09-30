import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def exploding_route():
    router = APIRouter()

    @router.get("/_test/explode")
    def explode():
        raise RuntimeError("boom")

    app.include_router(router)
    yield
    app.router.routes[:] = [r for r in app.router.routes if getattr(r, "path", "") != "/_test/explode"]


def test_unhandled_exception_should_return_uniform_500_body(exploding_route):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/explode")
    assert response.status_code == 500
    assert response.json() == {"error": True, "status_code": 500, "detail": "Internal server error"}
