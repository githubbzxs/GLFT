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
from app.services.engine import StrategyEngine
from app.services.grvt_client import GrvtClient
from app.services.market_data import MarketDataService
from app.services.repository import ensure_admin_user, get_latest_api_keys
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await ensure_admin_user(session, settings.admin_username, settings.admin_password)
    async with AsyncSessionLocal() as session:
        record = await get_latest_api_keys(session)
        api_key = settings.grvt_api_key
        private_key = settings.grvt_private_key
        sub_account_id = settings.grvt_sub_account_id
        if record:
            api_key = decrypt_text(record.encrypted_api_key)
            private_key = decrypt_text(record.encrypted_private_key)
            sub_account_id = record.sub_account_id
    client = GrvtClient(
        env=settings.grvt_env,
        api_key=api_key,
        private_key=private_key,
        sub_account_id=sub_account_id,
    )
    await client.load_markets()
    symbol = settings.grvt_symbol
    if symbol not in client._instruments:
        symbol = client.resolve_symbol("BTC")

    app_state = AppState()
    app_state.market.symbol = symbol
    inst = client.get_instrument(symbol)
    if inst:
        app_state.market.instrument_info = {
            "tick_size": float(inst.tick_size),
            "min_size": float(inst.min_size),
            "base_decimals": inst.base_decimals,
        }

    market_data = MarketDataService(client=client, state=app_state)
    engine_manager = StrategyEngine(state=app_state, client=client, session_factory=AsyncSessionLocal)
    app.state.app_state = app_state
    app.state.engine_manager = engine_manager

    await market_data.start()

    scheduler = AsyncIOScheduler()
    hour, minute = settings.calibration_update_time.split(":")
    scheduler.add_job(
        engine_manager.run_calibration,
        "cron",
        hour=int(hour),
        minute=int(minute),
        misfire_grace_time=300,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(_cleanup_logs(settings.log_retention_days)),
        "cron",
        hour=2,
        minute=0,
        misfire_grace_time=300,
    )
    scheduler.start()

    yield

    await engine_manager.stop()
    scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan, title="GLFT 做市系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=get_settings().api_prefix)
