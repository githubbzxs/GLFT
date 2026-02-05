from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

import numpy as np

from app.services.grvt_client import GrvtClient


@dataclass
class CalibrationResult:
    sigma: float
    A: float
    k: float


class GLFTCalibrator:
    def __init__(
        self,
        client: GrvtClient,
        symbol: str,
        window_days: int,
        timeframe: str,
        trade_sample: int,
    ) -> None:
        self.client = client
        self.symbol = symbol
        self.window_days = window_days
        self.timeframe = timeframe
        self.trade_sample = trade_sample

    async def calibrate(self) -> CalibrationResult:
        sigma = await self._estimate_sigma()
        A, k = await self._estimate_A_k()
        return CalibrationResult(sigma=sigma, A=A, k=k)

    async def _estimate_sigma(self) -> float:
        now_ns = time.time_ns()
        start_ns = now_ns - self.window_days * 24 * 3600 * 1_000_000_000
        candles = []
        cursor = None
        while True:
            resp = await self.client.fetch_ohlcv(
                self.symbol, self.timeframe, start_ns, 1000, cursor=cursor
            )
            data = resp.get("result", [])
            candles.extend(data)
            cursor = resp.get("next")
            if not cursor or len(data) == 0:
                break
            if len(candles) > 30000:
                break
        closes = []
        for c in candles:
            close = float(Decimal(str(c.get("close", "0"))) / Decimal("1000000000"))
            if close > 0:
                closes.append(close)
        if len(closes) < 3:
            return 0.5
        returns = np.diff(np.log(np.array(closes)))
        interval_seconds = self._interval_seconds()
        sigma = float(np.std(returns) / np.sqrt(interval_seconds))
        return max(sigma, 1e-6)

    async def _estimate_A_k(self) -> tuple[float, float]:
        now_ns = time.time_ns()
        start_ns = now_ns - self.window_days * 24 * 3600 * 1_000_000_000
        trades = []
        cursor = None
        while len(trades) < self.trade_sample:
            resp = await self.client.fetch_trades(
                self.symbol,
                since_ns=start_ns,
                limit=min(1000, self.trade_sample - len(trades)),
                cursor=cursor,
            )
            data = resp.get("result", [])
            trades.extend(data)
            cursor = resp.get("next")
            if not cursor or len(data) == 0:
                break
        if len(trades) < 10:
            return 0.5, 1.5
        prices = [
            float(Decimal(str(t.get("price", "0"))) / Decimal("1000000000"))
            for t in trades
            if float(t.get("price", "0")) > 0
        ]
        if not prices:
            return 0.5, 1.5
        mid = float(np.median(np.array(prices)))
        deltas = np.abs(np.array(prices) - mid)
        max_delta = float(np.percentile(deltas, 90))
        if max_delta <= 0:
            return 0.5, 1.5
        bins = np.linspace(0, max_delta, 15)
        counts, edges = np.histogram(deltas, bins=bins)
        x = (edges[:-1] + edges[1:]) / 2
        y = np.log(counts + 1)
        coeffs = np.polyfit(x, y, 1)
        k = max(-coeffs[0], 1e-6)
        A = float(np.exp(coeffs[1]))
        return A, k

    def _interval_seconds(self) -> int:
        mapping = {
            "1m": 60,
            "3m": 180,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "2h": 7200,
            "4h": 14400,
            "6h": 21600,
            "8h": 28800,
            "12h": 43200,
            "1d": 86400,
        }
        return mapping.get(self.timeframe, 300)
