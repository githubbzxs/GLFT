from __future__ import annotations

from pydantic import BaseModel


class RiskLimitsUpdate(BaseModel):
    max_inventory_usd: float
    max_order_usd: float
    max_leverage: float
    max_cancel_rate_per_min: float
    max_order_rate_per_min: float


class RiskStatusResponse(BaseModel):
    is_trading: bool
    last_event: str | None = None
    cancel_rate_per_min: float
    order_rate_per_min: float
