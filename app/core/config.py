from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Enterprise AI Operations Assistant", alias="API_APP_NAME")
    environment: str = Field(default="development", alias="API_ENVIRONMENT")
    version: str = Field(default="0.1.0", alias="API_VERSION")
    host: str = Field(default="127.0.0.1", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(default="", alias="API_CORS_ORIGINS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

