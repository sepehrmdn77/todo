from pydantic import BaseModel, Field, field_validator

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 250
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class UserLoginSchema(BaseModel):
    username: str = Field(..., max_length=USERNAME_MAX_LENGTH, description="username of the user")
    password: str = Field(..., max_length=PASSWORD_MAX_LENGTH, description="user password")


class UserRegisterSchema(BaseModel):
    username: str = Field(..., max_length=USERNAME_MAX_LENGTH, description="username of the user")
    password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH, description="user password"
    )
    confirm_password: str = Field(..., description="confirm user password")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, username: str) -> str:
        if any(ord(char) < 32 for char in username):
            raise ValueError("username must not contain control characters")
        cleaned = username.strip().lower()
        if len(cleaned) < USERNAME_MIN_LENGTH:
            raise ValueError(f"username must be at least {USERNAME_MIN_LENGTH} characters")
        return cleaned

    @field_validator("confirm_password")
    @classmethod
    def check_passwords_match(cls, confirm_password, validation):
        if not confirm_password == validation.data.get("password"):
            raise ValueError("password doesn't match")
        return confirm_password


class UserRefreshTokenSchema(BaseModel):
    token: str = Field(..., description="refresh token of the user")
