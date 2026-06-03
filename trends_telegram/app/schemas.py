from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ResolveChannelRequest(BaseModel):
    identifier: str


class ChannelResponse(BaseModel):
    title: str
    username: str | None
    url: str


class FetchPostsRequest(BaseModel):
    identifier: str
    limit: int = Field(ge=1, le=100)


class PostPayload(BaseModel):
    telegram_message_id: int
    post_date: datetime
    text: str
    views: int
    forwards: int
    reactions_count: int
    url: str


class FetchPostsResponse(BaseModel):
    posts: list[PostPayload]


class AuthStatusResponse(BaseModel):
    authorized: bool
    session_path: str

