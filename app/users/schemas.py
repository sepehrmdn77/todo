from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class UserLoginSchema(BaseModel):
    username: str = Field(..., max_length=250, description="username of the user")
    password: str = Field(..., description="user password")


class UserRegisterSchema(BaseModel):
    username: str = Field(..., max_length=250, description="username of the user")
    password: str = Field(..., description="user password")
    confirm_password: str = Field(..., description="confirm user password")

    @field_validator("confirm_password")
    def check_passwords_match(cls, confirm_password, validation):
        if not confirm_password == validation.data.get("password"):
            raise ValueError("password doesn't match")
        return confirm_password
