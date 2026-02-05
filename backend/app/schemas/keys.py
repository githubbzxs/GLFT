from __future__ import annotations

from pydantic import BaseModel


class ApiKeyUpdate(BaseModel):
    api_key: str
    private_key: str
    sub_account_id: str
    ip_whitelist: str | None = ""


class ApiKeyResponse(BaseModel):
    sub_account_id: str
    ip_whitelist: str | None = ""
