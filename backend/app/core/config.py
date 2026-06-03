from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Trend Monitor"
    debug: bool = False
    database_url: str = Field(default="postgresql+psycopg://trend_monitor:trend_monitor@postgres:5432/trend_monitor")
    cors_origins: str = Field(default="http://127.0.0.1:3015,http://127.0.0.1:8015")
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session_name: str = "trend_monitor"
    default_posts_limit: int = 10
    gliner_model: str = "urchade/gliner_multi-v2.1"
    schedule_enabled: bool = False
    schedule_hour_utc: int = 6

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    @field_validator("debug", "schedule_enabled", mode="before")
    @classmethod
    def empty_string_to_false(cls, value: object) -> object:
        if value == "":
            return False
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

