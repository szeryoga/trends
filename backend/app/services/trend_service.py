from __future__ import annotations

import math
from datetime import timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.models import Channel, DailyEntityStat, Entity, Post
from app.schemas.common import StatsPoint
from app.schemas.post import EntityRead, PostRead
from app.schemas.trend import TrendDetail, TrendPostExample, TrendRead
from app.services.analytics import estimate_design_potential


def list_trends_data(
    db: Session,
    days: int = 7,
    limit: int = 20,
    entity_type: str | None = None,
    category: str | None = None,
) -> list[dict]:
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


def list_trends(
    db: Session,
    days: int = 7,
    limit: int = 20,
    entity_type: str | None = None,
    category: str | None = None,
) -> list[TrendRead]:
    return [TrendRead.model_validate(item) for item in list_trends_data(db, days, limit, entity_type, category)]


def get_trend_detail(db: Session, entity_name: str) -> TrendDetail:
    stats = db.scalars(
        select(DailyEntityStat)
        .where(DailyEntityStat.entity == entity_name)
        .order_by(DailyEntityStat.date)
    ).all()
    if not stats:
        raise LookupError("Trend not found")
    entity_rows = db.execute(
        select(Entity, Post, Channel)
        .join(Post, Post.id == Entity.post_id)
        .join(Channel, Channel.id == Post.channel_id)
        .where(Entity.normalized_text == entity_name)
        .order_by(desc(Post.post_date))
        .limit(20)
    ).all()
    channels = sorted({channel.title for _, _, channel in entity_rows})
    sources = sorted({entity.source for entity, _, _ in entity_rows})
    related_entities = sorted(
        {
            item.normalized_text
            for _, post, _ in entity_rows
            for item in post.entities
            if item.normalized_text != entity_name
        }
    )
    last_stat = stats[-1]
    return TrendDetail(
        entity=entity_name,
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


def list_posts_data(
    db: Session,
    channel_id: int | None = None,
    entity: str | None = None,
    limit: int = 50,
) -> list[PostRead]:
    statement = select(Post).options(joinedload(Post.entities), joinedload(Post.channel)).order_by(desc(Post.post_date)).limit(limit)
    if channel_id is not None:
        statement = statement.where(Post.channel_id == channel_id)
    posts = list(db.scalars(statement).unique().all())
    if entity:
        entity_lower = entity.lower()
        posts = [post for post in posts if any(item.normalized_text.lower() == entity_lower for item in post.entities)]
    return [
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
        for post in posts
    ]
