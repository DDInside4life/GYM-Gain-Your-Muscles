from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "GYM API"
    environment: Literal["development", "staging", "production"] = "development"
    api_prefix: str = "/api"

    database_url: str = Field(
        default="postgresql+asyncpg://gym:gym@db:5432/gym",
        alias="DATABASE_URL",
    )

    secret_key: str = Field(default="dev-secret-change-me", alias="SECRET_KEY", min_length=16)
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES", ge=1)
    refresh_token_expire_days: int = Field(default=14, alias="REFRESH_TOKEN_EXPIRE_DAYS", ge=1)

    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    admin_email: str = Field(default="admin@gym.local", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="admin12345", alias="ADMIN_PASSWORD", min_length=8)

    rate_limit_login: str = Field(default="10/minute", alias="RATE_LIMIT_LOGIN")

    @field_validator("secret_key")
    @classmethod
    def _secret_not_default_in_prod(cls, v: str, info) -> str:
        env = (info.data.get("environment") or "development").lower()
        weak = v.startswith("dev-") or v == "change-me-super-secret-please-32+chars"
        if env == "production" and weak:
            raise ValueError("SECRET_KEY must be set to a strong value in production")
        return v

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_prod(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
