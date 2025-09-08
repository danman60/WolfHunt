"""Tests for trading API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


class TestTradingEndpoints:
    """Test trading endpoints."""
    
    def test_get_dashboard_data_unauthorized(self, test_client: TestClient):
        """Test dashboard endpoint without authentication."""
        response = test_client.get("/api/trading/dashboard")
        assert response.status_code == 401
    
    def test_get_dashboard_data(self, authenticated_client: TestClient):
        """Test dashboard endpoint with authentication."""
        response = authenticated_client.get("/api/trading/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_equity" in data
        assert "account_balance" in data
        assert "daily_pnl" in data
        assert "unrealized_pnl" in data
        assert "system_status" in data
        assert "trading_enabled" in data
    
    def test_get_positions_empty(self, authenticated_client: TestClient):
        """Test getting positions when none exist."""
        response = authenticated_client.get("/api/trading/positions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_positions_with_symbol_filter(self, authenticated_client: TestClient):
        """Test getting positions with symbol filter."""
        response = authenticated_client.get("/api/trading/positions?symbol=BTC-USD")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_trade_history_empty(self, authenticated_client: TestClient):
        """Test getting trade history when none exist."""
        response = authenticated_client.get("/api/trading/trades")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_trade_history_with_filters(self, authenticated_client: TestClient):
        """Test getting trade history with filters."""
        params = {
            "limit": 50,
            "offset": 0,
            "symbol": "BTC-USD",
            "strategy": "MovingAverageCrossover"
        }
        
        response = authenticated_client.get("/api/trading/trades", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_strategy_config(self, authenticated_client: TestClient):
        """Test getting strategy configuration."""
        response = authenticated_client.get("/api/trading/strategy/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "strategy_name" in data
        assert "ema_fast_period" in data
        assert "ema_slow_period" in data
        assert "max_position_size_pct" in data
        assert "enabled" in data
    
    def test_update_strategy_config(self, authenticated_client: TestClient, sample_strategy_config):
        """Test updating strategy configuration."""
        response = authenticated_client.post("/api/trading/strategy/config", json=sample_strategy_config)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ema_fast_period"] == sample_strategy_config["ema_fast_period"]
        assert data["ema_slow_period"] == sample_strategy_config["ema_slow_period"]
        assert data["enabled"] == sample_strategy_config["enabled"]
    
    def test_update_strategy_config_invalid_data(self, authenticated_client: TestClient):
        """Test updating strategy configuration with invalid data."""
        invalid_config = {
            "ema_fast_period": 50,  # Greater than slow period
            "ema_slow_period": 26,
            "enabled": True
        }
        
        response = authenticated_client.post("/api/trading/strategy/config", json=invalid_config)
        assert response.status_code == 422  # Validation error
    
    def test_emergency_stop(self, authenticated_client: TestClient):
        """Test emergency stop functionality."""
        stop_data = {
            "reason": "Test emergency stop for safety",
            "close_positions": False
        }
        
        response = authenticated_client.post("/api/trading/emergency-stop", json=stop_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["trading_enabled"] is False
    
    def test_resume_trading(self, authenticated_client: TestClient):
        """Test resuming trading after emergency stop."""
        # First stop trading
        stop_data = {
            "reason": "Test stop before resume",
            "close_positions": False
        }
        authenticated_client.post("/api/trading/emergency-stop", json=stop_data)
        
        # Then resume
        response = authenticated_client.post("/api/trading/resume-trading")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["trading_enabled"] is True
    
    def test_get_performance_metrics_no_trades(self, authenticated_client: TestClient):
        """Test performance metrics when no trades exist."""
        response = authenticated_client.get("/api/trading/performance?days=30")
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_days"] == 30
        assert data["error"] == "No trades in the specified period"
    
    def test_get_signals_empty(self, authenticated_client: TestClient):
        """Test getting signals when none exist."""
        response = authenticated_client.get("/api/trading/signals")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_signals_with_filters(self, authenticated_client: TestClient):
        """Test getting signals with filters."""
        params = {
            "limit": 25,
            "strategy": "MovingAverageCrossover",
            "symbol": "BTC-USD"
        }
        
        response = authenticated_client.get("/api/trading/signals", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_trading_health(self, authenticated_client: TestClient):
        """Test trading health endpoint."""
        response = authenticated_client.get("/api/trading/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "version" in data


class TestTradingIntegration:
    """Integration tests for trading functionality."""
    
    @patch('backend.src.trading.api_client.DydxRestClient')
    def test_place_order_integration(self, mock_client, authenticated_client: TestClient, mock_dydx_client):
        """Test order placement integration."""
        mock_client.return_value = mock_dydx_client
        
        # This would test actual order placement if implemented
        # For now, just ensure the endpoint structure exists
        response = authenticated_client.get("/api/trading/health")
        assert response.status_code == 200
    
    @patch('backend.src.trading.market_data.websocket_manager.DydxWebSocketManager')
    def test_market_data_integration(self, mock_ws, authenticated_client: TestClient):
        """Test market data integration."""
        mock_ws.return_value.connect = AsyncMock()
        mock_ws.return_value.subscribe_candles = AsyncMock()
        
        # Test that market data endpoints are accessible
        response = authenticated_client.get("/api/trading/dashboard")
        assert response.status_code == 200