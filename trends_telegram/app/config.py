from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session_name: str = "trend_monitor"
    telegram_session_dir: str = "/data/telegram"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    @property
    def session_path(self) -> Path:
        return Path(self.telegram_session_dir) / self.telegram_session_name


@lru_cache
def get_settings() -> Settings:
    return Settings()

