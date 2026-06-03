from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.shirt import ShirtOfDayResponse
from app.services.briefs import build_brief_prompt
from app.services.trend_service import get_trend_detail, list_trends_data


def get_shirt_of_day_payload(db: Session) -> ShirtOfDayResponse:
    trends = list_trends_data(db, days=7, limit=1)
    if not trends:
        raise LookupError("No trends available")
    top_trend = trends[0]
    trend_detail = get_trend_detail(db, top_trend["entity"])
    return ShirtOfDayResponse(
        trend_entity=trend_detail.entity,
        trend_entity_type=trend_detail.entity_type,
        trend_score=float(top_trend["trend_score"]),
        trend_growth_7d=top_trend["growth_7d"],
        brief_prompt=build_brief_prompt(trend_detail),
        trend_url=f"/app/trends/{trend_detail.entity}",
    )
