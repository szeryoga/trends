from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime

from telethon import TelegramClient
from telethon.errors import UsernameInvalidError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TelegramChannelInfo:
    title: str
    username: str | None
    url: str


@dataclass
class TelegramPostPayload:
    telegram_message_id: int
    post_date: datetime
    text: str
    views: int
    forwards: int
    reactions_count: int
    url: str


class TelegramService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.telegram_api_id and self.settings.telegram_api_hash)

    async def _make_client(self) -> TelegramClient:
        return TelegramClient(
            self.settings.telegram_session_name,
            self.settings.telegram_api_id,
            self.settings.telegram_api_hash,
        )

    async def resolve_channel(self, identifier: str) -> TelegramChannelInfo:
        if not self.is_configured():
            raise RuntimeError("Telegram credentials are not configured.")
        client = await self._make_client()
        async with client:
            try:
                entity = await client.get_entity(identifier)
            except UsernameInvalidError as exc:
                raise RuntimeError(f"Cannot resolve channel: {identifier}") from exc
            username = getattr(entity, "username", None)
            url = f"https://t.me/{username}" if username else identifier
            return TelegramChannelInfo(title=getattr(entity, "title", identifier), username=username, url=url)

    async def fetch_recent_posts(self, identifier: str, limit: int) -> list[TelegramPostPayload]:
        if not self.is_configured():
            raise RuntimeError("Telegram credentials are not configured.")
        client = await self._make_client()
        async with client:
            entity = await client.get_entity(identifier)
            messages = await client.get_messages(entity, limit=limit)
            posts: list[TelegramPostPayload] = []
            for message in messages:
                text = (message.message or "").strip()
                if not text:
                    continue
                reactions_count = 0
                if getattr(message, "reactions", None) and getattr(message.reactions, "results", None):
                    reactions_count = sum(result.count for result in message.reactions.results)
                username = getattr(entity, "username", None)
                post_url = f"https://t.me/{username}/{message.id}" if username else ""
                posts.append(
                    TelegramPostPayload(
                        telegram_message_id=message.id,
                        post_date=message.date,
                        text=text,
                        views=message.views or 0,
                        forwards=message.forwards or 0,
                        reactions_count=reactions_count,
                        url=post_url,
                    )
                )
            return posts


telegram_service = TelegramService()


def resolve_channel_sync(identifier: str) -> TelegramChannelInfo:
    return asyncio.run(telegram_service.resolve_channel(identifier))


def fetch_recent_posts_sync(identifier: str, limit: int) -> list[TelegramPostPayload]:
    return asyncio.run(telegram_service.fetch_recent_posts(identifier, limit))

