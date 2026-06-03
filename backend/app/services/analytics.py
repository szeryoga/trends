from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.models import Channel, DailyEntityStat, Entity, Post, now_utc


def _growth(current: int, previous: int) -> tuple[float | None, bool]:
    if previous == 0:
        return (None, current > 0)
    return (((current - previous) / previous) * 100, False)


def recompute_daily_stats(db: Session) -> None:
    rows = db.execute(
        select(
            Entity.normalized_text,
            Entity.entity_type,
            Post.post_date,
            Post.views,
            Post.reactions_count,
            Post.channel_id,
        ).join(Post, Post.id == Entity.post_id)
    ).all()
    db.execute(delete(DailyEntityStat))
    if not rows:
        db.commit()
        return

    frame = pd.DataFrame(
        rows,
        columns=["entity", "entity_type", "post_date", "views", "reactions_count", "channel_id"],
    )
    frame["date"] = pd.to_datetime(frame["post_date"]).dt.date
    grouped = (
        frame.groupby(["date", "entity", "entity_type"], as_index=False)
        .agg(
            mentions_count=("entity", "size"),
            channels_count=("channel_id", "nunique"),
            total_views=("views", "sum"),
            total_reactions=("reactions_count", "sum"),
        )
        .sort_values(["entity", "date"])
    )

    stats_rows: list[DailyEntityStat] = []
    today = datetime.now(timezone.utc).date()
    for _, row in grouped.iterrows():
        entity_mask = frame["entity"] == row["entity"]
        current_date = row["date"]
        current_7_start = current_date - timedelta(days=6)
        previous_7_start = current_date - timedelta(days=13)
        previous_7_end = current_date - timedelta(days=7)
        current_30_start = current_date - timedelta(days=29)
        previous_30_start = current_date - timedelta(days=59)
        previous_30_end = current_date - timedelta(days=30)

        entity_frame = frame[entity_mask]
        current_7 = int(entity_frame[entity_frame["date"].between(current_7_start, current_date)].shape[0])
        previous_7 = int(entity_frame[entity_frame["date"].between(previous_7_start, previous_7_end)].shape[0])
        current_30 = int(entity_frame[entity_frame["date"].between(current_30_start, current_date)].shape[0])
        previous_30 = int(entity_frame[entity_frame["date"].between(previous_30_start, previous_30_end)].shape[0])
        growth_7d, new_trend = _growth(current_7, previous_7)
        growth_30d, _ = _growth(current_30, previous_30)
        trend_score = (
            row["mentions_count"] * 0.25
            + row["channels_count"] * 0.2
            + math.log(row["total_views"] + 1) * 0.2
            + math.log(row["total_reactions"] + 1) * 0.15
            + ((growth_7d or 0.0) * 0.2)
        )
        stats_rows.append(
            DailyEntityStat(
                date=current_date,
                entity=row["entity"],
                entity_type=row["entity_type"],
                mentions_count=int(row["mentions_count"]),
                channels_count=int(row["channels_count"]),
                total_views=int(row["total_views"]),
                total_reactions=int(row["total_reactions"]),
                growth_7d=growth_7d,
                growth_30d=growth_30d,
                trend_score=trend_score,
                new_trend=new_trend and current_date >= today - timedelta(days=7),
                created_at=now_utc(),
            )
        )
    db.add_all(stats_rows)
    db.commit()


def estimate_design_potential(entity_type: str, growth_7d: float | None, related_count: int) -> str:
    if entity_type in {"meme", "visual_style", "subculture", "brand"} and ((growth_7d or 0) > 50 or related_count >= 3):
        return "Высокий потенциал для принта: тренд визуальный, быстро растет и имеет соседние ассоциации."
    if entity_type in {"event", "spb_place", "local_theme", "location"}:
        return "Хороший потенциал для локального дропа: можно завязать дизайн на Петербург и городской контекст."
    return "Средний потенциал: нужен ручной дизайнерский отбор перед генерацией брифа."

