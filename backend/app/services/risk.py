from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass


@dataclass
class RiskLimitsConfig:
    max_inventory_usd: float
    max_order_usd: float
    max_leverage: float
    max_cancel_rate_per_min: float
    max_order_rate_per_min: float


class RiskManager:
    def __init__(self, limits: RiskLimitsConfig) -> None:
        self.limits = limits
        self._cancel_ts = deque()
        self._order_ts = deque()
        self.last_event: str | None = None
        self.is_trading = True

    def record_cancel(self) -> None:
        now = time.time()
        self._cancel_ts.append(now)
        self._cleanup(self._cancel_ts)

    def record_order(self) -> None:
        now = time.time()
        self._order_ts.append(now)
        self._cleanup(self._order_ts)

    def _cleanup(self, dq: deque) -> None:
        cutoff = time.time() - 60
        while dq and dq[0] < cutoff:
            dq.popleft()

    def cancel_rate_per_min(self) -> float:
        self._cleanup(self._cancel_ts)
        self._cleanup(self._order_ts)
        orders = max(len(self._order_ts), 1)
        return float(len(self._cancel_ts)) / orders

    def order_rate_per_min(self) -> float:
        self._cleanup(self._order_ts)
        return float(len(self._order_ts))

    def check_limits(
        self, inventory_usd: float, order_usd: float, leverage: float
    ) -> tuple[bool, str | None]:
        if abs(inventory_usd) > self.limits.max_inventory_usd:
            return False, "库存超限"
        if order_usd > self.limits.max_order_usd:
            return False, "单笔超限"
        if leverage > self.limits.max_leverage:
            return False, "杠杆超限"
        if self.cancel_rate_per_min() > self.limits.max_cancel_rate_per_min:
            return False, "撤单率超限"
        if self.order_rate_per_min() > self.limits.max_order_rate_per_min:
            return False, "下单频率超限"
        return True, None
