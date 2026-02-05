from __future__ import annotations

from pydantic import BaseModel


class StrategyParamsUpdate(BaseModel):
    gamma: float
    sigma: float
    A: float
    k: float
    time_horizon_seconds: int
    inventory_cap_usd: float
    order_cap_usd: float
    leverage_limit: float
    auto_tuning_enabled: bool = True


class StrategyParamsResponse(BaseModel):
    gamma: float
    sigma: float
    A: float
    k: float
    time_horizon_seconds: int
    inventory_cap_usd: float
    order_cap_usd: float
    leverage_limit: float
    auto_tuning_enabled: bool
