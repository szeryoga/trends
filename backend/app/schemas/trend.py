from datetime import date

from pydantic import BaseModel

from app.schemas.common import StatsPoint


class TrendRead(BaseModel):
    entity: str
    entity_type: str
    mentions_count: int
    channels_count: int
    total_views: int
    total_reactions: int
    growth_7d: float | None
    growth_30d: float | None
    trend_score: float
    new_trend: bool
    latest_date: date


class TrendPostExample(BaseModel):
    channel_title: str
    post_date: str
    text: str
    url: str


class TrendDetail(BaseModel):
    entity: str
    entity_type: str
    sources: list[str]
    design_potential: str
    stats: list[StatsPoint]
    channels: list[str]
    related_entities: list[str]
    posts: list[TrendPostExample]

