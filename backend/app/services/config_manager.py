from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.db.session import AsyncSessionLocal
from app.services.alerts import AlertConfig
from app.services.engine import StrategyEngine
from app.services.grvt_client import GrvtClient
from app.services.market_data import MarketDataService
from app.core.crypto import decrypt_text, encrypt_text
from app.services.repository import (
    decrypt_smtp_password,
    get_current_app_config,
    get_latest_api_keys,
    get_or_create_app_config,
)
from app.services.state import AppState


@dataclass
class ConfigSnapshot:
    grvt_env: str
    grvt_symbol: str
    quote_interval_ms: int
    order_duration_secs: int
    calibration_window_days: int
    calibration_timeframe: str
    calibration_update_time: str
    calibration_trade_sample: int
    log_retention_days: int
    alert_email_to: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_tls: bool


class ConfigManager:
    def __init__(self, app_state: AppState) -> None:
        self.app_state = app_state
        self.settings: Settings = get_settings()
        self.snapshot: ConfigSnapshot | None = None
        self.client: GrvtClient | None = None
        self.market_data: MarketDataService | None = None
        self.engine: StrategyEngine | None = None

    async def initialize(self) -> None:
        async with AsyncSessionLocal() as session:
            config = await get_or_create_app_config(session, self._defaults())
            keys = await get_latest_api_keys(session)
            api_key = self.settings.grvt_api_key
            private_key = self.settings.grvt_private_key
            sub_account_id = self.settings.grvt_sub_account_id
            if keys:
                api_key = decrypt_text(keys.encrypted_api_key)
                private_key = decrypt_text(keys.encrypted_private_key)
                sub_account_id = keys.sub_account_id
            await self._build_services(config, api_key, private_key, sub_account_id)
            self.snapshot = self._to_snapshot(config)

    async def apply_config(self) -> None:
        async with AsyncSessionLocal() as session:
            config = await get_current_app_config(session)
            if not config:
                return
            snapshot = self._to_snapshot(config)
            need_reload = self.snapshot is None or (
                snapshot.grvt_env != self.snapshot.grvt_env
                or snapshot.grvt_symbol != self.snapshot.grvt_symbol
            )
            if need_reload:
                await self.reload_client()
            else:
                if self.engine:
                    self.engine.apply_runtime_config(
                        quote_interval_ms=snapshot.quote_interval_ms,
                        order_duration_secs=snapshot.order_duration_secs,
                        alert_config=self._alert_config(snapshot),
                    )
            self.snapshot = snapshot

    async def reload_client(self) -> None:
        async with AsyncSessionLocal() as session:
            config = await get_current_app_config(session)
            if not config:
                return
            keys = await get_latest_api_keys(session)
            api_key = self.settings.grvt_api_key
            private_key = self.settings.grvt_private_key
            sub_account_id = self.settings.grvt_sub_account_id
            if keys:
                api_key = decrypt_text(keys.encrypted_api_key)
                private_key = decrypt_text(keys.encrypted_private_key)
                sub_account_id = keys.sub_account_id
            await self._rebuild_services(config, api_key, private_key, sub_account_id)
            self.snapshot = self._to_snapshot(config)

    async def _rebuild_services(
        self, config, api_key: str, private_key: str, sub_account_id: str
    ) -> None:
        was_running = self.engine._running if self.engine else False
        if self.engine:
            await self.engine.stop()
        if self.market_data:
            await self.market_data.stop()
        await self._build_services(config, api_key, private_key, sub_account_id)
        if was_running and self.engine:
            await self.engine.start()

    async def _build_services(
        self, config, api_key: str, private_key: str, sub_account_id: str
    ) -> None:
        self.client = GrvtClient(
            env=config.grvt_env,
            api_key=api_key,
            private_key=private_key,
            sub_account_id=sub_account_id,
        )
        await self.client.load_markets()
        symbol = config.grvt_symbol
        if symbol not in self.client._instruments:
            symbol = self.client.resolve_symbol("BTC")
        self.app_state.market.symbol = symbol
        inst = self.client.get_instrument(symbol)
        if inst:
            self.app_state.market.instrument_info = {
                "tick_size": float(inst.tick_size),
                "min_size": float(inst.min_size),
                "base_decimals": inst.base_decimals,
            }
        self.market_data = MarketDataService(client=self.client, state=self.app_state)
        await self.market_data.start()
        self.engine = StrategyEngine(state=self.app_state, client=self.client, session_factory=AsyncSessionLocal)
        snapshot = self._to_snapshot(config)
        self.engine.apply_runtime_config(
            quote_interval_ms=snapshot.quote_interval_ms,
            order_duration_secs=snapshot.order_duration_secs,
            alert_config=self._alert_config(snapshot),
        )

    def _defaults(self) -> dict:
        return {
            "grvt_env": self.settings.grvt_env,
            "grvt_symbol": self.settings.grvt_symbol,
            "quote_interval_ms": self.settings.quote_interval_ms,
            "order_duration_secs": self.settings.order_duration_secs,
            "calibration_window_days": self.settings.calibration_window_days,
            "calibration_timeframe": self.settings.calibration_timeframe,
            "calibration_update_time": self.settings.calibration_update_time,
            "calibration_trade_sample": self.settings.calibration_trade_sample,
            "log_retention_days": self.settings.log_retention_days,
            "alert_email_to": self.settings.alert_email_to,
            "smtp_host": self.settings.smtp_host,
            "smtp_port": self.settings.smtp_port,
            "smtp_user": self.settings.smtp_user,
            "encrypted_smtp_password": encrypt_text(self.settings.smtp_password)
            if self.settings.smtp_password
            else "",
            "smtp_tls": self.settings.smtp_tls,
        }

    def _to_snapshot(self, config) -> ConfigSnapshot:
        return ConfigSnapshot(
            grvt_env=config.grvt_env,
            grvt_symbol=config.grvt_symbol,
            quote_interval_ms=config.quote_interval_ms,
            order_duration_secs=config.order_duration_secs,
            calibration_window_days=config.calibration_window_days,
            calibration_timeframe=config.calibration_timeframe,
            calibration_update_time=config.calibration_update_time,
            calibration_trade_sample=config.calibration_trade_sample,
            log_retention_days=config.log_retention_days,
            alert_email_to=config.alert_email_to,
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            smtp_user=config.smtp_user,
            smtp_password=decrypt_smtp_password(config),
            smtp_tls=config.smtp_tls,
        )

    def _alert_config(self, snapshot: ConfigSnapshot) -> AlertConfig:
        return AlertConfig(
            alert_email_to=snapshot.alert_email_to,
            smtp_host=snapshot.smtp_host,
            smtp_port=snapshot.smtp_port,
            smtp_user=snapshot.smtp_user,
            smtp_password=snapshot.smtp_password,
            smtp_tls=snapshot.smtp_tls,
        )
