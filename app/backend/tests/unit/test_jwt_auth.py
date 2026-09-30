from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from auth.jwt_auth import (
    decode_access_token,
    decode_refresh_token,
    generate_access_token,
    generate_refresh_token,
)
from core.config import settings


def assert_rejected(decode, token):
    with pytest.raises(HTTPException) as caught:
        decode(token)
    assert caught.value.status_code == 401
    assert caught.value.detail == "Authentication failed"


def test_decode_access_token_should_return_user_id():
    assert decode_access_token(generate_access_token(7)) == 7


def test_decode_refresh_token_should_return_user_id():
    assert decode_refresh_token(generate_refresh_token(7)) == 7


def test_decode_access_token_should_reject_refresh_token():
    assert_rejected(decode_access_token, generate_refresh_token(7))


def test_decode_access_token_should_reject_expired_token():
    assert_rejected(decode_access_token, generate_access_token(7, expire_in=-1))


def test_decode_access_token_should_reject_foreign_signature():
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {"type": "access", "user_id": 7, "iat": now, "exp": now + timedelta(minutes=5)},
        "not-" + settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    assert_rejected(decode_access_token, forged)


def test_decode_access_token_should_reject_missing_user_id():
    now = datetime.now(timezone.utc)
    token = jwt.encode({"type": "access", "exp": now + timedelta(minutes=5)}, settings.JWT_SECRET_KEY, algorithm="HS256")
    assert_rejected(decode_access_token, token)


def test_decode_access_token_should_reject_garbage():
    assert_rejected(decode_access_token, "not-a-jwt")
