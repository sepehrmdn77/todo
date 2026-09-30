"""Client-side checks mirroring the backend rules, so users get instant feedback."""

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 250
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def validate_login(username: str, password: str) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not username.strip():
        errors["username"] = "Enter your username."
    if not password:
        errors["password"] = "Enter your password."
    return errors


def validate_registration(username: str, password: str, confirm_password: str) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not USERNAME_MIN_LENGTH <= len(username.strip()) <= USERNAME_MAX_LENGTH:
        errors["username"] = f"Use {USERNAME_MIN_LENGTH} to {USERNAME_MAX_LENGTH} characters."
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        errors["password"] = f"Use at least {PASSWORD_MIN_LENGTH} characters."
    if confirm_password != password:
        errors["confirm_password"] = "Passwords don't match."
    return errors
