from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_text, encrypt_text
from app.core.security import hash_password, verify_password
from app.db import models


async def ensure_admin_user(session: AsyncSession, username: str, password: str) -> None:
    result = await session.execute(select(models.User).where(models.User.username == username))
    user = result.scalar_one_or_none()
    if user:
        if password and not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
            await session.commit()
        return
    session.add(models.User(username=username, password_hash=hash_password(password)))
    await session.commit()


async def get_or_create_params(session: AsyncSession) -> models.StrategyParams:
    result = await session.execute(select(models.StrategyParams).order_by(models.StrategyParams.id.desc()))
    params = result.scalar_one_or_none()
    if params:
        return params
    params = models.StrategyParams(
        gamma=0.1,
        sigma=0.5,
        A=0.5,
        k=1.5,
        time_horizon_seconds=3600,
        inventory_cap_usd=100,
        order_cap_usd=20,
        leverage_limit=50,
        auto_tuning_enabled=True,
    )
    session.add(params)
    await session.commit()
    await session.refresh(params)
    return params


async def update_params(session: AsyncSession, payload: dict) -> models.StrategyParams:
    result = await session.execute(select(models.StrategyParams).order_by(models.StrategyParams.id.desc()))
    params = result.scalar_one_or_none()
    if not params:
        params = await get_or_create_params(session)
    for key, value in payload.items():
        setattr(params, key, value)
    await session.commit()
    await session.refresh(params)
    return params


async def get_or_create_risk_limits(session: AsyncSession) -> models.RiskLimits:
    result = await session.execute(select(models.RiskLimits).order_by(models.RiskLimits.id.desc()))
    limits = result.scalar_one_or_none()
    if limits:
        return limits
    limits = models.RiskLimits(
        max_inventory_usd=100,
        max_order_usd=20,
        max_leverage=50,
        max_cancel_rate_per_min=0.85,
        max_order_rate_per_min=120,
    )
    session.add(limits)
    await session.commit()
    await session.refresh(limits)
    return limits


async def update_risk_limits(session: AsyncSession, payload: dict) -> models.RiskLimits:
    result = await session.execute(select(models.RiskLimits).order_by(models.RiskLimits.id.desc()))
    limits = result.scalar_one_or_none()
    if not limits:
        limits = await get_or_create_risk_limits(session)
    for key, value in payload.items():
        setattr(limits, key, value)
    await session.commit()
    await session.refresh(limits)
    return limits


async def save_api_keys(
    session: AsyncSession,
    encrypted_api_key: str,
    encrypted_private_key: str,
    sub_account_id: str,
    ip_whitelist: str,
) -> models.ApiKeyRecord:
    result = await session.execute(select(models.ApiKeyRecord).order_by(models.ApiKeyRecord.id.desc()))
    record = result.scalar_one_or_none()
    if record:
        record.encrypted_api_key = encrypted_api_key
        record.encrypted_private_key = encrypted_private_key
        record.sub_account_id = sub_account_id
        record.ip_whitelist = ip_whitelist
    else:
        record = models.ApiKeyRecord(
            encrypted_api_key=encrypted_api_key,
            encrypted_private_key=encrypted_private_key,
            sub_account_id=sub_account_id,
            ip_whitelist=ip_whitelist,
        )
        session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def get_latest_api_keys(session: AsyncSession) -> models.ApiKeyRecord | None:
    result = await session.execute(select(models.ApiKeyRecord).order_by(models.ApiKeyRecord.id.desc()))
    return result.scalar_one_or_none()


async def record_order(session: AsyncSession, payload: dict) -> None:
    session.add(models.Order(**payload))
    await session.commit()


async def record_trade(session: AsyncSession, payload: dict) -> None:
    session.add(models.Trade(**payload))
    await session.commit()


async def upsert_position(session: AsyncSession, payload: dict) -> None:
    result = await session.execute(
        select(models.Position).where(models.Position.symbol == payload["symbol"])
    )
    pos = result.scalar_one_or_none()
    if pos:
        for key, value in payload.items():
            setattr(pos, key, value)
    else:
        session.add(models.Position(**payload))
    await session.commit()


async def record_risk_event(session: AsyncSession, level: str, event_type: str, message: str) -> None:
    session.add(models.RiskEvent(level=level, event_type=event_type, message=message))
    await session.commit()


async def record_metric(session: AsyncSession, name: str, value: float) -> None:
    session.add(models.SystemMetric(name=name, value=value))
    await session.commit()


async def update_order_status(session: AsyncSession, order_id: str, status: str) -> None:
    await session.execute(
        update(models.Order).where(models.Order.order_id == order_id).values(status=status)
    )
    await session.commit()


async def trade_exists(session: AsyncSession, trade_id: str) -> bool:
    result = await session.execute(
        select(models.Trade.id).where(models.Trade.trade_id == trade_id)
    )
    return result.scalar_one_or_none() is not None


async def get_or_create_app_config(session: AsyncSession, defaults: dict) -> models.AppConfig:
    result = await session.execute(select(models.AppConfig).order_by(models.AppConfig.id.desc()))
    config = result.scalar_one_or_none()
    if config:
        return config
    config = models.AppConfig(**defaults)
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return config


async def update_app_config(session: AsyncSession, payload: dict) -> models.AppConfig:
    result = await session.execute(select(models.AppConfig).order_by(models.AppConfig.id.desc()))
    config = result.scalar_one_or_none()
    if not config:
        config = models.AppConfig()
        session.add(config)
    smtp_password = payload.pop("smtp_password", "")
    for key, value in payload.items():
        setattr(config, key, value)
    if smtp_password:
        config.encrypted_smtp_password = encrypt_text(smtp_password)
    await session.commit()
    await session.refresh(config)
    return config


async def get_current_app_config(session: AsyncSession) -> models.AppConfig | None:
    result = await session.execute(select(models.AppConfig).order_by(models.AppConfig.id.desc()))
    return result.scalar_one_or_none()


def app_config_to_response(config: models.AppConfig) -> dict:
    return {
        "grvt_env": config.grvt_env,
        "grvt_symbol": config.grvt_symbol,
        "quote_interval_ms": config.quote_interval_ms,
        "order_duration_secs": config.order_duration_secs,
        "calibration_window_days": config.calibration_window_days,
        "calibration_timeframe": config.calibration_timeframe,
        "calibration_update_time": config.calibration_update_time,
        "calibration_trade_sample": config.calibration_trade_sample,
        "log_retention_days": config.log_retention_days,
        "alert_email_to": config.alert_email_to,
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "smtp_user": config.smtp_user,
        "smtp_password_set": bool(config.encrypted_smtp_password),
        "smtp_tls": config.smtp_tls,
    }


def decrypt_smtp_password(config: models.AppConfig) -> str:
    if not config.encrypted_smtp_password:
        return ""
    return decrypt_text(config.encrypted_smtp_password)
