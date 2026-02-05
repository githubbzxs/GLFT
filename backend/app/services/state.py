from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MarketState:
    symbol: str = ""
    mid_price: float = 0.0
    best_bid: float = 0.0
    best_ask: float = 0.0
    last_update: datetime | None = None
    instrument_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class PositionState:
    size: float = 0.0
    entry_price: float = 0.0
    mark_price: float = 0.0
    unrealized_pnl: float = 0.0
    last_update: datetime | None = None


@dataclass
class EngineState:
    is_running: bool = False
    last_event: str | None = None
    cancel_timestamps: list[float] = field(default_factory=list)
    order_timestamps: list[float] = field(default_factory=list)
    open_order_ids: dict[str, str] = field(default_factory=dict)


@dataclass
class AppState:
    market: MarketState = field(default_factory=MarketState)
    position: PositionState = field(default_factory=PositionState)
    engine: EngineState = field(default_factory=EngineState)
