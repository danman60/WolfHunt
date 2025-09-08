"""Tests for database models."""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from backend.src.database.models import User, Trade, Position, StrategySignal, Configuration, Alert
from backend.src.security.auth import hash_password


class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password123"),
            is_active=True,
            trading_enabled=True,
            paper_trading_mode=True
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None
    
    def test_user_unique_email(self, db_session):
        """Test that user email must be unique."""
        user1 = User(
            email="test@example.com",
            username="testuser1",
            hashed_password=hash_password("password123")
        )
        user2 = User(
            email="test@example.com",
            username="testuser2",
            hashed_password=hash_password("password123")
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_unique_username(self, db_session):
        """Test that username must be unique."""
        user1 = User(
            email="test1@example.com",
            username="testuser",
            hashed_password=hash_password("password123")
        )
        user2 = User(
            email="test2@example.com",
            username="testuser",
            hashed_password=hash_password("password123")
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestTradeModel:
    """Test Trade model."""
    
    def test_create_trade(self, db_session, test_user):
        """Test creating a trade."""
        trade = Trade(
            user_id=test_user.id,
            order_id="test_order_123",
            symbol="BTC-USD",
            side="BUY",
            order_type="MARKET",
            size=0.001,
            price=45000.00,
            filled_size=0.001,
            notional_value=45.00,
            commission=0.045,
            status="FILLED",
            timestamp=datetime.utcnow()
        )
        
        db_session.add(trade)
        db_session.commit()
        db_session.refresh(trade)
        
        assert trade.id is not None
        assert trade.user_id == test_user.id
        assert trade.symbol == "BTC-USD"
        assert trade.status == "FILLED"
    
    def test_trade_unique_order_id(self, db_session, test_user):
        """Test that trade order_id must be unique."""
        trade1 = Trade(
            user_id=test_user.id,
            order_id="duplicate_order",
            symbol="BTC-USD",
            side="BUY",
            order_type="MARKET",
            size=0.001,
            price=45000.00,
            notional_value=45.00,
            status="FILLED",
            timestamp=datetime.utcnow()
        )
        trade2 = Trade(
            user_id=test_user.id,
            order_id="duplicate_order",
            symbol="ETH-USD",
            side="SELL",
            order_type="MARKET",
            size=0.01,
            price=3000.00,
            notional_value=30.00,
            status="FILLED",
            timestamp=datetime.utcnow()
        )
        
        db_session.add(trade1)
        db_session.commit()
        
        db_session.add(trade2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestPositionModel:
    """Test Position model."""
    
    def test_create_position(self, db_session, test_user):
        """Test creating a position."""
        position = Position(
            user_id=test_user.id,
            symbol="BTC-USD",
            side="LONG",
            size=0.001,
            entry_price=45000.00,
            mark_price=45100.00,
            unrealized_pnl=0.10,
            unrealized_pnl_percent=0.22,
            notional_value=45.10,
            margin_used=15.03,
            leverage=3.0,
            is_open=True,
            opened_at=datetime.utcnow()
        )
        
        db_session.add(position)
        db_session.commit()
        db_session.refresh(position)
        
        assert position.id is not None
        assert position.user_id == test_user.id
        assert position.symbol == "BTC-USD"
        assert position.is_open is True
    
    def test_position_unique_user_symbol_open(self, db_session, test_user):
        """Test that only one open position per user per symbol is allowed."""
        position1 = Position(
            user_id=test_user.id,
            symbol="BTC-USD",
            side="LONG",
            size=0.001,
            entry_price=45000.00,
            notional_value=45.00,
            margin_used=15.00,
            leverage=3.0,
            is_open=True,
            opened_at=datetime.utcnow()
        )
        position2 = Position(
            user_id=test_user.id,
            symbol="BTC-USD",
            side="LONG",
            size=0.002,
            entry_price=45500.00,
            notional_value=91.00,
            margin_used=30.33,
            leverage=3.0,
            is_open=True,
            opened_at=datetime.utcnow()
        )
        
        db_session.add(position1)
        db_session.commit()
        
        db_session.add(position2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestStrategySignalModel:
    """Test StrategySignal model."""
    
    def test_create_signal(self, db_session, test_user):
        """Test creating a strategy signal."""
        signal = StrategySignal(
            user_id=test_user.id,
            strategy_name="MovingAverageCrossover",
            symbol="BTC-USD",
            signal_type="BUY",
            strength=0.8,
            confidence=0.75,
            price=45000.00,
            indicators={"ema12": 44980, "ema26": 44920, "rsi": 65},
            reasoning="Fast EMA crossed above slow EMA",
            timestamp=datetime.utcnow()
        )
        
        db_session.add(signal)
        db_session.commit()
        db_session.refresh(signal)
        
        assert signal.id is not None
        assert signal.strategy_name == "MovingAverageCrossover"
        assert signal.signal_type == "BUY"
        assert signal.indicators["rsi"] == 65


class TestConfigurationModel:
    """Test Configuration model."""
    
    def test_create_global_config(self, db_session):
        """Test creating a global configuration."""
        config = Configuration(
            user_id=None,  # Global config
            category="strategy",
            key="ema_fast_period",
            value=12,
            value_type="int",
            description="Fast EMA period for crossover strategy"
        )
        
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)
        
        assert config.id is not None
        assert config.user_id is None
        assert config.category == "strategy"
        assert config.value == 12
    
    def test_create_user_config(self, db_session, test_user):
        """Test creating a user-specific configuration."""
        config = Configuration(
            user_id=test_user.id,
            category="strategy",
            key="ema_fast_period",
            value=15,
            value_type="int",
            description="User-specific fast EMA period"
        )
        
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)
        
        assert config.id is not None
        assert config.user_id == test_user.id
        assert config.value == 15
    
    def test_config_unique_user_category_key(self, db_session, test_user):
        """Test that configuration key must be unique per user/category."""
        config1 = Configuration(
            user_id=test_user.id,
            category="strategy",
            key="ema_fast_period",
            value=12,
            value_type="int"
        )
        config2 = Configuration(
            user_id=test_user.id,
            category="strategy",
            key="ema_fast_period",
            value=15,
            value_type="int"
        )
        
        db_session.add(config1)
        db_session.commit()
        
        db_session.add(config2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestAlertModel:
    """Test Alert model."""
    
    def test_create_user_alert(self, db_session, test_user):
        """Test creating a user alert."""
        alert = Alert(
            user_id=test_user.id,
            alert_type="trading",
            severity="INFO",
            title="Trade Executed",
            message="Successfully bought 0.001 BTC at $45,000",
            symbol="BTC-USD",
            strategy_name="MovingAverageCrossover",
            metadata={"trade_id": "test_order_123", "pnl": 0},
            timestamp=datetime.utcnow()
        )
        
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        assert alert.id is not None
        assert alert.user_id == test_user.id
        assert alert.alert_type == "trading"
        assert alert.severity == "INFO"
        assert alert.metadata["trade_id"] == "test_order_123"
    
    def test_create_system_alert(self, db_session):
        """Test creating a system alert."""
        alert = Alert(
            user_id=None,  # System alert
            alert_type="system",
            severity="WARNING",
            title="High CPU Usage",
            message="CPU usage is above 90%",
            metadata={"cpu_percent": 95.2},
            timestamp=datetime.utcnow()
        )
        
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        assert alert.id is not None
        assert alert.user_id is None
        assert alert.alert_type == "system"
        assert alert.severity == "WARNING"