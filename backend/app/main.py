from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import router
from app.core.config import get_settings
from app.core.crypto import decrypt_text
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.services.config_manager import ConfigManager
from app.services.repository import ensure_admin_user
from app.services.state import AppState
from app.utils.logger import setup_logging
from app.db import models


async def _cleanup_logs(days: int) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    async with AsyncSessionLocal() as session:
        await session.execute(delete(models.SystemMetric).where(models.SystemMetric.created_at < cutoff))
        await session.execute(delete(models.RiskEvent).where(models.RiskEvent.created_at < cutoff))
        await session.execute(delete(models.Alert).where(models.Alert.created_at < cutoff))
        await session.commit()


def schedule_jobs(app: FastAPI, config) -> None:
    scheduler: AsyncIOScheduler = app.state.scheduler
    hour, minute = config.calibration_update_time.split(":")
    scheduler.add_job(
        app.state.config_manager.engine.run_calibration,
        "cron",
        hour=int(hour),
        minute=int(minute),
        misfire_grace_time=300,
        id="calibration",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(_cleanup_logs(config.log_retention_days)),
        "cron",
        hour=2,
        minute=0,
        misfire_grace_time=300,
        id="cleanup",
        replace_existing=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await ensure_admin_user(session, settings.admin_username, settings.admin_password)

    app_state = AppState()
    config_manager = ConfigManager(app_state=app_state)
    await config_manager.initialize()

    app.state.app_state = app_state
    app.state.config_manager = config_manager
    app.state.scheduler = AsyncIOScheduler()
    app.state.scheduler.start()
    schedule_jobs(app, config_manager.snapshot)
    app.state.schedule_jobs = lambda config: schedule_jobs(app, config)

    yield

    if config_manager.engine:
        await config_manager.engine.stop()
    if config_manager.market_data:
        await config_manager.market_data.stop()
    app.state.scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan, title="GLFT 做市系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=get_settings().api_prefix)
