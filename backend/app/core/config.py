from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet
from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"

    microsoft_client_id: str = Field(min_length=1)
    microsoft_client_secret: str = Field(min_length=1)
    microsoft_tenant: str = "common"
    microsoft_redirect_uri: str = Field(min_length=1)

    session_secret: str = Field(min_length=32)
    session_cookie_name: str = "jarvis_session"
    # Keep the Jarvis session for seven days. Microsoft tokens are refreshed
    # separately from the encrypted server-side MSAL cache.
    session_max_age: int = 60 * 60 * 24 * 7
    session_https_only: bool = False
    token_encryption_key: str = Field(min_length=44)

    # The key stays on the backend. It is never sent to React.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    database_url: str = "sqlite:///./jarvis.db"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def microsoft_authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.microsoft_tenant}"

    @model_validator(mode="after")
    def validate_production_cookie(self) -> "Settings":
        if self.app_env.lower() == "production" and not self.session_https_only:
            raise ValueError("SESSION_HTTPS_ONLY must be true in production")
        if self.session_max_age <= 0:
            raise ValueError("SESSION_MAX_AGE must be greater than zero")
        try:
            Fernet(self.token_encryption_key.encode())
        except (ValueError, TypeError) as error:
            raise ValueError(
                "TOKEN_ENCRYPTION_KEY must be a valid Fernet key"
            ) from error
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
