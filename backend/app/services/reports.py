from __future__ import annotations

import csv
import io

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


async def generate_pnl_report(session: AsyncSession) -> str:
    trades_result = await session.execute(select(models.Trade).order_by(models.Trade.created_at.desc()))
    trades = trades_result.scalars().all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["trade_id", "symbol", "side", "price", "size", "fee", "realized_pnl", "created_at"])
    for t in trades:
        writer.writerow([t.trade_id, t.symbol, t.side, t.price, t.size, t.fee, t.realized_pnl, t.created_at])
    return output.getvalue()
