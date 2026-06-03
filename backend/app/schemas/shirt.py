from pydantic import BaseModel


class ShirtOfDayResponse(BaseModel):
    trend_entity: str
    trend_entity_type: str
    trend_score: float
    trend_growth_7d: float | None
    brief_prompt: str
    trend_url: str
