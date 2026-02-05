from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.crypto import encrypt_text
from app.core.security import create_access_token, verify_password
from app.db import models
from app.db.session import get_db
from app.schemas.alerts import AlertResponse
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.config import AppConfigResponse, AppConfigUpdate
from app.schemas.dashboard import DashboardMetrics
from app.schemas.keys import ApiKeyResponse, ApiKeyUpdate
from app.schemas.market import OrderResponse, PositionResponse, TradeResponse
from app.schemas.risk import RiskLimitsUpdate, RiskStatusResponse
from app.schemas.strategy import StrategyParamsResponse, StrategyParamsUpdate
from app.services.reports import generate_pnl_report
from app.services.repository import (
    app_config_to_response,
    get_current_app_config,
    get_latest_api_keys,
    get_or_create_params,
    get_or_create_risk_limits,
    save_api_keys,
    update_app_config,
    update_params,
    update_risk_limits,
)


router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    username = payload.username.strip()
    password = payload.password
    if not username or not password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    result = await db.execute(select(models.User).where(models.User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.username)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=UserResponse)
async def me(user: models.User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(username=user.username, is_active=user.is_active)


@router.get("/dashboard/metrics", response_model=DashboardMetrics)
async def dashboard_metrics(
    request: Request, user: models.User = Depends(get_current_user)
) -> DashboardMetrics:
    state = request.app.state.app_state
    engine = request.app.state.config_manager.engine
    mid = state.market.mid_price
    inventory_btc = state.position.size
    inventory_usd = inventory_btc * mid if mid else 0.0
    spread = state.market.best_ask - state.market.best_bid if mid else 0.0
    return DashboardMetrics(
        mid_price=mid,
        inventory_btc=inventory_btc,
        inventory_usd=inventory_usd,
        unrealized_pnl=state.position.unrealized_pnl,
        open_orders=len(state.engine.open_order_ids),
        spread=spread,
        cancel_rate_per_min=engine._risk_manager.cancel_rate_per_min()
        if engine and engine._risk_manager
        else 0.0,
        order_rate_per_min=engine._risk_manager.order_rate_per_min()
        if engine and engine._risk_manager
        else 0.0,
    )


@router.get("/positions", response_model=list[PositionResponse])
async def positions(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> list[PositionResponse]:
    result = await db.execute(select(models.Position))
    positions = result.scalars().all()
    return [
        PositionResponse(
            symbol=p.symbol,
            size=p.size,
            entry_price=p.entry_price,
            mark_price=p.mark_price,
            unrealized_pnl=p.unrealized_pnl,
        )
        for p in positions
    ]


@router.get("/orders", response_model=list[OrderResponse])
async def orders(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> list[OrderResponse]:
    result = await db.execute(select(models.Order).order_by(models.Order.created_at.desc()).limit(200))
    orders = result.scalars().all()
    return [
        OrderResponse(
            order_id=o.order_id,
            symbol=o.symbol,
            side=o.side,
            price=o.price,
            size=o.size,
            status=o.status,
        )
        for o in orders
    ]


@router.get("/trades", response_model=list[TradeResponse])
async def trades(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> list[TradeResponse]:
    result = await db.execute(select(models.Trade).order_by(models.Trade.created_at.desc()).limit(200))
    trades = result.scalars().all()
    return [
        TradeResponse(
            trade_id=t.trade_id,
            symbol=t.symbol,
            side=t.side,
            price=t.price,
            size=t.size,
            fee=t.fee,
            realized_pnl=t.realized_pnl,
        )
        for t in trades
    ]


@router.get("/strategy/params", response_model=StrategyParamsResponse)
async def get_params(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> StrategyParamsResponse:
    params = await get_or_create_params(db)
    return StrategyParamsResponse(
        gamma=params.gamma,
        sigma=params.sigma,
        A=params.A,
        k=params.k,
        time_horizon_seconds=params.time_horizon_seconds,
        inventory_cap_usd=params.inventory_cap_usd,
        order_cap_usd=params.order_cap_usd,
        leverage_limit=params.leverage_limit,
        auto_tuning_enabled=params.auto_tuning_enabled,
    )


@router.post("/strategy/params", response_model=StrategyParamsResponse)
async def update_strategy_params(
    payload: StrategyParamsUpdate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> StrategyParamsResponse:
    params = await update_params(db, payload.model_dump())
    return StrategyParamsResponse(
        gamma=params.gamma,
        sigma=params.sigma,
        A=params.A,
        k=params.k,
        time_horizon_seconds=params.time_horizon_seconds,
        inventory_cap_usd=params.inventory_cap_usd,
        order_cap_usd=params.order_cap_usd,
        leverage_limit=params.leverage_limit,
        auto_tuning_enabled=params.auto_tuning_enabled,
    )


@router.get("/risk/status", response_model=RiskStatusResponse)
async def risk_status(request: Request, user: models.User = Depends(get_current_user)) -> RiskStatusResponse:
    engine = request.app.state.config_manager.engine
    rm = engine._risk_manager if engine else None
    return RiskStatusResponse(
        is_trading=engine._running if engine else False,
        last_event=request.app.state.app_state.engine.last_event,
        cancel_rate_per_min=rm.cancel_rate_per_min() if rm else 0.0,
        order_rate_per_min=rm.order_rate_per_min() if rm else 0.0,
    )


@router.post("/risk/limits")
async def update_limits(
    payload: RiskLimitsUpdate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    limits = await update_risk_limits(db, payload.model_dump())
    return {"status": "ok", "updated_at": str(limits.updated_at)}


@router.post("/keys", response_model=ApiKeyResponse)
async def save_keys(
    payload: ApiKeyUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> ApiKeyResponse:
    record = await save_api_keys(
        db,
        encrypt_text(payload.api_key),
        encrypt_text(payload.private_key),
        payload.sub_account_id,
        payload.ip_whitelist or "",
    )
    await request.app.state.config_manager.reload_client()
    return ApiKeyResponse(sub_account_id=record.sub_account_id, ip_whitelist=record.ip_whitelist)


@router.get("/keys", response_model=ApiKeyResponse)
async def get_keys(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> ApiKeyResponse:
    record = await get_latest_api_keys(db)
    if not record:
        raise HTTPException(status_code=404, detail="未配置密钥")
    return ApiKeyResponse(sub_account_id=record.sub_account_id, ip_whitelist=record.ip_whitelist)


@router.post("/engine/start")
async def engine_start(request: Request, user: models.User = Depends(get_current_user)) -> dict:
    await request.app.state.config_manager.engine.start()
    return {"status": "running"}


@router.post("/engine/stop")
async def engine_stop(request: Request, user: models.User = Depends(get_current_user)) -> dict:
    await request.app.state.config_manager.engine.stop()
    return {"status": "stopped"}


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> list[AlertResponse]:
    result = await db.execute(select(models.Alert).order_by(models.Alert.created_at.desc()).limit(200))
    alerts = result.scalars().all()
    return [
        AlertResponse(id=a.id, level=a.level, message=a.message, is_read=a.is_read) for a in alerts
    ]


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> dict:
    await db.execute(
        select(models.Alert).where(models.Alert.id == alert_id).execution_options(populate_existing=True)
    )
    alert = await db.get(models.Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    alert.is_read = True
    await db.commit()
    return {"status": "ok"}


@router.get("/reports/pnl.csv")
async def report_pnl(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> Response:
    csv_data = await generate_pnl_report(db)
    return Response(content=csv_data, media_type="text/csv")


@router.get("/config", response_model=AppConfigResponse)
async def get_config(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> AppConfigResponse:
    config = await get_current_app_config(db)
    if not config:
        raise HTTPException(status_code=404, detail="未初始化配置")
    return AppConfigResponse(**app_config_to_response(config))


@router.post("/config", response_model=AppConfigResponse)
async def update_config(
    payload: AppConfigUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> AppConfigResponse:
    config = await update_app_config(db, payload.model_dump())
    await request.app.state.config_manager.apply_config()
    request.app.state.schedule_jobs(config)
    return AppConfigResponse(**app_config_to_response(config))
