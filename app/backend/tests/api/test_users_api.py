from tests.api.conftest import DEFAULT_PASSWORD


def test_login_should_return_401_for_unknown_user(anonymous_client):
    response = anonymous_client.post("/users/login", json={"username": "nobody", "password": "1234567"})
    assert response.status_code == 401


def test_login_should_return_401_for_wrong_password(anonymous_client, user):
    response = anonymous_client.post("/users/login", json={"username": user.username, "password": "@1234567"})
    assert response.status_code == 401


def test_register_should_return_201(anonymous_client):
    payload = {"username": "kazem", "password": "secret1234", "confirm_password": "secret1234"}
    response = anonymous_client.post("/users/register", json=payload)
    assert response.status_code == 201


def test_login_should_return_202_with_tokens(anonymous_client, user):
    response = anonymous_client.post("/users/login", json={"username": user.username, "password": DEFAULT_PASSWORD})
    assert response.status_code == 202
    body = response.json()
    assert body["access_token"] and body["refresh_token"]
