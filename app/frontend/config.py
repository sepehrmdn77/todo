import os
from dataclasses import dataclass

DEFAULT_API_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class FrontendSettings:
    api_base_url: str
    request_timeout_seconds: float


def load_settings() -> FrontendSettings:
    """Read frontend configuration from the environment (see .env.example)."""
    base_url = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("API_BASE_URL must start with http:// or https://")
    timeout = float(os.getenv("API_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    if timeout <= 0:
        raise ValueError("API_TIMEOUT_SECONDS must be positive")
    return FrontendSettings(api_base_url=base_url, request_timeout_seconds=timeout)
