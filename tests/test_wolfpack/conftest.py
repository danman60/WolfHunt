"""
🧪 WOLF PACK TEST CONFIGURATION
Shared test fixtures and configuration for Wolf Pack test suite
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch
import asyncio

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'WOLF_PACK_TRADING_ENABLED': 'false',
        'GMX_ACCOUNT_ADDRESS': '0x1234567890123456789012345678901234567890',
        'GMX_PRIVATE_KEY': 'test_private_key',
        'GMX_RPC_URL': 'https://test.arbitrum.io',
        'GOOGLE_SHEETS_ID': 'test_sheets_id',
        'GOOGLE_SHEETS_API_KEY': None,  # Force mock mode
        'DATABASE_URL': 'sqlite:///:memory:',
        'REDIS_URL': None  # Use no Redis for testing
    }):
        yield

@pytest.fixture
def mock_gmx_sdk():
    """Mock the GMX SDK modules that might not be available"""
    with patch.dict('sys.modules', {
        'gmx_python_sdk.scripts.v2.gmx_utils': Mock(),
        'gmx_python_sdk.scripts.v2.order.create_order': Mock(),
        'gmx_python_sdk.scripts.v2.order.create_order_utils': Mock(),
        'gmx_python_sdk.scripts.v2.get.get_markets': Mock(),
        'gmx_python_sdk.scripts.v2.get.get_oracle_prices': Mock(),
        'gmx_python_sdk.scripts.v2.get.get_positions': Mock(),
    }):
        yield

@pytest.fixture
def sample_crypto_data():
    """Sample cryptocurrency data for testing"""
    return {
        "ETH": {
            "price": 2850.75,
            "technical_score": 72.5,
            "sentiment_score": 68.3,
            "signal_strength": "STRONG",
            "volume_ratio": 2.1,
            "confidence_level": 0.82,
            "dominant_narrative": "ETF Approval Momentum",
            "pattern_detected": "Ascending Triangle",
            "rsi": 72.5,
            "macd_signal": "BULLISH",
            "sma_trend": "UPTREND",
            "bb_position": "UPPER",
            "support_level": 2750.0,
            "resistance_level": 2950.0,
            "data_quality": "GOOD"
        },
        "LINK": {
            "price": 15.85,
            "technical_score": 65.2,
            "sentiment_score": 71.8,
            "signal_strength": "MODERATE",
            "volume_ratio": 1.7,
            "confidence_level": 0.75,
            "dominant_narrative": "Real World Assets Growth",
            "pattern_detected": "Bull Flag",
            "rsi": 65.2,
            "macd_signal": "NEUTRAL",
            "sma_trend": "UPTREND",
            "bb_position": "MIDDLE",
            "support_level": 14.50,
            "resistance_level": 17.00,
            "data_quality": "GOOD"
        },
        "WBTC": {
            "price": 45750.30,
            "technical_score": 78.1,
            "sentiment_score": 73.5,
            "signal_strength": "VERY_STRONG",
            "volume_ratio": 2.8,
            "confidence_level": 0.89,
            "dominant_narrative": "Digital Gold Narrative",
            "pattern_detected": "Breakout",
            "rsi": 78.1,
            "macd_signal": "BULLISH",
            "sma_trend": "UPTREND",
            "bb_position": "UPPER",
            "support_level": 44000.0,
            "resistance_level": 47000.0,
            "data_quality": "GOOD"
        }
    }

@pytest.fixture
def sample_portfolio_state():
    """Sample portfolio state for testing"""
    return {
        "total_equity": 100000.0,
        "available_margin": 85000.0,
        "current_positions": {
            "ETH": 0.25,
            "LINK": 0.15,
            "WBTC": 0.35,
            "BTC": 0.25
        },
        "daily_trades_count": 3,
        "last_trade_time": "2024-01-15T10:30:00Z",
        "risk_metrics": {
            "portfolio_var": 0.03,
            "max_drawdown": 0.08,
            "sharpe_ratio": 1.8
        }
    }

@pytest.fixture
def mock_database():
    """Mock database for testing"""
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.close.return_value = None
    return mock_db

# Test markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.api = pytest.mark.api
pytest.mark.automation = pytest.mark.automation
pytest.mark.intelligence = pytest.mark.intelligence