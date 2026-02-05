from __future__ import annotations

from pydantic import BaseModel


class OrderResponse(BaseModel):
    order_id: str
    symbol: str
    side: str
    price: float
    size: float
    status: str


class TradeResponse(BaseModel):
    trade_id: str
    symbol: str
    side: str
    price: float
    size: float
    fee: float
    realized_pnl: float


class PositionResponse(BaseModel):
    symbol: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
