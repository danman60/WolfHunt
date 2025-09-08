"""Pytest configuration and fixtures for testing."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.src.main import create_application
from backend.src.database.base import Base, get_db
from backend.src.database.models import User
from backend.src.security.auth import hash_password
from backend.src.config.settings import get_settings

# Test database URL (use SQLite in memory for tests)
TEST_DATABASE_URL = "sqlite:///./test_wolfhunt.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def test_client(db_session):
    """Create a test FastAPI client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app = create_application()
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    user_data = {
        "email": "test@wolfhunt.trading",
        "username": "testuser",
        "hashed_password": hash_password("testpassword123"),
        "is_active": True,
        "is_superuser": False,
        "is_2fa_enabled": False,
        "trading_enabled": True,
        "paper_trading_mode": True
    }
    
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def authenticated_client(test_client, test_user):
    """Create an authenticated test client."""
    # Login to get token
    login_response = test_client.post("/api/auth/login", json={
        "email": test_user.email,
        "password": "testpassword123"
    })
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Set authorization header
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    
    return test_client


@pytest.fixture
def mock_dydx_client():
    """Mock dYdX API client for testing."""
    class MockDydxClient:
        async def get_account_info(self):
            return {
                "account": {
                    "equity": "10000.00",
                    "free_collateral": "9500.00",
                    "pending_deposits": "0.00",
                    "pending_withdrawals": "0.00"
                }
            }
        
        async def place_order(self, order_data):
            return {
                "order": {
                    "id": "test_order_123",
                    "client_id": order_data.get("client_id"),
                    "market": order_data["market"],
                    "side": order_data["side"],
                    "size": order_data["size"],
                    "price": order_data.get("price", "45000"),
                    "status": "PENDING",
                    "type": order_data["type"],
                    "created_at": "2024-01-01T00:00:00.000Z"
                }
            }
        
        async def cancel_order(self, order_id):
            return {"cancel": {"id": order_id}}
        
        async def get_positions(self):
            return {
                "positions": [
                    {
                        "market": "BTC-USD",
                        "side": "LONG",
                        "size": "0.001",
                        "entry_price": "45000",
                        "unrealized_pnl": "5.00",
                        "status": "OPEN"
                    }
                ]
            }
    
    return MockDydxClient()


@pytest.fixture
def mock_market_data():
    """Mock market data for testing."""
    return {
        "candles": [
            {
                "market": "BTC-USD",
                "resolution": "1m",
                "low": "44900",
                "high": "45100", 
                "open": "45000",
                "close": "45050",
                "base_token_volume": "10.5",
                "usd_volume": "472500",
                "trades": 25,
                "started_at": "2024-01-01T00:00:00.000Z"
            }
        ]
    }


@pytest.fixture
def sample_strategy_config():
    """Sample strategy configuration for testing."""
    return {
        "ema_fast_period": 12,
        "ema_slow_period": 26,
        "rsi_period": 14,
        "rsi_oversold": 30.0,
        "rsi_overbought": 70.0,
        "max_position_size_pct": 0.005,
        "max_leverage": 3.0,
        "stop_loss_pct": 0.02,
        "take_profit_ratio": 1.5,
        "daily_loss_limit": 0.02,
        "enabled": True,
        "paper_mode": True
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "order_id": "test_order_123",
        "symbol": "BTC-USD",
        "side": "BUY",
        "order_type": "MARKET",
        "size": 0.001,
        "price": 45000.00,
        "filled_size": 0.001,
        "notional_value": 45.00,
        "commission": 0.045,
        "status": "FILLED",
        "strategy_name": "MovingAverageCrossover",
        "timestamp": "2024-01-01T00:00:00.000Z"
    }


@pytest.fixture
def sample_position_data():
    """Sample position data for testing."""
    return {
        "symbol": "BTC-USD",
        "side": "LONG",
        "size": 0.001,
        "entry_price": 45000.00,
        "mark_price": 45100.00,
        "unrealized_pnl": 0.10,
        "unrealized_pnl_percent": 0.22,
        "notional_value": 45.10,
        "margin_used": 15.03,
        "leverage": 3.0,
        "strategy_name": "MovingAverageCrossover",
        "entry_reason": "EMA crossover signal"
    }