from datetime import date, datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str


class CollectionResponse(BaseModel):
    collected_posts: int
    extracted_entities: int
    processed_channels: int
    started_at: datetime
    finished_at: datetime
    warnings: list[str] = Field(default_factory=list)


class BriefResponse(BaseModel):
    prompt: str


class StatsPoint(BaseModel):
    date: date
    mentions_count: int
    channels_count: int
    total_views: int
    total_reactions: int
    growth_7d: float | None
    growth_30d: float | None
    trend_score: float
    new_trend: bool

