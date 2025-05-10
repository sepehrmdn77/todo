
def test_login_invalid_data_response_401(anonymous_client):
    payload = { #  wrong user
        "username": "test",
        "password": "1234567"
    }
    response = anonymous_client.post("/users/login", json=payload)
    assert response.status_code == 401

    payload = { #  wrong password
        "username": "testuser",
        "password": "@1234567"
    }
    response = anonymous_client.post("/users/login", json=payload)
    assert response.status_code == 401


def test_register_response_201(anonymous_client):
    payload = {
        "username": "kazem",
        "password": "secret1234",
        "confirm_password": "secret1234"
    }
    response = anonymous_client.post("/users/register", json=payload)
    assert response.status_code == 201

# def test_login_response_202(anonymous_client):
#     payload = {
#         "username": "usertest",
#         "password": "12345678"
#     }
#     response = anonymous_client.post("/users/login", json=payload)
#     assert response.status_code == 202
#     assert "access_token" in response.json()
#     assert "refresh_token" in response.json()

