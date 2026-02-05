from __future__ import annotations

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    mid_price: float
    inventory_btc: float
    inventory_usd: float
    unrealized_pnl: float
    open_orders: int
    spread: float
    cancel_rate_per_min: float
    order_rate_per_min: float
