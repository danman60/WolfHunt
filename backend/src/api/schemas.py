"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Authentication Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    confirm_password: str


class TwoFactorRequest(BaseModel):
    token: str = Field(..., min_length=6, max_length=6, regex=r'^\d{6}$')


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_2fa: bool = False


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_2fa_enabled: bool
    is_active: bool
    trading_enabled: bool
    paper_trading_mode: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


# Trading Schemas
class DashboardResponse(BaseModel):
    # Account information
    total_equity: float
    account_balance: float
    daily_pnl: float
    daily_pnl_percent: float
    total_unrealized_pnl: float
    
    # Margin information
    available_margin: float
    used_margin: float
    margin_utilization: float
    
    # Trading statistics
    open_positions: int
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    
    # System status
    system_status: str
    trading_enabled: bool
    paper_mode: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PositionResponse(BaseModel):
    id: int
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    notional_value: float
    margin_used: float
    leverage: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    liquidation_price: Optional[float]
    strategy_name: Optional[str]
    opened_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    id: int
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    size: float
    price: float
    filled_size: float
    notional_value: float
    commission: float
    realized_pnl: Optional[float]
    status: OrderStatus
    strategy_name: Optional[str]
    signal_strength: Optional[float]
    entry_reason: Optional[str]
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class StrategyConfigRequest(BaseModel):
    # Strategy parameters
    ema_fast_period: int = Field(12, ge=5, le=50, description="Fast EMA period")
    ema_slow_period: int = Field(26, ge=10, le=200, description="Slow EMA period")
    rsi_period: int = Field(14, ge=5, le=50, description="RSI calculation period")
    rsi_oversold: float = Field(30, ge=10, le=40, description="RSI oversold threshold")
    rsi_overbought: float = Field(70, ge=60, le=90, description="RSI overbought threshold")
    
    # Risk management parameters
    max_position_size_pct: float = Field(0.005, ge=0.001, le=0.1, description="Max position size as % of equity")
    max_leverage: float = Field(3.0, ge=1.0, le=10.0, description="Maximum leverage")
    stop_loss_pct: float = Field(0.02, ge=0.005, le=0.1, description="Stop loss percentage")
    take_profit_ratio: float = Field(1.5, ge=1.0, le=5.0, description="Risk/reward ratio")
    daily_loss_limit: float = Field(0.02, ge=0.01, le=0.1, description="Daily loss limit as % of equity")
    
    # Control parameters
    enabled: bool = Field(True, description="Strategy enabled/disabled")
    paper_mode: bool = Field(True, description="Paper trading mode")

    @validator('ema_slow_period')
    def slow_period_must_be_greater_than_fast(cls, v, values):
        if 'ema_fast_period' in values and v <= values['ema_fast_period']:
            raise ValueError('Slow EMA period must be greater than fast EMA period')
        return v


class StrategyConfigResponse(BaseModel):
    strategy_name: str
    ema_fast_period: int
    ema_slow_period: int
    rsi_period: int
    rsi_oversold: float
    rsi_overbought: float
    max_position_size_pct: float
    max_leverage: float
    stop_loss_pct: float
    take_profit_ratio: float
    daily_loss_limit: float
    enabled: bool
    paper_mode: bool
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class EmergencyStopRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)
    close_positions: bool = Field(False, description="Whether to close all open positions")


class PerformanceMetricsResponse(BaseModel):
    period_days: int
    total_trades: Optional[int] = None
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    win_rate: Optional[float] = None
    total_pnl: Optional[float] = None
    net_pnl: Optional[float] = None
    total_volume: Optional[float] = None
    total_commission: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    error: Optional[str] = None


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    type: str
    channel: Optional[str] = None
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SubscriptionRequest(BaseModel):
    action: str = Field(..., regex=r'^(subscribe|unsubscribe)$')
    channels: List[str] = Field(..., min_items=1)


class MarketDataUpdate(BaseModel):
    symbol: str
    price: float
    volume: Optional[float] = None
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None


class PositionUpdate(BaseModel):
    position_id: int
    symbol: str
    unrealized_pnl: float
    unrealized_pnl_percent: float
    mark_price: float
    timestamp: datetime


class TradeExecution(BaseModel):
    trade_id: int
    order_id: str
    symbol: str
    side: OrderSide
    size: float
    price: float
    commission: float
    realized_pnl: Optional[float]
    timestamp: datetime


# Alert Schemas
class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    symbol: Optional[str]
    strategy_name: Optional[str]
    metadata: Optional[Dict[str, Any]]
    is_read: bool
    is_resolved: bool
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class CreateAlertRequest(BaseModel):
    alert_type: str = Field(..., min_length=1, max_length=50)
    severity: AlertSeverity
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    symbol: Optional[str] = None
    strategy_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Order Management Schemas
class PlaceOrderRequest(BaseModel):
    symbol: str = Field(..., regex=r'^[A-Z]+-[A-Z]+$')
    side: OrderSide
    order_type: OrderType
    size: float = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    time_in_force: str = Field("GTC", regex=r'^(GTC|IOC|FOK)$')
    reduce_only: bool = False
    post_only: bool = False

    @validator('price')
    def price_required_for_limit_orders(cls, v, values):
        if values.get('order_type') in ['LIMIT', 'STOP_LIMIT'] and v is None:
            raise ValueError('Price is required for limit orders')
        return v


class OrderResponse(BaseModel):
    order_id: str
    client_order_id: Optional[str]
    symbol: str
    side: OrderSide
    order_type: OrderType
    size: float
    price: Optional[float]
    filled_size: float
    remaining_size: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class CancelOrderRequest(BaseModel):
    order_id: str


# Backtesting Schemas
class BacktestRequest(BaseModel):
    strategy_config: StrategyConfigRequest
    symbols: List[str] = Field(..., min_items=1, max_items=10)
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(10000, gt=0, le=1000000)
    commission_rate: float = Field(0.001, ge=0, le=0.01)


class BacktestResult(BaseModel):
    strategy_name: str
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    backtest_duration_days: int


class BacktestStatusResponse(BaseModel):
    backtest_id: str
    status: str
    progress: float
    message: str
    start_time: datetime
    error: Optional[str] = None


class BacktestListItem(BaseModel):
    backtest_id: str
    strategy_name: str
    status: str
    progress: float
    start_time: str


class BacktestListResponse(BaseModel):
    backtests: List[BacktestListItem]
    total: int
    limit: int
    offset: int


# Health Check Schemas
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    checks: Dict[str, str]
    version: str
    uptime_seconds: Optional[float] = None


# Configuration Schemas
class ConfigurationItem(BaseModel):
    category: str
    key: str
    value: Union[str, int, float, bool, Dict[str, Any], List[Any]]
    value_type: str
    description: Optional[str]
    is_sensitive: bool
    version: int
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateConfigRequest(BaseModel):
    value: Union[str, int, float, bool, Dict[str, Any], List[Any]]
    description: Optional[str] = None