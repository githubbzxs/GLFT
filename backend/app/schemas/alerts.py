from __future__ import annotations

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    level: str
    message: str
    is_read: bool
