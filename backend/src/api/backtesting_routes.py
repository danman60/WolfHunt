"""
Backtesting API Routes

REST API endpoints for running backtests, retrieving results,
and managing backtesting operations in the WolfHunt trading system.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio

from ..database.base import get_db
from ..security.auth import get_current_user, User
from ..trading.backtesting.engine import BacktestEngine
from ..trading.backtesting.utils import BacktestConfig
from ..trading.backtesting.mock_wallet import MockWallet
from .schemas import (
    BacktestRequest,
    BacktestResult,
    BacktestStatusResponse,
    BacktestListResponse
)

router = APIRouter(prefix="/api/backtesting", tags=["backtesting"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Global backtest engine instance
backtest_engine = BacktestEngine()


@router.post("/run", response_model=Dict[str, Any])
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a backtest with historical data

    - **strategy_config**: Strategy parameters and configuration
    - **symbols**: List of trading symbols (BTC, ETH, LINK)
    - **start_date**: Backtest start date
    - **end_date**: Backtest end date
    - **initial_capital**: Starting portfolio value
    - **commission_rate**: Trading commission rate

    Returns backtest ID for tracking progress
    """
    try:
        logger.info(f"User {current_user.id} requested backtest: {request.strategy_config.strategy_name}")

        # Create backtest configuration
        config = BacktestConfig(
            strategy_name=request.strategy_config.strategy_name,
            strategy_params=request.strategy_config.parameters,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe='1h',  # Default timeframe
            symbols=request.symbols,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate
        )

        # Validate date range
        if config.end_date <= config.start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")

        max_days = 365 * 2  # 2 year limit
        if (config.end_date - config.start_date).days > max_days:
            raise HTTPException(status_code=400, detail=f"Backtest period too long (max {max_days} days)")

        # Start backtest in background
        async def progress_callback(backtest_id: str, progress: float, message: str):
            logger.debug(f"Backtest {backtest_id}: {progress:.1f}% - {message}")

        # Execute backtest asynchronously
        backtest_task = asyncio.create_task(
            backtest_engine.run_backtest(config, progress_callback)
        )

        # Get backtest ID from active backtests
        backtest_id = None
        for bid, info in backtest_engine.active_backtests.items():
            if info['config'] == config:
                backtest_id = bid
                break

        if not backtest_id:
            # Fallback - create temporary ID
            import uuid
            backtest_id = str(uuid.uuid4())

        return {
            "backtest_id": backtest_id,
            "status": "started",
            "message": f"Backtest started for {config.strategy_name} on {len(config.symbols)} symbols",
            "estimated_completion_minutes": _estimate_completion_time(config)
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Backtest execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")


@router.get("/status/{backtest_id}", response_model=BacktestStatusResponse)
async def get_backtest_status(
    backtest_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a running or completed backtest

    Returns current progress, status, and any error messages
    """
    try:
        status_info = backtest_engine.get_backtest_status(backtest_id)

        if not status_info:
            raise HTTPException(status_code=404, detail="Backtest not found")

        return BacktestStatusResponse(
            backtest_id=backtest_id,
            status=status_info['status'].value,
            progress=status_info['progress'],
            message=status_info.get('status_message', ''),
            start_time=status_info['start_time'],
            error=status_info.get('error')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backtest status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get backtest status")


@router.get("/results/{backtest_id}", response_model=Dict[str, Any])
async def get_backtest_results(
    backtest_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve completed backtest results

    Returns comprehensive performance metrics, trade history,
    and portfolio analysis for the specified backtest
    """
    try:
        status_info = backtest_engine.get_backtest_status(backtest_id)

        if not status_info:
            raise HTTPException(status_code=404, detail="Backtest not found")

        if status_info['status'].value != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Backtest not completed. Status: {status_info['status'].value}"
            )

        # Results would be stored in the status_info or retrieved from database
        # For now, return a structured response
        results = status_info.get('results', {})

        if not results:
            raise HTTPException(status_code=404, detail="Backtest results not available")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving backtest results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve backtest results")


@router.get("/history", response_model=BacktestListResponse)
async def get_user_backtests(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """
    List user's previous backtests

    Returns paginated list of user's backtest history with summary metrics
    """
    try:
        active_backtests = backtest_engine.list_active_backtests()

        # Apply pagination
        paginated_backtests = active_backtests[offset:offset + limit]

        return BacktestListResponse(
            backtests=paginated_backtests,
            total=len(active_backtests),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing backtests: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list backtests")


@router.delete("/cancel/{backtest_id}")
async def cancel_backtest(
    backtest_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a running backtest

    Stops the execution of a currently running backtest
    """
    try:
        success = backtest_engine.cancel_backtest(backtest_id)

        if not success:
            raise HTTPException(status_code=404, detail="Backtest not found or not running")

        return {
            "backtest_id": backtest_id,
            "status": "cancelled",
            "message": "Backtest cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling backtest: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel backtest")


@router.post("/quick-test", response_model=Dict[str, Any])
async def run_quick_backtest(
    strategy_name: str = "ema_crossover",
    symbols: List[str] = ["BTC"],
    days_back: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Run a quick backtest for testing purposes

    Executes a simplified backtest with default parameters for rapid validation
    """
    try:
        # Default configuration for quick testing
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        config = BacktestConfig(
            strategy_name=strategy_name,
            strategy_params={
                'fastPeriod': 12,
                'slowPeriod': 26,
                'positionSize': 0.1
            },
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
            initial_capital=10000.0
        )

        # Run quick backtest (synchronous for testing)
        results = await backtest_engine.run_backtest(config)

        return {
            "status": "completed",
            "quick_test": True,
            "summary": {
                "initial_capital": results.get('initial_capital'),
                "final_value": results.get('final_value'),
                "total_return_pct": results.get('total_return_pct'),
                "total_trades": results.get('total_trades'),
                "win_rate_pct": results.get('win_rate_pct'),
                "max_drawdown_pct": results.get('max_drawdown_pct'),
                "sharpe_ratio": results.get('sharpe_ratio')
            },
            "config": {
                "strategy": strategy_name,
                "symbols": symbols,
                "period_days": days_back
            }
        }

    except Exception as e:
        logger.error(f"Quick backtest failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick backtest failed: {str(e)}")


@router.get("/strategies")
async def list_available_strategies():
    """
    List available trading strategies for backtesting

    Returns information about supported strategies and their parameters
    """
    strategies = [
        {
            "name": "ema_crossover",
            "display_name": "EMA Crossover",
            "description": "Exponential Moving Average crossover strategy",
            "parameters": {
                "fastPeriod": {"type": "integer", "default": 12, "min": 5, "max": 50},
                "slowPeriod": {"type": "integer", "default": 26, "min": 20, "max": 200},
                "positionSize": {"type": "float", "default": 0.1, "min": 0.01, "max": 1.0}
            }
        },
        {
            "name": "rsi_mean_reversion",
            "display_name": "RSI Mean Reversion",
            "description": "RSI-based mean reversion strategy",
            "parameters": {
                "period": {"type": "integer", "default": 14, "min": 7, "max": 30},
                "oversoldLevel": {"type": "integer", "default": 30, "min": 10, "max": 40},
                "overboughtLevel": {"type": "integer", "default": 70, "min": 60, "max": 90},
                "positionSize": {"type": "float", "default": 0.05, "min": 0.01, "max": 0.5}
            }
        },
        {
            "name": "momentum",
            "display_name": "Momentum Strategy",
            "description": "Price momentum-based strategy",
            "parameters": {
                "lookback": {"type": "integer", "default": 20, "min": 10, "max": 50},
                "threshold": {"type": "float", "default": 0.02, "min": 0.01, "max": 0.1},
                "positionSize": {"type": "float", "default": 0.05, "min": 0.01, "max": 0.5}
            }
        }
    ]

    return {
        "strategies": strategies,
        "supported_symbols": ["BTC", "ETH", "LINK", "WBTC"],
        "supported_timeframes": ["1h", "4h", "1d"],
        "max_backtest_days": 730
    }


def _estimate_completion_time(config: BacktestConfig) -> int:
    """Estimate backtest completion time in minutes"""
    days = (config.end_date - config.start_date).days
    symbols = len(config.symbols)

    # Base time estimation
    base_minutes = 1
    data_factor = days * symbols * 0.01  # More data = more time
    complexity_factor = 0.5  # Strategy complexity

    estimated_minutes = max(1, int(base_minutes + data_factor + complexity_factor))
    return min(estimated_minutes, 30)  # Cap at 30 minutes