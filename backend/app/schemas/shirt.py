from datetime import datetime

from pydantic import BaseModel


class ShirtBriefHistoryItem(BaseModel):
    id: int
    created_at: datetime
    trend_entity: str
    trend_entity_type: str
    trend_score: float
    trend_growth_7d: float | None
    description: str
    brief_prompt: str


class ShirtOfDayResponse(BaseModel):
    current: ShirtBriefHistoryItem | None
    history: list[ShirtBriefHistoryItem]
