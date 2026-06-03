from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import httpx

from app.core.config import get_settings


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


class TrendsTelegramClient:
    def __init__(self) -> None:
        self.base_url = get_settings().trends_telegram_base_url.rstrip("/")

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = None
            try:
                payload = response.json()
                detail = payload.get("detail")
            except Exception:
                detail = None
            if detail:
                raise RuntimeError(detail) from exc
            raise

    def resolve_channel(self, identifier: str) -> TelegramChannelInfo:
        with httpx.Client(base_url=self.base_url, timeout=60.0) as client:
            response = client.post("/channels/resolve", json={"identifier": identifier})
            self._raise_for_status(response)
            payload = response.json()
            return TelegramChannelInfo(
                title=payload["title"],
                username=payload.get("username"),
                url=payload["url"],
            )

    def fetch_recent_posts(self, identifier: str, limit: int) -> list[TelegramPostPayload]:
        with httpx.Client(base_url=self.base_url, timeout=120.0) as client:
            response = client.post("/posts/fetch", json={"identifier": identifier, "limit": limit})
            self._raise_for_status(response)
            payload = response.json()
            return [
                TelegramPostPayload(
                    telegram_message_id=item["telegram_message_id"],
                    post_date=datetime.fromisoformat(item["post_date"]),
                    text=item["text"],
                    views=item["views"],
                    forwards=item["forwards"],
                    reactions_count=item["reactions_count"],
                    url=item["url"],
                )
                for item in payload["posts"]
            ]


telegram_client = TrendsTelegramClient()
