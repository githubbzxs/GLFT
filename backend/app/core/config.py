from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = Field(default="prod", alias="APP_ENV")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    database_url: str = Field(
        default="postgresql+asyncpg://glft:glft@localhost:5432/glft",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(default="please-change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=480, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    app_encryption_key: str = Field(default="please-generate-a-fernet-key", alias="APP_ENCRYPTION_KEY")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="change-this-password", alias="ADMIN_PASSWORD")

    grvt_env: str = Field(default="prod", alias="GRVT_ENV")
    grvt_api_key: str = Field(default="", alias="GRVT_API_KEY")
    grvt_private_key: str = Field(default="", alias="GRVT_PRIVATE_KEY")
    grvt_sub_account_id: str = Field(default="", alias="GRVT_SUB_ACCOUNT_ID")
    grvt_symbol: str = Field(default="BTC_USDT_Perp", alias="GRVT_SYMBOL")

    quote_interval_ms: int = Field(default=250, alias="QUOTE_INTERVAL_MS")
    order_duration_secs: int = Field(default=10, alias="ORDER_DURATION_SECS")
    time_horizon_seconds: int = Field(default=3600, alias="TIME_HORIZON_SECONDS")

    inventory_cap_usd: float = Field(default=100, alias="INVENTORY_CAP_USD")
    order_cap_usd: float = Field(default=20, alias="ORDER_CAP_USD")
    leverage_limit: float = Field(default=50, alias="LEVERAGE_LIMIT")
    max_cancel_rate_per_min: float = Field(default=0.85, alias="MAX_CANCEL_RATE_PER_MIN")
    max_order_rate_per_min: float = Field(default=120, alias="MAX_ORDER_RATE_PER_MIN")

    calibration_window_days: int = Field(default=30, alias="CALIBRATION_WINDOW_DAYS")
    calibration_timeframe: str = Field(default="5m", alias="CALIBRATION_TIMEFRAME")
    calibration_update_time: str = Field(default="00:10", alias="CALIBRATION_UPDATE_TIME")
    calibration_trade_sample: int = Field(default=5000, alias="CALIBRATION_TRADE_SAMPLE")

    log_retention_days: int = Field(default=30, alias="LOG_RETENTION_DAYS")

    alert_email_to: str = Field(default="", alias="ALERT_EMAIL_TO")
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_tls: bool = Field(default=True, alias="SMTP_TLS")


@lru_cache
def get_settings() -> Settings:
    return Settings()

