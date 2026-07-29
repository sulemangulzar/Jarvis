from functools import lru_cache

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
    session_max_age: int = 3600
    session_https_only: bool = False

    database_url: str = "sqlite:///./jarvis.db"

    model_config = SettingsConfigDict(
        env_file=".env",
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
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
