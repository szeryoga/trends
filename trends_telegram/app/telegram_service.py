from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from telethon import TelegramClient
from telethon.errors import UsernameInvalidError

from app.config import get_settings


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
        self.settings.session_path.parent.mkdir(parents=True, exist_ok=True)

    def is_configured(self) -> bool:
        return bool(self.settings.telegram_api_id and self.settings.telegram_api_hash)

    def create_client(self) -> TelegramClient:
        return TelegramClient(
            str(self.settings.session_path),
            self.settings.telegram_api_id,
            self.settings.telegram_api_hash,
        )

    async def is_authorized(self) -> bool:
        if not self.is_configured():
            return False
        client = self.create_client()
        async with client:
            return await client.is_user_authorized()

    async def ensure_authorized(self) -> None:
        if not self.is_configured():
            raise RuntimeError("Telegram credentials are not configured.")
        if not await self.is_authorized():
            raise RuntimeError(
                "Telegram session is not authorized. Run `docker compose run --rm trends-telegram python -m app.auth_cli`."
            )

    async def resolve_channel(self, identifier: str) -> TelegramChannelInfo:
        await self.ensure_authorized()
        client = self.create_client()
        async with client:
            try:
                entity = await client.get_entity(identifier)
            except UsernameInvalidError as exc:
                raise RuntimeError(f"Cannot resolve channel: {identifier}") from exc
            username = getattr(entity, "username", None)
            url = f"https://t.me/{username}" if username else identifier
            return TelegramChannelInfo(title=getattr(entity, "title", identifier), username=username, url=url)

    async def fetch_recent_posts(self, identifier: str, limit: int) -> list[TelegramPostPayload]:
        await self.ensure_authorized()
        client = self.create_client()
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
                posts.append(
                    TelegramPostPayload(
                        telegram_message_id=message.id,
                        post_date=message.date,
                        text=text,
                        views=message.views or 0,
                        forwards=message.forwards or 0,
                        reactions_count=reactions_count,
                        url=f"https://t.me/{username}/{message.id}" if username else "",
                    )
                )
            return posts


telegram_service = TelegramService()

