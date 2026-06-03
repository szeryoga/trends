from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.public import router as public_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models.models import CollectionSettings
from app.services.scheduler import scheduler, sync_scheduler
from app.services.seed import seed_initial_data

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_initial_data()
    db = SessionLocal()
    try:
        sync_scheduler(db.get(CollectionSettings, 1))
    finally:
        db.close()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(public_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    finally:
        db.close()
    return {"status": "ok"}
