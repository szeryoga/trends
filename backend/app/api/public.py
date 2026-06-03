from __future__ import annotations

import math
from datetime import timedelta
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.models.models import Channel, CollectionSettings, DailyEntityStat, Entity, Post
from app.schemas.channel import ChannelCreate, ChannelRead, ChannelUpdate
from app.schemas.common import BriefResponse, CollectionResponse, StatsPoint
from app.schemas.post import EntityRead, PostRead
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.schemas.trend import TrendDetail, TrendPostExample, TrendRead
from app.services.analytics import estimate_design_potential
from app.services.briefs import build_brief_prompt
from app.services.channel_service import create_channel
from app.services.collector import collect_posts
from app.services.scheduler import sync_scheduler

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/bootstrap")
def bootstrap(db: Session = Depends(get_db)) -> dict:
    settings = db.get(CollectionSettings, 1)
    channels = db.scalars(select(Channel).order_by(Channel.title)).all()
    top_trends = _list_trends(db, days=7, limit=20, entity_type=None, category=None)
    return {
        "settings": SettingsRead.model_validate(settings),
        "channels": [ChannelRead.model_validate(channel) for channel in channels],
        "top_trends": [TrendRead.model_validate(item) for item in top_trends],
    }


@router.get("/channels", response_model=list[ChannelRead])
def list_channels(db: Session = Depends(get_db)) -> list[Channel]:
    return list(db.scalars(select(Channel).order_by(Channel.title)).all())


@router.post("/channels", response_model=ChannelRead)
def add_channel(payload: ChannelCreate, db: Session = Depends(get_db)) -> Channel:
    try:
        return create_channel(db, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/channels/{channel_id}", response_model=ChannelRead)
def update_channel(channel_id: int, payload: ChannelUpdate, db: Session = Depends(get_db)) -> Channel:
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    channel.is_active = payload.is_active
    db.commit()
    db.refresh(channel)
    return channel


@router.post("/collect", response_model=CollectionResponse)
def run_collection(limit: int | None = Query(default=None, ge=1, le=100), db: Session = Depends(get_db)) -> CollectionResponse:
    settings = db.get(CollectionSettings, 1)
    effective_limit = limit or (settings.default_posts_limit if settings else 10)
    summary = collect_posts(db, effective_limit)
    return CollectionResponse(**summary.__dict__)


@router.get("/posts", response_model=list[PostRead])
def list_posts(
    channel_id: int | None = None,
    entity: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[PostRead]:
    statement = select(Post).options(joinedload(Post.entities), joinedload(Post.channel)).order_by(desc(Post.post_date)).limit(limit)
    if channel_id is not None:
        statement = statement.where(Post.channel_id == channel_id)
    posts = list(db.scalars(statement).unique().all())
    if entity:
        entity_lower = entity.lower()
        posts = [post for post in posts if any(item.normalized_text.lower() == entity_lower for item in post.entities)]
    result: list[PostRead] = []
    for post in posts:
        result.append(
            PostRead(
                id=post.id,
                telegram_message_id=post.telegram_message_id,
                channel_id=post.channel_id,
                channel_title=post.channel.title,
                post_date=post.post_date,
                text=post.text,
                views=post.views,
                forwards=post.forwards,
                reactions_count=post.reactions_count,
                url=post.url,
                entities=[EntityRead.model_validate(item) for item in post.entities],
            )
        )
    return result


def _list_trends(db: Session, days: int, limit: int, entity_type: str | None, category: str | None) -> list[dict]:
    latest_statement = select(func.max(Post.post_date)).join(Channel, Channel.id == Post.channel_id)
    if category:
        latest_statement = latest_statement.where(Channel.category == category)
    latest_datetime = db.scalar(latest_statement)
    latest_date = latest_datetime.date() if latest_datetime else None
    if latest_date is None:
        return []
    current_start = latest_date - timedelta(days=days - 1)
    earliest_needed = latest_date - timedelta(days=59)
    statement = (
        select(
            Entity.normalized_text,
            Entity.entity_type,
            Post.channel_id,
            Post.views,
            Post.reactions_count,
            func.date(Post.post_date),
        )
        .join(Post, Post.id == Entity.post_id)
        .join(Channel, Channel.id == Post.channel_id)
        .where(Post.post_date >= earliest_needed)
    )
    if category:
        statement = statement.where(Channel.category == category)
    rows = db.execute(statement).all()
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for normalized_text, row_entity_type, channel_id, views, reactions_count, post_date in rows:
        if entity_type and row_entity_type != entity_type:
            continue
        key = (normalized_text, row_entity_type)
        bucket = grouped.setdefault(
            key,
            {
                "entity": normalized_text,
                "entity_type": row_entity_type,
                "current_mentions": 0,
                "current_channels": set(),
                "current_views": 0,
                "current_reactions": 0,
                "latest_date": latest_date,
                "dates": [],
            },
        )
        bucket["dates"].append(post_date)
        if post_date >= current_start:
            bucket["current_mentions"] += 1
            bucket["current_channels"].add(channel_id)
            bucket["current_views"] += views
            bucket["current_reactions"] += reactions_count

    items: list[dict] = []
    for bucket in grouped.values():
        dates = bucket["dates"]
        current_7_start = latest_date - timedelta(days=6)
        previous_7_start = latest_date - timedelta(days=13)
        previous_7_end = latest_date - timedelta(days=7)
        current_30_start = latest_date - timedelta(days=29)
        previous_30_start = latest_date - timedelta(days=59)
        previous_30_end = latest_date - timedelta(days=30)
        current_7 = sum(1 for item_date in dates if current_7_start <= item_date <= latest_date)
        previous_7 = sum(1 for item_date in dates if previous_7_start <= item_date <= previous_7_end)
        current_30 = sum(1 for item_date in dates if current_30_start <= item_date <= latest_date)
        previous_30 = sum(1 for item_date in dates if previous_30_start <= item_date <= previous_30_end)
        growth_7d = None if previous_7 == 0 else ((current_7 - previous_7) / previous_7) * 100
        growth_30d = None if previous_30 == 0 else ((current_30 - previous_30) / previous_30) * 100
        mentions_count = int(bucket["current_mentions"])
        channels_count = len(bucket["current_channels"])
        total_views = int(bucket["current_views"])
        total_reactions = int(bucket["current_reactions"])
        if mentions_count == 0:
            continue
        items.append(
            {
                "entity": bucket["entity"],
                "entity_type": bucket["entity_type"],
                "mentions_count": mentions_count,
                "channels_count": channels_count,
                "total_views": total_views,
                "total_reactions": total_reactions,
                "growth_7d": growth_7d,
                "growth_30d": growth_30d,
                "trend_score": (
                    mentions_count * 0.25
                    + channels_count * 0.2
                    + math.log(total_views + 1) * 0.2
                    + math.log(total_reactions + 1) * 0.15
                    + ((growth_7d or 0.0) * 0.2)
                ),
                "new_trend": previous_7 == 0 and current_7 > 0,
                "latest_date": latest_date,
            }
        )
    return sorted(items, key=lambda item: item["trend_score"], reverse=True)[:limit]


@router.get("/trends", response_model=list[TrendRead])
def list_trends(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=20, ge=1, le=100),
    entity_type: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
) -> list[TrendRead]:
    return [TrendRead.model_validate(item) for item in _list_trends(db, days, limit, entity_type, category)]


@router.get("/trends/{entity_name}", response_model=TrendDetail)
def get_trend(entity_name: str, db: Session = Depends(get_db)) -> TrendDetail:
    normalized = unquote(entity_name)
    stats = db.scalars(
        select(DailyEntityStat)
        .where(DailyEntityStat.entity == normalized)
        .order_by(DailyEntityStat.date)
    ).all()
    if not stats:
        raise HTTPException(status_code=404, detail="Trend not found")
    entity_rows = db.execute(
        select(Entity, Post, Channel)
        .join(Post, Post.id == Entity.post_id)
        .join(Channel, Channel.id == Post.channel_id)
        .where(Entity.normalized_text == normalized)
        .order_by(desc(Post.post_date))
        .limit(20)
    ).all()
    channels = sorted({channel.title for _, _, channel in entity_rows})
    sources = sorted({entity.source for entity, _, _ in entity_rows})
    related_entities = sorted(
        {
            item.normalized_text
            for entity, post, _ in entity_rows
            for item in post.entities
            if item.normalized_text != normalized
        }
    )
    last_stat = stats[-1]
    detail = TrendDetail(
        entity=normalized,
        entity_type=last_stat.entity_type,
        sources=sources,
        design_potential=estimate_design_potential(last_stat.entity_type, last_stat.growth_7d, len(related_entities)),
        stats=[StatsPoint.model_validate(item, from_attributes=True) for item in stats],
        channels=channels,
        related_entities=related_entities,
        posts=[
            TrendPostExample(
                channel_title=channel.title,
                post_date=post.post_date.isoformat(),
                text=post.text,
                url=post.url,
            )
            for _, post, channel in entity_rows
        ],
    )
    return detail


@router.post("/trends/{entity_name}/brief", response_model=BriefResponse)
def create_brief(entity_name: str, db: Session = Depends(get_db)) -> BriefResponse:
    detail = get_trend(entity_name, db)
    return BriefResponse(prompt=build_brief_prompt(detail))


@router.get("/settings", response_model=SettingsRead)
def get_settings_view(db: Session = Depends(get_db)) -> SettingsRead:
    settings = db.get(CollectionSettings, 1)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return SettingsRead.model_validate(settings)


@router.put("/settings", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)) -> SettingsRead:
    settings = db.get(CollectionSettings, 1)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    settings.default_posts_limit = payload.default_posts_limit
    settings.schedule_enabled = payload.schedule_enabled
    settings.schedule_hour_utc = payload.schedule_hour_utc
    db.commit()
    db.refresh(settings)
    sync_scheduler(settings)
    return SettingsRead.model_validate(settings)
