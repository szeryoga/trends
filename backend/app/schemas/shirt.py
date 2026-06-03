from datetime import datetime

from pydantic import BaseModel


class ShirtDesignRead(BaseModel):
    id: int
    trend_entity: str
    trend_entity_type: str
    trend_score: float
    trend_growth_7d: float | None
    brief_prompt: str
    description: str
    image_url: str
    created_at: datetime


class ShirtOfDayResponse(BaseModel):
    current: ShirtDesignRead | None
    history: list[ShirtDesignRead]
