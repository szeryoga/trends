from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.models import ShirtDesign
from app.schemas.shirt import ShirtBriefHistoryItem, ShirtOfDayResponse
from app.services.briefs import build_brief_prompt
from app.services.trend_service import get_trend_detail, list_trends_data


def _build_description(entity: str, entity_type: str, growth_7d: float | None, trend_score: float) -> str:
    growth_text = "новый сигнал" if growth_7d is None else f"рост {growth_7d:.0f}% за 7 дней"
    return f"{entity} / {entity_type}: {growth_text}, score {trend_score:.1f}."


def create_shirt_brief_history_entry(db: Session) -> ShirtDesign:
    trends = list_trends_data(db, days=7, limit=1)
    if not trends:
        raise LookupError("No trends available")
    top_trend = trends[0]
    trend_detail = get_trend_detail(db, top_trend["entity"])
    entry = ShirtDesign(
        trend_entity=trend_detail.entity,
        trend_entity_type=trend_detail.entity_type,
        trend_score=float(top_trend["trend_score"]),
        trend_growth_7d=top_trend["growth_7d"],
        description=_build_description(
            trend_detail.entity,
            trend_detail.entity_type,
            top_trend["growth_7d"],
            float(top_trend["trend_score"]),
        ),
        brief_prompt=build_brief_prompt(trend_detail),
        image_s3_key="",
        image_url="",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_shirt_of_day_payload(db: Session) -> ShirtOfDayResponse:
    items = list(db.scalars(select(ShirtDesign).order_by(desc(ShirtDesign.created_at)).limit(20)).all())
    if not items:
        raise LookupError("No brief history available")
    return ShirtOfDayResponse(
        current=ShirtBriefHistoryItem.model_validate(items[0], from_attributes=True),
        history=[ShirtBriefHistoryItem.model_validate(item, from_attributes=True) for item in items],
    )
