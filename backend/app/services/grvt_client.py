from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from pysdk.grvt_ccxt_env import GrvtEnv
from pysdk.grvt_ccxt_pro import GrvtCcxtPro
from pysdk.grvt_ccxt_ws import GrvtCcxtWS


PRICE_MULTIPLIER = Decimal("1000000000")


@dataclass
class GrvtInstrument:
    symbol: str
    base: str
    quote: str
    kind: str
    tick_size: Decimal
    min_size: Decimal
    base_decimals: int


class GrvtClient:
    def __init__(
        self,
        env: str,
        api_key: str,
        private_key: str,
        sub_account_id: str,
        loop: asyncio.AbstractEventLoop | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.env = GrvtEnv(env)
        self.parameters = {
            "api_key": api_key,
            "private_key": private_key,
            "trading_account_id": sub_account_id,
        }
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
        self.rest = GrvtCcxtPro(env=self.env, logger=self.logger, parameters=self.parameters)
        self.ws = GrvtCcxtWS(env=self.env, loop=loop, logger=self.logger, parameters=self.parameters)
        self._markets_loaded = False
        self._instruments: dict[str, GrvtInstrument] = {}

    async def connect_ws(self) -> None:
        await self.ws.connect_all_channels()

    async def load_markets(self) -> dict[str, GrvtInstrument]:
        markets = await self.rest.fetch_markets(params={"kind": "PERPETUAL"})
        instruments: dict[str, GrvtInstrument] = {}
        for m in markets:
            symbol = str(m.get("instrument"))
            if not symbol:
                continue
            tick_size = Decimal(str(m.get("tick_size", "0.5")))
            min_size = Decimal(str(m.get("min_size", "0.001")))
            base_decimals = int(m.get("base_decimals", 8))
            instruments[symbol] = GrvtInstrument(
                symbol=symbol,
                base=str(m.get("base", "")),
                quote=str(m.get("quote", "")),
                kind=str(m.get("kind", "")),
                tick_size=tick_size,
                min_size=min_size,
                base_decimals=base_decimals,
            )
        self._instruments = instruments
        self._markets_loaded = True
        return instruments

    def resolve_symbol(self, prefer: str = "BTC") -> str:
        if not self._markets_loaded:
            raise RuntimeError("市场未加载")
        for symbol, inst in self._instruments.items():
            if inst.base == prefer and inst.kind == "PERPETUAL":
                return symbol
        return next(iter(self._instruments.keys()))

    def get_instrument(self, symbol: str) -> GrvtInstrument | None:
        return self._instruments.get(symbol)

    async def fetch_ticker(self, symbol: str) -> dict:
        return await self.rest.fetch_ticker(symbol)

    async def fetch_order_book(self, symbol: str, depth: int = 10) -> dict:
        return await self.rest.fetch_order_book(symbol, depth)

    async def fetch_positions(self, symbol: str) -> list[dict]:
        return await self.rest.fetch_positions([symbol])

    async def fetch_balance(self) -> dict:
        return await self.rest.fetch_balance()

    async def fetch_trades(self, symbol: str, since_ns: int, limit: int, cursor: str | None = None) -> dict:
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        return await self.rest.fetch_trades(symbol, since_ns, limit, params)

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since_ns: int,
        limit: int,
        cursor: str | None = None,
        end_time: int | None = None,
    ) -> dict:
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if end_time:
            params["end_time"] = end_time
        return await self.rest.fetch_ohlcv(symbol, timeframe, since_ns, limit, params=params)

    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        post_only: bool = True,
        reduce_only: bool = False,
        client_order_id: int | None = None,
        order_duration_secs: int | None = None,
    ) -> dict:
        params: dict[str, Any] = {
            "post_only": post_only,
            "reduce_only": reduce_only,
        }
        if client_order_id:
            params["client_order_id"] = client_order_id
        if order_duration_secs:
            params["order_duration_secs"] = order_duration_secs
        return await self.rest.create_order(symbol, "limit", side, amount, price, params)

    async def cancel_order(self, order_id: str) -> dict:
        return await self.rest.cancel_order(order_id)

    async def cancel_all_orders(self, symbol: str) -> bool:
        params = {"base": symbol.split("_")[0], "quote": symbol.split("_")[1] if "_" in symbol else "USDT"}
        return await self.rest.cancel_all_orders(params)

    @staticmethod
    def normalize_price(raw_price: str | int | float) -> float:
        return float(Decimal(str(raw_price)) / PRICE_MULTIPLIER)

    def normalize_size(self, symbol: str, raw_size: str | int | float) -> float:
        inst = self.get_instrument(symbol)
        if not inst:
            return float(raw_size)
        size = Decimal(str(raw_size)) / Decimal(10 ** inst.base_decimals)
        return float(size)

    def round_price(self, symbol: str, price: float) -> float:
        inst = self.get_instrument(symbol)
        if not inst:
            return price
        tick = inst.tick_size
        rounded = (Decimal(str(price)) // tick) * tick
        return float(rounded)

    def round_size(self, symbol: str, size: float) -> float:
        inst = self.get_instrument(symbol)
        if not inst:
            return size
        step = Decimal(10) ** (-inst.base_decimals)
        rounded = (Decimal(str(size)) // step) * step
        if rounded < inst.min_size:
            return float(inst.min_size)
        return float(rounded)

    async def wait_for_ready(self, timeout: int = 30) -> None:
        start = time.time()
        while not self._markets_loaded:
            if time.time() - start > timeout:
                raise TimeoutError("市场加载超时")
            await asyncio.sleep(0.5)
