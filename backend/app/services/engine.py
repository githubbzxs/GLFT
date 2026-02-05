from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.calibration import GLFTCalibrator
from app.services.grvt_client import GrvtClient
from app.services.alerts import create_alert, send_email_alert
from app.services.repository import (
    get_or_create_params,
    get_or_create_risk_limits,
    record_metric,
    record_order,
    record_risk_event,
    record_trade,
    trade_exists,
    update_params,
    update_order_status,
    upsert_position,
)
from app.services.risk import RiskLimitsConfig, RiskManager
from app.services.state import AppState
from app.services.strategy_glft import GLFTParams, compute_quotes


@dataclass
class EngineConfig:
    quote_interval_ms: int
    order_duration_secs: int


@dataclass
class TunedParams:
    gamma: float
    sigma: float
    A: float
    k: float


class StrategyEngine:
    def __init__(
        self,
        state: AppState,
        client: GrvtClient,
        session_factory,
    ) -> None:
        settings = get_settings()
        self.state = state
        self.client = client
        self.session_factory = session_factory
        self.config = EngineConfig(
            quote_interval_ms=settings.quote_interval_ms,
            order_duration_secs=settings.order_duration_secs,
        )
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_quotes: tuple[float, float] | None = None
        self._last_trade_sync = 0.0
        self._last_position_sync = 0.0
        self._risk_manager: RiskManager | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self.state.engine.is_running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._running = False
        self.state.engine.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_loop(self) -> None:
        while self._running:
            await self._tick()
            await asyncio.sleep(self.config.quote_interval_ms / 1000)

    async def _tick(self) -> None:
        settings = get_settings()
        async with self.session_factory() as session:
            await self._ensure_risk_manager(session)
            params = await get_or_create_params(session)
            limits = await get_or_create_risk_limits(session)
            self._risk_manager.limits = RiskLimitsConfig(
                max_inventory_usd=limits.max_inventory_usd,
                max_order_usd=limits.max_order_usd,
                max_leverage=limits.max_leverage,
                max_cancel_rate_per_min=limits.max_cancel_rate_per_min,
                max_order_rate_per_min=limits.max_order_rate_per_min,
            )

            if time.time() - self._last_position_sync > 2:
                await self._refresh_position(session)
                self._last_position_sync = time.time()
            if time.time() - self._last_trade_sync > 10:
                await self._sync_trades(session)
                self._last_trade_sync = time.time()

            mid = await self._get_mid_price()
            if mid <= 0:
                return
            inventory_btc = self.state.position.size
            inventory_usd = inventory_btc * mid

            order_size = max(params.order_cap_usd / mid, 0.0)
            if order_size <= 0:
                return
            order_size = self.client.round_size(self.state.market.symbol, order_size)

            leverage = await self._estimate_leverage(mid, order_size)
            allowed, reason = self._risk_manager.check_limits(
                inventory_usd=inventory_usd,
                order_usd=params.order_cap_usd,
                leverage=leverage,
            )
            if not allowed:
                self.state.engine.last_event = reason
                await record_risk_event(session, "WARN", "RISK_BLOCK", reason or "")
                await create_alert(session, "WARN", f"风控触发：{reason}")
                send_email_alert("GLFT 风控触发", f"风控触发：{reason}")
                return

            tuned = self._apply_auto_tuning(params, inventory_usd)
            glft_params = GLFTParams(
                gamma=tuned.gamma,
                sigma=tuned.sigma,
                A=tuned.A,
                k=tuned.k,
                order_size=order_size,
            )
            bid, ask, spread = compute_quotes(mid, inventory_btc, glft_params)

            bid = self.client.round_price(self.state.market.symbol, bid)
            ask = self.client.round_price(self.state.market.symbol, ask)

            if bid <= 0 or ask <= 0 or bid >= ask:
                return

            await record_metric(session, "spread", float(spread))
            await self._place_quotes(session, bid, ask, order_size)

    async def _ensure_risk_manager(self, session: AsyncSession) -> None:
        if self._risk_manager:
            return
        limits = await get_or_create_risk_limits(session)
        self._risk_manager = RiskManager(
            RiskLimitsConfig(
                max_inventory_usd=limits.max_inventory_usd,
                max_order_usd=limits.max_order_usd,
                max_leverage=limits.max_leverage,
                max_cancel_rate_per_min=limits.max_cancel_rate_per_min,
                max_order_rate_per_min=limits.max_order_rate_per_min,
            )
        )

    async def _get_mid_price(self) -> float:
        if self.state.market.mid_price > 0:
            return self.state.market.mid_price
        ticker = await self.client.fetch_ticker(self.state.market.symbol)
        mid_raw = ticker.get("mid_price") or ticker.get("mark_price") or ticker.get("last_price")
        if not mid_raw:
            return 0.0
        mid = self.client.normalize_price(mid_raw)
        self.state.market.mid_price = mid
        return mid

    async def _refresh_position(self, session: AsyncSession) -> None:
        positions = await self.client.fetch_positions(self.state.market.symbol)
        if not positions:
            return
        pos = positions[0]
        size = self.client.normalize_size(self.state.market.symbol, pos.get("size", 0))
        entry = self.client.normalize_price(pos.get("entry_price", 0))
        mark = self.client.normalize_price(pos.get("mark_price", 0))
        pnl = float(pos.get("unrealized_pnl", 0))
        self.state.position.size = size
        self.state.position.entry_price = entry
        self.state.position.mark_price = mark
        self.state.position.unrealized_pnl = pnl
        await upsert_position(
            session,
            {
                "symbol": self.state.market.symbol,
                "size": size,
                "entry_price": entry,
                "mark_price": mark,
                "unrealized_pnl": pnl,
            },
        )

    async def _sync_trades(self, session: AsyncSession) -> None:
        # 仅同步最近交易，避免过载
        try:
            trades_resp = await self.client.rest.fetch_my_trades(
                symbol=self.state.market.symbol, limit=50
            )
            trades = trades_resp.get("result", [])
            for t in trades:
                trade_id = str(t.get("trade_id"))
                if not trade_id or await trade_exists(session, trade_id):
                    continue
                price = self.client.normalize_price(t.get("price", 0))
                size = self.client.normalize_size(self.state.market.symbol, t.get("size", 0))
                side = "buy" if t.get("is_taker_buyer") else "sell"
                await record_trade(
                    session,
                    {
                        "trade_id": trade_id,
                        "symbol": self.state.market.symbol,
                        "side": side,
                        "price": price,
                        "size": size,
                        "fee": 0,
                        "realized_pnl": 0,
                    },
                )
        except Exception:
            return

    async def _place_quotes(
        self, session: AsyncSession, bid: float, ask: float, size: float
    ) -> None:
        last_bid, last_ask = self._last_quotes or (0.0, 0.0)
        if abs(bid - last_bid) < 1e-9 and abs(ask - last_ask) < 1e-9:
            return
        # 先撤旧单
        for side_key in ["bid", "ask"]:
            order_id = self.state.engine.open_order_ids.get(side_key)
            if order_id:
                try:
                    await self.client.cancel_order(order_id)
                    await update_order_status(session, order_id, "canceled")
                    self._risk_manager.record_cancel()
                except Exception:
                    pass
                self.state.engine.open_order_ids.pop(side_key, None)

        try:
            bid_order = await self.client.create_limit_order(
                self.state.market.symbol,
                "buy",
                size,
                bid,
                post_only=True,
                order_duration_secs=self.config.order_duration_secs,
            )
            bid_id = str(bid_order.get("order_id", ""))
            if bid_id:
                self.state.engine.open_order_ids["bid"] = bid_id
                self._risk_manager.record_order()
                await record_order(
                    session,
                    {
                        "order_id": bid_id,
                        "symbol": self.state.market.symbol,
                        "side": "buy",
                        "price": bid,
                        "size": size,
                        "status": "open",
                    },
                )
        except Exception:
            await record_risk_event(session, "WARN", "ORDER_FAIL", "买单提交失败")
            await create_alert(session, "WARN", "买单提交失败")
            send_email_alert("GLFT 下单失败", "买单提交失败")

        try:
            ask_order = await self.client.create_limit_order(
                self.state.market.symbol,
                "sell",
                size,
                ask,
                post_only=True,
                order_duration_secs=self.config.order_duration_secs,
            )
            ask_id = str(ask_order.get("order_id", ""))
            if ask_id:
                self.state.engine.open_order_ids["ask"] = ask_id
                self._risk_manager.record_order()
                await record_order(
                    session,
                    {
                        "order_id": ask_id,
                        "symbol": self.state.market.symbol,
                        "side": "sell",
                        "price": ask,
                        "size": size,
                        "status": "open",
                    },
                )
        except Exception:
            await record_risk_event(session, "WARN", "ORDER_FAIL", "卖单提交失败")
            await create_alert(session, "WARN", "卖单提交失败")
            send_email_alert("GLFT 下单失败", "卖单提交失败")
        self._last_quotes = (bid, ask)

    async def _estimate_leverage(self, mid_price: float, order_size: float) -> float:
        try:
            balance = await self.client.fetch_balance()
            usdt = balance.get("USDT", {}).get("free") or balance.get("free", {}).get("USDT")
            equity = float(usdt) if usdt else 1.0
        except Exception:
            equity = 1.0
        notional = mid_price * order_size
        return notional / max(equity, 1e-6)

    def _apply_auto_tuning(self, params, inventory_usd: float) -> TunedParams:
        gamma = params.gamma
        if params.auto_tuning_enabled:
            inv_ratio = min(abs(inventory_usd) / max(params.inventory_cap_usd, 1e-6), 1.0)
            gamma = params.gamma * (1.0 + inv_ratio)
        return TunedParams(gamma=gamma, sigma=params.sigma, A=params.A, k=params.k)

    async def run_calibration(self) -> None:
        settings = get_settings()
        calibrator = GLFTCalibrator(
            client=self.client,
            symbol=self.state.market.symbol,
            window_days=settings.calibration_window_days,
            timeframe=settings.calibration_timeframe,
            trade_sample=settings.calibration_trade_sample,
        )
        result = await calibrator.calibrate()
        async with self.session_factory() as session:
            await record_metric(session, "sigma", result.sigma)
            await record_metric(session, "A", result.A)
            await record_metric(session, "k", result.k)
            params = await get_or_create_params(session)
            await update_params(
                session,
                {
                    "sigma": result.sigma,
                    "A": result.A,
                    "k": result.k,
                    "time_horizon_seconds": params.time_horizon_seconds,
                    "inventory_cap_usd": params.inventory_cap_usd,
                    "order_cap_usd": params.order_cap_usd,
                    "leverage_limit": params.leverage_limit,
                    "gamma": params.gamma,
                    "auto_tuning_enabled": params.auto_tuning_enabled,
                },
            )
