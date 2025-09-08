"""Trading API routes for the dYdX trading bot."""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..database.base import get_db
from ..database.dao import TradingDAO
from ..security.auth import get_current_user, User
from ..trading.strategies.ma_crossover import MovingAverageCrossoverStrategy
from ..trading.risk_management.position_sizer import PositionSizer
from ..trading.api_client import DydxRestClient
from ..config.settings import get_settings
from .schemas import (
    DashboardResponse,
    PositionResponse,
    TradeResponse,
    StrategyConfigRequest,
    StrategyConfigResponse,
    EmergencyStopRequest,
    PerformanceMetricsResponse
)

router = APIRouter(prefix="/api/trading", tags=["trading"])
security = HTTPBearer()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data including:
    - Account balance and equity
    - Current positions with unrealized P&L
    - Today's trading activity
    - Performance metrics
    - System status
    """
    try:
        trading_dao = TradingDAO(db)
        
        # Get current positions
        positions = trading_dao.get_current_positions(current_user.id)
        
        # Calculate total unrealized P&L
        total_unrealized_pnl = sum(pos.unrealized_pnl or 0 for pos in positions)
        
        # Get today's P&L
        today = datetime.utcnow().date()
        today_pnl = trading_dao.calculate_daily_pnl(current_user.id, datetime.combine(today, datetime.min.time()))
        
        # Get recent trades
        recent_trades = trading_dao.get_trade_history(
            user_id=current_user.id,
            start_date=datetime.utcnow() - timedelta(days=7),
            limit=10
        )
        
        # Calculate performance metrics
        performance = trading_dao.get_performance_metrics(current_user.id, days=30)
        
        # Mock account balance (in production, fetch from dYdX API)
        account_balance = 10000.0  # This would come from the API client
        total_equity = account_balance + total_unrealized_pnl
        
        # Calculate margin utilization
        used_margin = sum(pos.margin_used for pos in positions)
        available_margin = max(0, account_balance - used_margin)
        margin_utilization = (used_margin / account_balance * 100) if account_balance > 0 else 0
        
        return DashboardResponse(
            total_equity=total_equity,
            account_balance=account_balance,
            daily_pnl=today_pnl.get("total_pnl", 0),
            daily_pnl_percent=(today_pnl.get("total_pnl", 0) / account_balance * 100) if account_balance > 0 else 0,
            total_unrealized_pnl=total_unrealized_pnl,
            available_margin=available_margin,
            used_margin=used_margin,
            margin_utilization=margin_utilization,
            open_positions=len(positions),
            total_trades=len(recent_trades),
            win_rate=performance.get("win_rate", 0) * 100,
            sharpe_ratio=performance.get("sharpe_ratio", 0),
            max_drawdown=performance.get("max_drawdown", 0) * 100,
            system_status="healthy",  # This would be determined by health checks
            trading_enabled=current_user.trading_enabled,
            paper_mode=current_user.paper_trading_mode
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """Get all current positions with real-time P&L."""
    try:
        trading_dao = TradingDAO(db)
        positions = trading_dao.get_current_positions(current_user.id, symbol=symbol)
        
        return [
            PositionResponse(
                id=pos.id,
                symbol=pos.symbol,
                side=pos.side,
                size=pos.size,
                entry_price=pos.entry_price,
                mark_price=pos.mark_price or pos.entry_price,
                unrealized_pnl=pos.unrealized_pnl or 0,
                unrealized_pnl_percent=pos.unrealized_pnl_percent or 0,
                notional_value=pos.notional_value,
                margin_used=pos.margin_used,
                leverage=pos.leverage,
                stop_loss_price=pos.stop_loss_price,
                take_profit_price=pos.take_profit_price,
                liquidation_price=pos.liquidation_price,
                strategy_name=pos.strategy_name,
                opened_at=pos.opened_at,
                updated_at=pos.updated_at
            ) for pos in positions
        ]
        
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch positions")


@router.get("/trades", response_model=List[TradeResponse])
async def get_trade_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000, description="Number of trades to return"),
    offset: int = Query(0, ge=0, description="Number of trades to skip"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter")
):
    """Get paginated trade history with filters."""
    try:
        trading_dao = TradingDAO(db)
        trades = trading_dao.get_trade_history(
            user_id=current_user.id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            strategy_name=strategy,
            limit=limit,
            offset=offset
        )
        
        return [
            TradeResponse(
                id=trade.id,
                order_id=trade.order_id,
                symbol=trade.symbol,
                side=trade.side,
                order_type=trade.order_type,
                size=trade.size,
                price=trade.price,
                filled_size=trade.filled_size,
                notional_value=trade.notional_value,
                commission=trade.commission,
                realized_pnl=trade.realized_pnl,
                status=trade.status,
                strategy_name=trade.strategy_name,
                signal_strength=trade.signal_strength,
                entry_reason=trade.entry_reason,
                timestamp=trade.timestamp,
                created_at=trade.created_at
            ) for trade in trades
        ]
        
    except Exception as e:
        logger.error(f"Error fetching trade history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trade history")


@router.get("/strategy/config", response_model=StrategyConfigResponse)
async def get_strategy_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current strategy configuration."""
    try:
        from ..database.dao import ConfigurationDAO
        
        config_dao = ConfigurationDAO(db)
        
        # Get strategy configurations
        strategy_configs = config_dao.get_category_configs("strategy", current_user.id)
        risk_configs = config_dao.get_category_configs("risk", current_user.id)
        
        # Build configuration response with defaults
        config_dict = {}
        for config in strategy_configs + risk_configs:
            config_dict[config.key] = config.value
        
        return StrategyConfigResponse(
            strategy_name="MovingAverageCrossover",
            ema_fast_period=config_dict.get("ema_fast_period", 12),
            ema_slow_period=config_dict.get("ema_slow_period", 26),
            rsi_period=config_dict.get("rsi_period", 14),
            rsi_oversold=config_dict.get("rsi_oversold", 30),
            rsi_overbought=config_dict.get("rsi_overbought", 70),
            max_position_size_pct=config_dict.get("max_position_size_pct", 0.005),
            max_leverage=config_dict.get("max_leverage", 3.0),
            stop_loss_pct=config_dict.get("stop_loss_pct", 0.02),
            take_profit_ratio=config_dict.get("take_profit_ratio", 1.5),
            daily_loss_limit=config_dict.get("daily_loss_limit", 0.02),
            enabled=config_dict.get("strategy_enabled", True),
            paper_mode=current_user.paper_trading_mode
        )
        
    except Exception as e:
        logger.error(f"Error fetching strategy config: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch strategy configuration")


@router.post("/strategy/config", response_model=StrategyConfigResponse)
async def update_strategy_config(
    config_request: StrategyConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update strategy configuration."""
    try:
        from ..database.dao import ConfigurationDAO
        
        config_dao = ConfigurationDAO(db)
        
        # Define configuration mappings
        config_updates = {
            # Strategy parameters
            ("strategy", "ema_fast_period"): (config_request.ema_fast_period, "int"),
            ("strategy", "ema_slow_period"): (config_request.ema_slow_period, "int"),
            ("strategy", "rsi_period"): (config_request.rsi_period, "int"),
            ("strategy", "rsi_oversold"): (config_request.rsi_oversold, "float"),
            ("strategy", "rsi_overbought"): (config_request.rsi_overbought, "float"),
            ("strategy", "strategy_enabled"): (config_request.enabled, "bool"),
            
            # Risk parameters
            ("risk", "max_position_size_pct"): (config_request.max_position_size_pct, "float"),
            ("risk", "max_leverage"): (config_request.max_leverage, "float"),
            ("risk", "stop_loss_pct"): (config_request.stop_loss_pct, "float"),
            ("risk", "take_profit_ratio"): (config_request.take_profit_ratio, "float"),
            ("risk", "daily_loss_limit"): (config_request.daily_loss_limit, "float")
        }
        
        # Save all configuration updates
        for (category, key), (value, value_type) in config_updates.items():
            await config_dao.save_config(
                category=category,
                key=key,
                value=value,
                value_type=value_type,
                user_id=current_user.id,
                updated_by=current_user.id
            )
        
        # Update user's paper trading mode
        if hasattr(config_request, 'paper_mode'):
            from ..database.dao import UserDAO
            user_dao = UserDAO(db)
            user_dao.update_user(current_user.id, {"paper_trading_mode": config_request.paper_mode})
        
        logger.info(f"Strategy configuration updated for user {current_user.id}")
        
        # Return updated configuration
        return await get_strategy_config(current_user, db)
        
    except Exception as e:
        logger.error(f"Error updating strategy config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update strategy configuration")


@router.post("/emergency-stop")
async def emergency_stop(
    request: EmergencyStopRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Emergency stop all trading activity."""
    try:
        from ..database.dao import UserDAO, AlertDAO
        
        user_dao = UserDAO(db)
        alert_dao = AlertDAO(db)
        
        # Disable trading for the user
        user_dao.update_user(current_user.id, {
            "trading_enabled": False
        })
        
        # Create emergency stop alert
        await alert_dao.create_alert({
            "user_id": current_user.id,
            "alert_type": "system",
            "severity": "CRITICAL",
            "title": "Emergency Stop Activated",
            "message": f"Trading has been emergency stopped. Reason: {request.reason}",
            "metadata": {
                "reason": request.reason,
                "requested_by": current_user.email,
                "close_positions": request.close_positions
            }
        })
        
        # TODO: In production, add background task to:
        # 1. Cancel all open orders
        # 2. Close positions if requested
        # 3. Stop strategy execution
        # 4. Send notifications
        
        logger.warning(f"Emergency stop activated by user {current_user.id}: {request.reason}")
        
        return {
            "success": True,
            "message": "Emergency stop activated successfully",
            "trading_enabled": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute emergency stop")


@router.post("/resume-trading")
async def resume_trading(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume trading after emergency stop."""
    try:
        from ..database.dao import UserDAO, AlertDAO
        
        user_dao = UserDAO(db)
        alert_dao = AlertDAO(db)
        
        # Check if user can resume trading (basic safety checks)
        today_pnl = TradingDAO(db).calculate_daily_pnl(
            current_user.id, 
            datetime.utcnow()
        )
        
        daily_loss_limit = 0.02  # 2% (should come from config)
        if abs(today_pnl.get("total_pnl", 0)) > daily_loss_limit * 10000:  # Assuming 10k balance
            raise HTTPException(
                status_code=400, 
                detail="Cannot resume trading: daily loss limit exceeded"
            )
        
        # Re-enable trading
        user_dao.update_user(current_user.id, {
            "trading_enabled": True
        })
        
        # Create resume alert
        await alert_dao.create_alert({
            "user_id": current_user.id,
            "alert_type": "system",
            "severity": "INFO",
            "title": "Trading Resumed",
            "message": "Trading has been resumed after emergency stop.",
            "metadata": {
                "resumed_by": current_user.email
            }
        })
        
        logger.info(f"Trading resumed for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Trading resumed successfully",
            "trading_enabled": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resuming trading: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume trading")


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get detailed performance metrics."""
    try:
        trading_dao = TradingDAO(db)
        metrics = trading_dao.get_performance_metrics(current_user.id, days)
        
        if "error" in metrics:
            return PerformanceMetricsResponse(
                period_days=days,
                error=metrics["error"]
            )
        
        return PerformanceMetricsResponse(
            period_days=metrics["period_days"],
            total_trades=metrics["total_trades"],
            winning_trades=metrics["winning_trades"],
            losing_trades=metrics["losing_trades"],
            win_rate=metrics["win_rate"] * 100,
            total_pnl=metrics["total_pnl"],
            net_pnl=metrics["net_pnl"],
            total_volume=metrics["total_volume"],
            total_commission=metrics["total_commission"],
            avg_win=metrics["avg_win"],
            avg_loss=metrics["avg_loss"],
            risk_reward_ratio=metrics["risk_reward_ratio"],
            sharpe_ratio=metrics["sharpe_ratio"],
            max_drawdown=metrics["max_drawdown"] * 100
        )
        
    except Exception as e:
        logger.error(f"Error fetching performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch performance metrics")


@router.get("/signals")
async def get_recent_signals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    strategy: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None)
):
    """Get recent strategy signals."""
    try:
        trading_dao = TradingDAO(db)
        signals = trading_dao.get_recent_signals(
            user_id=current_user.id,
            strategy_name=strategy,
            symbol=symbol,
            limit=limit
        )
        
        return [
            {
                "id": signal.id,
                "strategy_name": signal.strategy_name,
                "symbol": signal.symbol,
                "signal_type": signal.signal_type,
                "strength": signal.strength,
                "confidence": signal.confidence,
                "price": signal.price,
                "volume": signal.volume,
                "indicators": signal.indicators,
                "reasoning": signal.reasoning,
                "risk_score": signal.risk_score,
                "executed": signal.executed,
                "execution_price": signal.execution_price,
                "timestamp": signal.timestamp
            } for signal in signals
        ]
        
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch signals")


@router.get("/health")
async def get_trading_health():
    """Get trading system health status."""
    try:
        # TODO: Implement actual health checks
        # - dYdX API connectivity
        # - WebSocket connection status  
        # - Database connectivity
        # - Strategy execution status
        # - Risk management system status
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "healthy",
                "dydx_api": "healthy", 
                "websocket": "healthy",
                "strategies": "healthy",
                "risk_management": "healthy"
            },
            "version": "1.0.0"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }