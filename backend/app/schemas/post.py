from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class EntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_text: str
    normalized_text: str
    entity_type: str
    source: str
    confidence: float | None


class PostRead(BaseModel):
    id: int
    telegram_message_id: int
    channel_id: int
    channel_title: str
    post_date: datetime
    text: str
    views: int
    forwards: int
    reactions_count: int
    url: str
    entities: list[EntityRead]
