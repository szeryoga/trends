from datetime import datetime

from pydantic import BaseModel, HttpUrl
from pydantic import ConfigDict


class ChannelBase(BaseModel):
    title: str
    username: str | None = None
    url: HttpUrl
    category: str
    is_active: bool = True


class ChannelCreate(BaseModel):
    identifier: str
    category: str = "general"


class ChannelUpdate(BaseModel):
    is_active: bool


class ChannelRead(ChannelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
