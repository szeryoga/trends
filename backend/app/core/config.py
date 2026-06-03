from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Trend Monitor"
    debug: bool = False
    database_url: str = Field(default="postgresql+psycopg://trend_monitor:trend_monitor@postgres:5432/trend_monitor")
    cors_origins: str = Field(default="http://127.0.0.1:3015,http://127.0.0.1:8015")
    trends_telegram_base_url: str = "http://trends-telegram:8010"
    default_posts_limit: int = 10
    gliner_model: str = "urchade/gliner_multi-v2.1"
    openai_api_key: str = ""
    openai_text_model: str = "gpt-5.5"
    openai_image_model: str = "gpt-image-2"
    openai_image_size: str = "1024x1024"
    s3_endpoint_url: str = ""
    s3_region: str = "ru-1"
    s3_bucket: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_public_base_url: str = ""
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
