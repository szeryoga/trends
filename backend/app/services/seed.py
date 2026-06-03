from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.models import Channel, CollectionSettings

logger = logging.getLogger(__name__)

DEFAULT_CHANNELS = [
    {"title": "Лентач", "username": "lentachold", "url": "https://t.me/lentachold", "category": "news"},
    {"title": "МДК", "username": "mudak", "url": "https://t.me/mudak", "category": "meme"},
    {"title": "Двач", "username": "ru2ch", "url": "https://t.me/ru2ch", "category": "meme"},
    {"title": "Код Дурова", "username": "d_code", "url": "https://t.me/d_code", "category": "tech"},
    {"title": "Технокотики", "username": "techsparks", "url": "https://t.me/techsparks", "category": "tech"},
    {"title": "Бумага", "username": "paperpaper_ru", "url": "https://t.me/paperpaper_ru", "category": "spb"},
    {"title": "Ротонда", "username": "rotondamedia", "url": "https://t.me/rotondamedia", "category": "spb"},
    {"title": "Афиша Daily", "username": "afishadaily", "url": "https://t.me/afishadaily", "category": "culture"},
    {"title": "The Flow", "username": "theflowmusic", "url": "https://t.me/theflowmusic", "category": "music"},
    {"title": "Design Hunters", "username": "designhunters", "url": "https://t.me/designhunters", "category": "design"},
]


def seed_initial_data() -> None:
    settings = get_settings()
    db: Session = SessionLocal()
    try:
        if db.scalar(select(CollectionSettings.id).limit(1)) is None:
            db.add(
                CollectionSettings(
                    id=1,
                    default_posts_limit=settings.default_posts_limit,
                    schedule_enabled=settings.schedule_enabled,
                    schedule_hour_utc=settings.schedule_hour_utc,
                )
            )
        existing_urls = set(db.scalars(select(Channel.url)).all())
        existing_usernames = set(db.scalars(select(Channel.username)).all())
        for item in DEFAULT_CHANNELS:
            if item["url"] in existing_urls or item["username"] in existing_usernames:
                continue
            db.add(Channel(**item, is_active=True))
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            # Startup runs in multiple gunicorn workers. Duplicate seed inserts are benign.
            logger.info("Skipping duplicate seed data during concurrent startup: %s", exc)
    finally:
        db.close()
