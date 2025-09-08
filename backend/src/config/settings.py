"""
Trading Bot Configuration Management
Centralized configuration with environment-specific settings, validation, and type safety.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator, Field
from enum import Enum


class TradingEnvironment(str, Enum):
    """Trading environment options"""
    TESTNET = "testnet"
    MAINNET = "mainnet"


class TradingMode(str, Enum):
    """Trading mode options"""
    PAPER = "paper"
    LIVE = "live"


class LogLevel(str, Enum):
    """Logging level options"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class TradingConfig(BaseSettings):
    """
    Comprehensive trading bot configuration with validation and type safety.
    All settings can be overridden via environment variables.
    """
    
    # =============================================================================
    # dYdX API Configuration
    # =============================================================================
    
    dydx_api_key: str = Field(..., description="dYdX API key")
    dydx_secret_key: str = Field(..., description="dYdX secret key")
    dydx_passphrase: str = Field(..., description="dYdX passphrase")
    dydx_environment: TradingEnvironment = Field(
        TradingEnvironment.TESTNET, 
        description="dYdX environment (testnet/mainnet)"
    )
    
    @validator('dydx_api_key', 'dydx_secret_key', 'dydx_passphrase')
    def validate_dydx_credentials(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("dYdX credentials cannot be empty")
        return v.strip()
    
    # =============================================================================
    # Database Configuration
    # =============================================================================
    
    database_url: str = Field(
        "postgresql://trading_user:secure_password@localhost:5432/trading_bot",
        description="PostgreSQL database URL"
    )
    database_test_url: str = Field(
        "postgresql://trading_user:secure_password@localhost:5432/trading_bot_test",
        description="Test database URL"
    )
    
    # =============================================================================
    # Redis Configuration
    # =============================================================================
    
    redis_url: str = Field(
        "redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # =============================================================================
    # Security Configuration
    # =============================================================================
    
    jwt_secret_key: str = Field(..., description="JWT secret key (min 32 characters)")
    jwt_algorithm: str = Field("HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(
        30, 
        description="JWT access token expiration in minutes"
    )
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v
    
    # =============================================================================
    # Trading Configuration
    # =============================================================================
    
    trading_mode: TradingMode = Field(
        TradingMode.PAPER, 
        description="Trading mode (paper/live)"
    )
    
    # Supported trading symbols
    symbols: List[str] = Field(
        ["BTC-USD", "ETH-USD", "LINK-USD"],
        description="List of symbols to trade"
    )
    
    # Capital management
    initial_capital: float = Field(
        10000.0, 
        gt=0, 
        description="Initial trading capital"
    )
    
    # Position sizing
    max_position_size_pct: float = Field(
        0.005, 
        gt=0, 
        le=0.1, 
        description="Maximum position size as percentage of equity (0.5%)"
    )
    
    # Leverage and risk
    max_leverage: float = Field(
        3.0, 
        gt=1.0, 
        le=10.0, 
        description="Maximum leverage allowed"
    )
    
    daily_loss_limit_pct: float = Field(
        0.02, 
        gt=0, 
        le=0.1, 
        description="Daily loss limit as percentage (2%)"
    )
    
    # =============================================================================
    # Strategy Parameters - Moving Average Crossover
    # =============================================================================
    
    # EMA periods
    ema_fast_period: int = Field(
        12, 
        gt=1, 
        lt=100, 
        description="Fast EMA period"
    )
    
    ema_slow_period: int = Field(
        26, 
        gt=1, 
        lt=200, 
        description="Slow EMA period"
    )
    
    @validator('ema_slow_period')
    def validate_ema_periods(cls, v, values):
        if 'ema_fast_period' in values and v <= values['ema_fast_period']:
            raise ValueError("Slow EMA period must be greater than fast EMA period")
        return v
    
    # RSI parameters
    rsi_period: int = Field(
        14, 
        gt=1, 
        lt=50, 
        description="RSI calculation period"
    )
    
    rsi_oversold: float = Field(
        30.0, 
        gt=0, 
        lt=50, 
        description="RSI oversold threshold"
    )
    
    rsi_overbought: float = Field(
        70.0, 
        gt=50, 
        lt=100, 
        description="RSI overbought threshold"
    )
    
    @validator('rsi_overbought')
    def validate_rsi_thresholds(cls, v, values):
        if 'rsi_oversold' in values and v <= values['rsi_oversold']:
            raise ValueError("RSI overbought must be greater than oversold")
        return v
    
    # =============================================================================
    # Risk Management Parameters
    # =============================================================================
    
    # Stop loss and take profit
    stop_loss_pct: float = Field(
        0.02, 
        gt=0, 
        le=0.1, 
        description="Stop loss percentage (2%)"
    )
    
    take_profit_ratio: float = Field(
        1.5, 
        gt=0, 
        le=10, 
        description="Risk/reward ratio for take profit (1.5:1)"
    )
    
    # Correlation limits
    max_correlation: float = Field(
        0.8, 
        gt=0, 
        le=1, 
        description="Maximum position correlation allowed"
    )
    
    # Trailing stops
    enable_trailing_stops: bool = Field(
        True, 
        description="Enable trailing stops for profitable positions"
    )
    
    trailing_stop_trigger_pct: float = Field(
        0.01, 
        gt=0, 
        le=0.1, 
        description="Profit percentage to trigger trailing stop (1%)"
    )
    
    # =============================================================================
    # Market Data Configuration
    # =============================================================================
    
    # WebSocket settings
    websocket_reconnect_delay: int = Field(
        5, 
        gt=0, 
        description="WebSocket reconnect delay in seconds"
    )
    
    websocket_max_reconnect_attempts: int = Field(
        10, 
        gt=0, 
        description="Maximum WebSocket reconnect attempts"
    )
    
    # Candle timeframes
    candle_timeframes: List[str] = Field(
        ["1m", "5m", "15m", "1h", "4h", "1d"],
        description="Supported candle timeframes"
    )
    
    # Order book depth
    orderbook_depth: int = Field(
        20, 
        gt=0, 
        le=100, 
        description="Order book depth to maintain"
    )
    
    # =============================================================================
    # Monitoring and Alerting
    # =============================================================================
    
    enable_monitoring: bool = Field(
        True, 
        description="Enable Prometheus metrics collection"
    )
    
    prometheus_port: int = Field(
        9090, 
        gt=1000, 
        lt=65536, 
        description="Prometheus metrics port"
    )
    
    # Email alerts
    smtp_server: Optional[str] = Field(None, description="SMTP server for email alerts")
    smtp_port: int = Field(587, description="SMTP server port")
    smtp_username: Optional[str] = Field(None, description="SMTP username")
    smtp_password: Optional[str] = Field(None, description="SMTP password")
    alert_email: Optional[str] = Field(None, description="Email for alerts")
    
    # Slack alerts
    slack_webhook_url: Optional[str] = Field(None, description="Slack webhook URL")
    
    # SMS alerts (Twilio)
    twilio_account_sid: Optional[str] = Field(None, description="Twilio account SID")
    twilio_auth_token: Optional[str] = Field(None, description="Twilio auth token")
    twilio_phone_number: Optional[str] = Field(None, description="Twilio phone number")
    alert_phone_number: Optional[str] = Field(None, description="Phone number for alerts")
    
    # =============================================================================
    # Logging Configuration
    # =============================================================================
    
    log_level: LogLevel = Field(LogLevel.INFO, description="Logging level")
    log_format: str = Field("json", description="Log format (json/text)")
    log_file_path: str = Field("logs/trading_bot.log", description="Log file path")
    log_max_size_mb: int = Field(100, gt=0, description="Max log file size in MB")
    log_backup_count: int = Field(5, gt=0, description="Number of log file backups")
    
    # =============================================================================
    # Performance Configuration
    # =============================================================================
    
    # API rate limiting
    api_requests_per_second: int = Field(
        10, 
        gt=0, 
        description="Maximum API requests per second"
    )
    
    # Database connection pooling
    db_pool_size: int = Field(20, gt=0, description="Database connection pool size")
    db_max_overflow: int = Field(30, gt=0, description="Database connection overflow")
    
    # Cache TTL
    market_data_cache_ttl: int = Field(
        60, 
        gt=0, 
        description="Market data cache TTL in seconds"
    )
    
    # =============================================================================
    # Backtesting Configuration
    # =============================================================================
    
    # Transaction costs
    maker_fee_pct: float = Field(
        0.0002, 
        ge=0, 
        description="Maker fee percentage (0.02%)"
    )
    
    taker_fee_pct: float = Field(
        0.0005, 
        ge=0, 
        description="Taker fee percentage (0.05%)"
    )
    
    # Slippage simulation
    slippage_pct: float = Field(
        0.001, 
        ge=0, 
        description="Slippage percentage for backtesting (0.1%)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global configuration instance
config = TradingConfig()


def get_config() -> TradingConfig:
    """Get the global configuration instance"""
    return config


def reload_config() -> TradingConfig:
    """Reload configuration from environment variables"""
    global config
    config = TradingConfig()
    return config