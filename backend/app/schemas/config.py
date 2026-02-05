from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AppConfigUpdate(BaseModel):
    grvt_env: str = Field(min_length=2)
    grvt_symbol: str = Field(min_length=3)

    quote_interval_ms: int = Field(ge=50, le=5000)
    order_duration_secs: int = Field(ge=5, le=3600)

    calibration_window_days: int = Field(ge=1, le=120)
    calibration_timeframe: str
    calibration_update_time: str
    calibration_trade_sample: int = Field(ge=100, le=20000)

    log_retention_days: int = Field(ge=1, le=365)

    alert_email_to: str = ""
    smtp_host: str = ""
    smtp_port: int = Field(ge=1, le=65535)
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = True

    @field_validator("calibration_update_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("时间格式应为 HH:MM")
        hour, minute = int(parts[0]), int(parts[1])
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("时间格式应为 HH:MM")
        return v


class AppConfigResponse(BaseModel):
    grvt_env: str
    grvt_symbol: str

    quote_interval_ms: int
    order_duration_secs: int

    calibration_window_days: int
    calibration_timeframe: str
    calibration_update_time: str
    calibration_trade_sample: int

    log_retention_days: int

    alert_email_to: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password_set: bool
    smtp_tls: bool
