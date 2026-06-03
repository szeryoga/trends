from datetime import datetime

from pydantic import BaseModel, Field


class SettingsRead(BaseModel):
    default_posts_limit: int = Field(ge=1, le=100)
    schedule_enabled: bool
    schedule_hour_utc: int = Field(ge=0, le=23)
    last_collected_at: datetime | None


class SettingsUpdate(BaseModel):
    default_posts_limit: int = Field(ge=1, le=100)
    schedule_enabled: bool
    schedule_hour_utc: int = Field(ge=0, le=23)

