from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.schemas import AuthStatusResponse, ChannelResponse, FetchPostsRequest, FetchPostsResponse, PostPayload, ResolveChannelRequest
from app.telegram_service import telegram_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

app = FastAPI(title="trends-telegram")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    settings = get_settings()
    return AuthStatusResponse(
        authorized=await telegram_service.is_authorized(),
        session_path=str(settings.session_path),
    )


@app.post("/channels/resolve", response_model=ChannelResponse)
async def resolve_channel(payload: ResolveChannelRequest) -> ChannelResponse:
    try:
        result = await telegram_service.resolve_channel(payload.identifier)
        return ChannelResponse(title=result.title, username=result.username, url=result.url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/posts/fetch", response_model=FetchPostsResponse)
async def fetch_posts(payload: FetchPostsRequest) -> FetchPostsResponse:
    try:
        posts = await telegram_service.fetch_recent_posts(payload.identifier, payload.limit)
        return FetchPostsResponse(
            posts=[
                PostPayload(
                    telegram_message_id=item.telegram_message_id,
                    post_date=item.post_date,
                    text=item.text,
                    views=item.views,
                    forwards=item.forwards,
                    reactions_count=item.reactions_count,
                    url=item.url,
                )
                for item in posts
            ]
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

