from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.models import Channel, CollectionSettings
from app.schemas.channel import ChannelCreate, ChannelRead, ChannelUpdate
from app.schemas.common import BriefResponse, CollectionResponse
from app.schemas.post import PostRead
from app.schemas.shirt import ShirtOfDayResponse
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.schemas.trend import TrendDetail, TrendRead
from app.services.briefs import build_brief_prompt
from app.services.channel_service import create_channel
from app.services.collector import collect_posts
from app.services.scheduler import sync_scheduler
from app.services.shirt_of_day import get_shirt_of_day_payload
from app.services.trend_service import get_trend_detail, list_posts_data, list_trends as list_trends_service

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/bootstrap")
def bootstrap(db: Session = Depends(get_db)) -> dict:
    settings = db.get(CollectionSettings, 1)
    channels = db.scalars(select(Channel).order_by(Channel.title)).all()
    top_trends = list_trends_service(db, days=7, limit=20, entity_type=None, category=None)
    return {
        "settings": SettingsRead.model_validate(settings),
        "channels": [ChannelRead.model_validate(channel) for channel in channels],
        "top_trends": top_trends,
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
    return list_posts_data(db, channel_id=channel_id, entity=entity, limit=limit)


@router.get("/trends", response_model=list[TrendRead])
def list_trends(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=20, ge=1, le=100),
    entity_type: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
) -> list[TrendRead]:
    return list_trends_service(db, days, limit, entity_type, category)


@router.get("/trends/{entity_name}", response_model=TrendDetail)
def get_trend(entity_name: str, db: Session = Depends(get_db)) -> TrendDetail:
    normalized = unquote(entity_name)
    try:
        return get_trend_detail(db, normalized)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Trend not found")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/trends/{entity_name}/brief", response_model=BriefResponse)
def create_brief(entity_name: str, db: Session = Depends(get_db)) -> BriefResponse:
    detail = get_trend(entity_name, db)
    return BriefResponse(prompt=build_brief_prompt(detail))


@router.get("/shirt-of-day", response_model=ShirtOfDayResponse)
def get_shirt_of_day(db: Session = Depends(get_db)) -> ShirtOfDayResponse:
    try:
        return get_shirt_of_day_payload(db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="No trends available") from exc


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
