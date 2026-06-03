from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Channel
from app.schemas.channel import ChannelCreate
from app.services.telegram import resolve_channel_sync


def normalize_channel_identifier(identifier: str) -> str:
    cleaned = identifier.strip()
    if cleaned.startswith("https://t.me/"):
        cleaned = cleaned.removeprefix("https://t.me/")
    cleaned = cleaned.lstrip("@").strip("/")
    return cleaned


def create_channel(db: Session, payload: ChannelCreate) -> Channel:
    identifier = normalize_channel_identifier(payload.identifier)
    existing = db.scalar(select(Channel).where((Channel.username == identifier) | (Channel.url == f"https://t.me/{identifier}")))
    if existing:
        return existing
    resolved = resolve_channel_sync(identifier)
    channel = Channel(
        title=resolved.title,
        username=resolved.username or identifier,
        url=resolved.url,
        category=payload.category,
        is_active=True,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel
