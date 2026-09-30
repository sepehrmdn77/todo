from auth.jwt_auth import generate_refresh_token
from tests.api.conftest import DEFAULT_PASSWORD
from users.models import UsersModel


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


def register(client, username="newuser", password="secret1234", confirm=None):
    return client.post(
        "/users/register",
        json={"username": username, "password": password, "confirm_password": confirm or password},
    )


def test_register_should_reject_short_password(anonymous_client):
    assert register(anonymous_client, password="short").status_code == 422


def test_register_should_reject_short_username(anonymous_client):
    assert register(anonymous_client, username=" ab ").status_code == 422


def test_register_should_not_echo_password_on_mismatch(anonymous_client):
    response = register(anonymous_client, password="secret1234", confirm="different99")
    assert response.status_code == 422
    assert "secret1234" not in response.text and "different99" not in response.text


def test_register_should_reject_case_insensitive_duplicate(anonymous_client, user):
    assert register(anonymous_client, username=user.username.upper()).status_code == 409


def test_register_should_store_username_lowercase_and_trimmed(anonymous_client, db_session):
    register(anonymous_client, username="  NewUser ")
    assert db_session.query(UsersModel).filter_by(username="newuser").one_or_none() is not None


def test_refresh_token_should_issue_working_access_token(anonymous_client, user):
    response = anonymous_client.post("/users/refresh_token", json={"token": generate_refresh_token(user.id)})
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert anonymous_client.get("/todo/tasks", headers=headers).status_code == 200


def test_access_with_refresh_token_should_return_401(anonymous_client, user):
    headers = {"Authorization": f"Bearer {generate_refresh_token(user.id)}"}
    assert anonymous_client.get("/todo/tasks", headers=headers).status_code == 401


def test_token_of_deleted_user_should_return_401(auth_client, user, db_session):
    db_session.delete(user)
    db_session.commit()
    response = auth_client.get("/todo/tasks")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication failed"


def test_refresh_for_deleted_user_should_return_401(anonymous_client, user, db_session):
    token = generate_refresh_token(user.id)
    db_session.delete(user)
    db_session.commit()
    assert anonymous_client.post("/users/refresh_token", json={"token": token}).status_code == 401
