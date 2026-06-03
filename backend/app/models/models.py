from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AuditMixin(TimestampMixin):
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class Channel(TimestampMixin, Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    url: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    posts: Mapped[list["Post"]] = relationship(back_populates="channel", cascade="all, delete-orphan")


class Post(TimestampMixin, Base):
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint("telegram_message_id", "channel_id", name="uq_posts_message_channel"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    post_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    text: Mapped[str] = mapped_column(Text)
    views: Mapped[int] = mapped_column(Integer, default=0)
    forwards: Mapped[int] = mapped_column(Integer, default=0)
    reactions_count: Mapped[int] = mapped_column(Integer, default=0)
    url: Mapped[str] = mapped_column(String(500))
    channel: Mapped[Channel] = relationship(back_populates="posts")
    entities: Mapped[list["Entity"]] = relationship(back_populates="post", cascade="all, delete-orphan")


class Entity(TimestampMixin, Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    entity_text: Mapped[str] = mapped_column(String(255))
    normalized_text: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    post: Mapped[Post] = relationship(back_populates="entities")


class DailyEntityStat(TimestampMixin, Base):
    __tablename__ = "daily_entity_stats"
    __table_args__ = (UniqueConstraint("date", "entity", "entity_type", name="uq_daily_entity_stats_date_entity_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    entity: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(120))
    mentions_count: Mapped[int] = mapped_column(Integer)
    channels_count: Mapped[int] = mapped_column(Integer)
    total_views: Mapped[int] = mapped_column(Integer)
    total_reactions: Mapped[int] = mapped_column(Integer)
    growth_7d: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_30d: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend_score: Mapped[float] = mapped_column(Float)
    new_trend: Mapped[bool] = mapped_column(Boolean, default=False)


class CollectionSettings(AuditMixin, Base):
    __tablename__ = "collection_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    default_posts_limit: Mapped[int] = mapped_column(Integer, default=10)
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_hour_utc: Mapped[int] = mapped_column(Integer, default=6)
    last_collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

