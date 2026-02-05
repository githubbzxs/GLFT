from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from app.services.grvt_client import GrvtClient
from app.services.state import AppState


class MarketDataService:
    def __init__(self, client: GrvtClient, state: AppState) -> None:
        self.client = client
        self.state = state
        self._poll_task: asyncio.Task | None = None

    async def start(self) -> None:
        asyncio.create_task(self.client.connect_ws())
        await asyncio.sleep(1)
        await self.client.ws.subscribe(
            "ticker.s",
            self._on_ticker,
            params={"instrument": self.state.market.symbol, "rate": "500"},
        )
        self._poll_task = asyncio.create_task(self._poll_fallback())

    async def _on_ticker(self, message: dict) -> None:
        data = message.get("result") or message.get("data") or message.get("payload") or message
        if not isinstance(data, dict):
            return
        mid_raw = data.get("mid_price") or data.get("mark_price") or data.get("last_price")
        bid_raw = data.get("best_bid_price")
        ask_raw = data.get("best_ask_price")
        if mid_raw:
            self.state.market.mid_price = self.client.normalize_price(mid_raw)
        if bid_raw:
            self.state.market.best_bid = self.client.normalize_price(bid_raw)
        if ask_raw:
            self.state.market.best_ask = self.client.normalize_price(ask_raw)
        self.state.market.last_update = datetime.now(timezone.utc)

    async def _poll_fallback(self) -> None:
        while True:
            try:
                ticker = await self.client.fetch_ticker(self.state.market.symbol)
                mid_raw = ticker.get("mid_price") or ticker.get("mark_price") or ticker.get("last_price")
                if mid_raw:
                    self.state.market.mid_price = self.client.normalize_price(mid_raw)
                    self.state.market.last_update = datetime.now(timezone.utc)
            except Exception:
                pass
            await asyncio.sleep(1)
