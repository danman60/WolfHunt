"""Database models for the trading bot."""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from .base import Base


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 2FA fields
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(32), nullable=True)
    backup_codes = Column(JSON, nullable=True)  # List of backup codes
    
    # User status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # API key management
    api_key_encrypted = Column(Text, nullable=True)
    api_secret_encrypted = Column(Text, nullable=True)
    api_passphrase_encrypted = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Trading preferences
    trading_enabled = Column(Boolean, default=True)
    paper_trading_mode = Column(Boolean, default=True)
    
    # Relationships
    trades = relationship("Trade", back_populates="user")
    positions = relationship("Position", back_populates="user")
    alerts = relationship("Alert", back_populates="user")


class Trade(Base):
    """Trade execution records."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Trade identification
    order_id = Column(String(100), unique=True, nullable=False)
    client_order_id = Column(String(100), nullable=True)
    
    # Market information
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP_LIMIT
    
    # Execution details
    size = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    filled_size = Column(Float, default=0.0)
    remaining_size = Column(Float, default=0.0)
    
    # Financial details
    notional_value = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    realized_pnl = Column(Float, nullable=True)
    
    # Trade status
    status = Column(String(20), nullable=False)  # FILLED, PARTIALLY_FILLED, CANCELLED, etc.
    
    # Strategy information
    strategy_name = Column(String(100), nullable=True)
    signal_strength = Column(Float, nullable=True)
    entry_reason = Column(String(500), nullable=True)
    
    # Risk management
    stop_loss_price = Column(Float, nullable=True)
    take_profit_price = Column(Float, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trades")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_trades_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_trades_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_trades_strategy_timestamp', 'strategy_name', 'timestamp'),
    )


class Position(Base):
    """Current and historical position tracking."""
    
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Position identification
    symbol = Column(String(20), nullable=False, index=True)
    
    # Position details
    side = Column(String(10), nullable=False)  # LONG, SHORT
    size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    mark_price = Column(Float, nullable=True)  # Current market price
    
    # Financial metrics
    unrealized_pnl = Column(Float, nullable=True)
    unrealized_pnl_percent = Column(Float, nullable=True)
    notional_value = Column(Float, nullable=False)
    margin_used = Column(Float, nullable=False)
    leverage = Column(Float, nullable=False)
    
    # Risk management
    stop_loss_price = Column(Float, nullable=True)
    take_profit_price = Column(Float, nullable=True)
    liquidation_price = Column(Float, nullable=True)
    
    # Position status
    is_open = Column(Boolean, default=True, index=True)
    
    # Strategy information
    strategy_name = Column(String(100), nullable=True)
    entry_reason = Column(String(500), nullable=True)
    
    # Timestamps
    opened_at = Column(DateTime, nullable=False, index=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="positions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_positions_user_open', 'user_id', 'is_open'),
        Index('idx_positions_symbol_open', 'symbol', 'is_open'),
        Index('idx_positions_strategy_open', 'strategy_name', 'is_open'),
        UniqueConstraint('user_id', 'symbol', 'is_open', name='uix_user_symbol_open'),
    )


class StrategySignal(Base):
    """Strategy signals and trading decisions."""
    
    __tablename__ = "strategy_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Signal identification
    strategy_name = Column(String(100), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Signal details
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    strength = Column(Float, nullable=True)  # Signal strength 0.0 - 1.0
    confidence = Column(Float, nullable=True)  # Confidence level 0.0 - 1.0
    
    # Market conditions
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    
    # Technical indicators (JSON for flexibility)
    indicators = Column(JSON, nullable=True)  # EMA, RSI, etc. values
    
    # Signal metadata
    reasoning = Column(Text, nullable=True)
    risk_score = Column(Float, nullable=True)
    
    # Execution status
    executed = Column(Boolean, default=False, index=True)
    execution_price = Column(Float, nullable=True)
    execution_timestamp = Column(DateTime, nullable=True)
    execution_trade_id = Column(String(100), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_signals_strategy_timestamp', 'strategy_name', 'timestamp'),
        Index('idx_signals_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_signals_user_executed', 'user_id', 'executed'),
    )


class Configuration(Base):
    """Persistent configuration storage."""
    
    __tablename__ = "configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for global config
    
    # Configuration identification
    category = Column(String(100), nullable=False, index=True)  # strategy, risk, system
    key = Column(String(200), nullable=False, index=True)
    
    # Configuration data
    value = Column(JSON, nullable=False)
    value_type = Column(String(50), nullable=False)  # int, float, string, dict, list, bool
    
    # Metadata
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False)  # For sensitive configs
    is_active = Column(Boolean, default=True)
    
    # Version control
    version = Column(Integer, default=1)
    previous_value = Column(JSON, nullable=True)
    
    # Validation
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    allowed_values = Column(JSON, nullable=True)  # List of allowed values
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'category', 'key', name='uix_user_category_key'),
        Index('idx_config_category_key', 'category', 'key'),
    )


class Alert(Base):
    """System alerts and notifications."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for system alerts
    
    # Alert classification
    alert_type = Column(String(50), nullable=False, index=True)  # risk, system, trading, performance
    severity = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    
    # Alert content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert context
    symbol = Column(String(20), nullable=True, index=True)
    strategy_name = Column(String(100), nullable=True)
    related_trade_id = Column(String(100), nullable=True)
    related_position_id = Column(Integer, nullable=True)
    
    # Alert data (JSON for flexibility)
    metadata = Column(JSON, nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Notification status
    email_sent = Column(Boolean, default=False)
    sms_sent = Column(Boolean, default=False)
    slack_sent = Column(Boolean, default=False)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_alerts_user_read', 'user_id', 'is_read'),
        Index('idx_alerts_severity_timestamp', 'severity', 'timestamp'),
        Index('idx_alerts_type_timestamp', 'alert_type', 'timestamp'),
    )