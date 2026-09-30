from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from users.models import UsersModel

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_SECONDS = 15 * 60
REFRESH_TOKEN_TTL_SECONDS = 24 * 60 * 60
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

security = HTTPBearer()


def _authentication_failed() -> HTTPException:
    # One generic message for every failure so callers can't probe why a token was rejected.
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _generate_token(user_id: int, token_type: str, expire_in: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "type": token_type,
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expire_in),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _decode_token(token: str, expected_type: str) -> int:
    """Validate signature, expiry (PyJWT), token type and user_id; return the user id."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "type", "user_id"]},
        )
    except jwt.PyJWTError:
        raise _authentication_failed() from None
    user_id = payload["user_id"]
    if payload["type"] != expected_type or not isinstance(user_id, int) or isinstance(user_id, bool):
        raise _authentication_failed()
    return user_id


def generate_access_token(user_id: int, expire_in: int = ACCESS_TOKEN_TTL_SECONDS) -> str:
    return _generate_token(user_id, ACCESS_TOKEN_TYPE, expire_in)


def generate_refresh_token(user_id: int, expire_in: int = REFRESH_TOKEN_TTL_SECONDS) -> str:
    return _generate_token(user_id, REFRESH_TOKEN_TYPE, expire_in)


def decode_access_token(token: str) -> int:
    return _decode_token(token, ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> int:
    return _decode_token(token, REFRESH_TOKEN_TYPE)


def find_active_user(db: Session, user_id: int) -> UsersModel:
    user_obj = db.query(UsersModel).filter_by(id=user_id, is_active=True).one_or_none()
    if user_obj is None:
        raise _authentication_failed()
    return user_obj


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UsersModel:
    return find_active_user(db, decode_access_token(credentials.credentials))
