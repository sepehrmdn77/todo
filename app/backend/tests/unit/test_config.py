import pytest
from pydantic import ValidationError

from core.config import Settings


def test_settings_should_reject_short_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, SQLALCHEMY_DATABASE_URL="sqlite://", JWT_SECRET_KEY="change-me")


def test_settings_should_accept_32_character_jwt_secret():
    settings = Settings(_env_file=None, SQLALCHEMY_DATABASE_URL="sqlite://", JWT_SECRET_KEY="x" * 32)
    assert len(settings.JWT_SECRET_KEY) == 32
