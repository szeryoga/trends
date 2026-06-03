from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.models import CollectionSettings
from app.services.collector import collect_posts

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def _scheduled_collection_job() -> None:
    db: Session = SessionLocal()
    try:
        settings = db.get(CollectionSettings, 1)
        if not settings or not settings.schedule_enabled:
            return
        logger.info("Running scheduled collection")
        collect_posts(db, settings.default_posts_limit)
    except Exception:
        logger.exception("Scheduled collection failed")
    finally:
        db.close()


def sync_scheduler(settings: CollectionSettings | None) -> None:
    job_id = "daily_collection"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    if settings and settings.schedule_enabled:
        scheduler.add_job(
            _scheduled_collection_job,
            CronTrigger(hour=settings.schedule_hour_utc, minute=0),
            id=job_id,
            replace_existing=True,
        )
    if not scheduler.running:
        scheduler.start()

