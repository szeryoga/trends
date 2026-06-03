from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Channel, CollectionSettings, Entity, Post
from app.services.analytics import recompute_daily_stats
from app.services.entity_extractor import get_entity_extractor
from app.services.telegram import fetch_recent_posts_sync

logger = logging.getLogger(__name__)


@dataclass
class CollectionSummary:
    collected_posts: int
    extracted_entities: int
    processed_channels: int
    started_at: datetime
    finished_at: datetime
    warnings: list[str]


def collect_posts(db: Session, limit: int) -> CollectionSummary:
    extractor = get_entity_extractor()
    started_at = datetime.now(timezone.utc)
    warnings: list[str] = []
    collected_posts = 0
    extracted_entities = 0
    channels = db.scalars(select(Channel).where(Channel.is_active.is_(True)).order_by(Channel.title)).all()
    for channel in channels:
        identifier = channel.username or channel.url
        try:
            posts = fetch_recent_posts_sync(identifier, limit)
        except Exception as exc:
            logger.exception("Failed to collect posts for %s", identifier)
            warnings.append(f"{channel.title}: {exc}")
            continue
        for payload in posts:
            duplicate = db.scalar(
                select(Post.id).where(
                    Post.channel_id == channel.id,
                    Post.telegram_message_id == payload.telegram_message_id,
                )
            )
            if duplicate:
                continue
            post = Post(
                telegram_message_id=payload.telegram_message_id,
                channel_id=channel.id,
                post_date=payload.post_date,
                text=payload.text,
                views=payload.views,
                forwards=payload.forwards,
                reactions_count=payload.reactions_count,
                url=payload.url,
            )
            db.add(post)
            db.flush()
            entities = extractor.extract(payload.text)
            for item in entities:
                db.add(
                    Entity(
                        post_id=post.id,
                        entity_text=item.entity_text,
                        normalized_text=item.normalized_text,
                        entity_type=item.entity_type,
                        source=item.source,
                        confidence=item.confidence,
                    )
                )
            collected_posts += 1
            extracted_entities += len(entities)
        db.commit()

    recompute_daily_stats(db)
    settings = db.get(CollectionSettings, 1)
    if settings:
        settings.last_collected_at = datetime.now(timezone.utc)
        db.commit()
    finished_at = datetime.now(timezone.utc)
    return CollectionSummary(
        collected_posts=collected_posts,
        extracted_entities=extracted_entities,
        processed_channels=len(channels),
        started_at=started_at,
        finished_at=finished_at,
        warnings=warnings,
    )
