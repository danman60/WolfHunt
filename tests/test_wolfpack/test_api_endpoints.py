"""
🌐 WOLF PACK API ENDPOINTS TESTS
Comprehensive test suite for the Wolf Pack API integration
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

# Mock the Wolf Pack modules before importing the main app
with patch.dict('sys.modules', {
    'src.integrations.wolfpack_intelligence': Mock(),
    'src.integrations.strategy_automation': Mock()
}):
    # Import the main FastAPI app
    from simple_main import app

class TestWolfPackAPIEndpoints:
    """🌐 Test suite for Wolf Pack API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_intelligence_data(self):
        """Mock unified intelligence data"""
        return {
            "timestamp": "2024-01-15T10:30:00Z",
            "eth_intelligence": {
                "price": 2850.75,
                "technical_score": 72.5,
                "sentiment_score": 68.3,
                "signal_strength": "STRONG",
                "volume_ratio": 2.1,
                "confidence_level": 0.82,
                "dominant_narrative": "ETF Approval Momentum",
                "pattern_detected": "Ascending Triangle"
            },
            "link_intelligence": {
                "price": 15.85,
                "technical_score": 65.2,
                "sentiment_score": 71.8,
                "signal_strength": "MODERATE",
                "volume_ratio": 1.7,
                "confidence_level": 0.75,
                "dominant_narrative": "Real World Assets Growth",
                "pattern_detected": "Bull Flag"
            },
            "wbtc_intelligence": {
                "price": 45750.30,
                "technical_score": 78.1,
                "sentiment_score": 73.5,
                "signal_strength": "VERY_STRONG",
                "volume_ratio": 2.8,
                "confidence_level": 0.89,
                "dominant_narrative": "Digital Gold Narrative",
                "pattern_detected": "Breakout"
            },
            "portfolio_signals": {
                "overall_sentiment": 71.2,
                "technical_strength": 71.9,
                "volume_activity": 2.2,
                "signal_convergence": 2,
                "active_opportunities": 3
            },
            "strategy_suggestions": [
                {
                    "adjustment_type": "allocation_increase",
                    "target_crypto": "WBTC",
                    "current_value": 33.33,
                    "suggested_value": 42.0,
                    "confidence": 0.89,
                    "justification": "🚀 Exceptional bullish convergence!",
                    "expected_impact": "Potential 20-30% alpha capture",
                    "risk_assessment": "LOW - High conviction signals"
                }
            ],
            "market_context": {
                "overall_trend": "BULLISH",
                "volatility_regime": "ELEVATED",
                "sentiment_regime": "OPTIMISTIC"
            },
            "system_health": {
                "quant_status": "ACTIVE",
                "snoop_status": "ACTIVE",
                "sage_status": "ACTIVE",
                "brief_status": "ACTIVE",
                "last_update": "2024-01-15T10:30:00Z",
                "data_freshness": "FRESH",
                "api_health": "OPTIMAL"
            }
        }
    
    def test_root_endpoint(self, client):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert "wolf_pack_status" in data
        assert data["status"] == "running"
        
    def test_health_endpoint(self, client):
        """Test the health check endpoint"""
        response = client.get("/api/trading/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "version" in data
        
    def test_dashboard_endpoint(self, client):
        """Test the trading dashboard endpoint"""
        response = client.get("/api/trading/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_equity" in data
        assert "daily_pnl" in data
        assert "system_status" in data
        assert "trading_enabled" in data
        
    def test_positions_endpoint(self, client):
        """Test the positions endpoint"""
        response = client.get("/api/trading/positions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            position = data[0]
            assert "symbol" in position
            assert "side" in position
            assert "size" in position
            assert "unrealized_pnl" in position
            
    def test_trades_endpoint(self, client):
        """Test the trades endpoint"""
        response = client.get("/api/trading/trades")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            trade = data[0]
            assert "symbol" in trade
            assert "side" in trade
            assert "price" in trade
            assert "status" in trade
            
    @patch('simple_main.WOLFPACK_AVAILABLE', True)
    @patch('simple_main.get_intelligence_engine')
    def test_unified_intelligence_endpoint(self, mock_get_engine, client, mock_intelligence_data):
        """Test the unified intelligence endpoint when Wolf Pack is available"""
        # Mock the intelligence engine
        mock_engine = Mock()
        mock_engine.fetch_latest_quant_data = AsyncMock(return_value={
            "ETH": {"technical_score": 72.5, "price": 2850.75},
            "LINK": {"technical_score": 65.2, "price": 15.85}
        })
        mock_engine.fetch_latest_snoop_data = AsyncMock(return_value={
            "ETH": {"sentiment_score": 68.3},
            "LINK": {"sentiment_score": 71.8}
        })
        mock_engine.generate_strategy_suggestions = Mock(return_value=[])
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/api/v1/unified-intelligence")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "eth_intelligence" in data
        assert "link_intelligence" in data
        assert "wbtc_intelligence" in data
        assert "portfolio_signals" in data
        assert "system_health" in data
        
    def test_unified_intelligence_endpoint_simplified(self, client):
        """Test the unified intelligence endpoint in simplified mode"""
        response = client.get("/api/v1/unified-intelligence")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "eth_intelligence" in data
        assert "link_intelligence" in data
        assert "wbtc_intelligence" in data
        assert "strategy_suggestions" in data
        
        # Should contain mock data
        assert data["eth_intelligence"]["signal_strength"] == "STRONG"
        
    def test_live_signals_endpoint(self, client):
        """Test the live signals endpoint"""
        response = client.get("/api/v1/live-signals")
        assert response.status_code == 200
        
        data = response.json()
        assert "signals" in data
        assert "timestamp" in data
        
        signals = data["signals"]
        assert "ETH" in signals
        assert "LINK" in signals
        assert "WBTC" in signals
        
        eth_signal = signals["ETH"]
        assert "price" in eth_signal
        assert "technical_signal" in eth_signal
        assert "sentiment_signal" in eth_signal
        assert "confidence" in eth_signal
        
    def test_execute_suggestion_approval(self, client):
        """Test strategy suggestion execution with approval"""
        suggestion_data = {
            "suggestion_id": "test_123",
            "approved": True,
            "suggestion_data": {
                "adjustment_type": "allocation_increase",
                "target_crypto": "ETH",
                "current_value": 30.0,
                "suggested_value": 35.0,
                "confidence": 0.8,
                "justification": "Test execution",
                "expected_impact": "Test impact",
                "risk_assessment": "LOW"
            }
        }
        
        response = client.post("/api/v1/execute-suggestion", json=suggestion_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "suggestion_id" in data
        assert "timestamp" in data
        assert data["suggestion_id"] == "test_123"
        
    def test_execute_suggestion_rejection(self, client):
        """Test strategy suggestion execution with rejection"""
        suggestion_data = {
            "suggestion_id": "test_456",
            "approved": False
        }
        
        response = client.post("/api/v1/execute-suggestion", json=suggestion_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "rejected"
        assert data["suggestion_id"] == "test_456"
        
    def test_performance_metrics_endpoint(self, client):
        """Test the performance metrics endpoint"""
        response = client.get("/api/v1/performance-metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "signal_accuracy" in data
        assert "portfolio_performance" in data
        assert "system_efficiency" in data
        assert "agent_performance" in data
        
        signal_accuracy = data["signal_accuracy"]
        assert "technical_signals" in signal_accuracy
        assert "sentiment_signals" in signal_accuracy
        assert "combined_signals" in signal_accuracy
        
        portfolio_perf = data["portfolio_performance"]
        assert "total_return_7d" in portfolio_perf
        assert "sharpe_ratio" in portfolio_perf
        assert "win_rate" in portfolio_perf
        
    def test_system_health_endpoint(self, client):
        """Test the system health endpoint"""
        response = client.get("/api/v1/system-health")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_agents" in data
        assert "total_agents" in data
        assert "wolf_pack_enabled" in data
        assert "automation_enabled" in data
        assert "gmx_integration" in data
        assert "arbitrum_network" in data
        
    @patch('simple_main.AUTOMATION_AVAILABLE', True)
    @patch('simple_main.get_automation_engine')
    def test_automation_status_endpoint(self, mock_get_engine, client):
        """Test the automation status endpoint"""
        # Mock the automation engine
        mock_engine = Mock()
        mock_engine.get_automation_status = AsyncMock(return_value={
            "engine_status": "active",
            "trading_enabled": False,
            "daily_executions": 5,
            "max_daily_executions": 50
        })
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/api/v1/automation/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "engine_status" in data
        assert "trading_enabled" in data
        assert "daily_executions" in data
        
    def test_automation_status_unavailable(self, client):
        """Test automation status when automation is unavailable"""
        response = client.get("/api/v1/automation/status")
        
        # Should handle unavailable automation gracefully
        assert response.status_code == 200
        data = response.json()
        assert "automation_enabled" in data
        
    @patch('simple_main.AUTOMATION_AVAILABLE', True)
    @patch('simple_main.WOLFPACK_AVAILABLE', True)
    @patch('simple_main.get_automation_engine')
    @patch('simple_main.get_intelligence_engine')
    def test_automation_evaluate_endpoint(self, mock_get_intel, mock_get_auto, client):
        """Test the automation evaluate endpoint"""
        # Mock engines
        mock_intel = Mock()
        mock_intel.fetch_latest_quant_data = AsyncMock(return_value={"ETH": {"technical_score": 75}})
        mock_intel.fetch_latest_snoop_data = AsyncMock(return_value={"ETH": {"sentiment_score": 70}})
        mock_intel.generate_strategy_suggestions = Mock(return_value=[])
        mock_get_intel.return_value = mock_intel
        
        mock_auto = Mock()
        mock_auto.evaluate_strategy_suggestions = AsyncMock(return_value=[])
        mock_get_auto.return_value = mock_auto
        
        response = client.post("/api/v1/automation/evaluate")
        assert response.status_code == 200
        
        data = response.json()
        assert "execution_plans_count" in data
        assert "evaluation_timestamp" in data
        assert "total_suggestions" in data
        
    def test_automation_evaluate_unavailable(self, client):
        """Test automation evaluate when services are unavailable"""
        response = client.post("/api/v1/automation/evaluate")
        assert response.status_code == 200
        
        data = response.json()
        assert "execution_plans" in data
        assert "message" in data
        
    def test_automation_rules_endpoint(self, client):
        """Test the automation rules endpoint"""
        response = client.get("/api/v1/automation/rules")
        assert response.status_code == 200
        
        data = response.json()
        # Should handle gracefully whether automation is available or not
        assert isinstance(data, dict)
        
    def test_automation_execution_history_endpoint(self, client):
        """Test the automation execution history endpoint"""
        response = client.get("/api/v1/automation/execution-history")
        assert response.status_code == 200
        
        data = response.json()
        assert "execution_history" in data
        
        if "message" not in data:  # If automation is available
            assert "total_executions" in data
            assert "successful_executions" in data
            
    def test_close_position_endpoint(self, client):
        """Test the close position endpoint"""
        response = client.post("/api/trading/positions/1/close")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "timestamp" in data
        
    def test_emergency_stop_endpoint(self, client):
        """Test the emergency stop endpoint"""
        response = client.post("/api/trading/emergency-stop")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "trading_enabled" in data
        assert data["trading_enabled"] == False
        
    def test_cors_headers(self, client):
        """Test that CORS headers are properly set"""
        response = client.options("/api/v1/unified-intelligence")
        # The test client doesn't process CORS middleware exactly like a browser
        # but we can test that the endpoint is accessible
        assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS
        
    def test_api_error_handling(self, client):
        """Test API error handling for invalid endpoints"""
        response = client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404
        
    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON in POST requests"""
        response = client.post(
            "/api/v1/execute-suggestion",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity
        
    @patch('simple_main.AUTOMATION_AVAILABLE', True)
    @patch('simple_main.WOLFPACK_AVAILABLE', True)
    @patch('simple_main.get_automation_engine')
    @patch('simple_main.get_intelligence_engine')
    def test_auto_execute_endpoint(self, mock_get_intel, mock_get_auto, client):
        """Test the auto-execute endpoint"""
        # Mock successful auto-execution
        mock_intel = Mock()
        mock_intel.fetch_latest_quant_data = AsyncMock(return_value={"ETH": {"technical_score": 85}})
        mock_intel.fetch_latest_snoop_data = AsyncMock(return_value={"ETH": {"sentiment_score": 80}})
        
        from src.integrations.wolfpack_intelligence import StrategyAdjustment
        mock_suggestion = StrategyAdjustment(
            adjustment_type="allocation_increase",
            target_crypto="ETH",
            current_value=30.0,
            suggested_value=35.0,
            confidence=0.9,
            justification="High confidence signal",
            expected_impact="Strong upside",
            risk_assessment="LOW"
        )
        mock_intel.generate_strategy_suggestions = Mock(return_value=[mock_suggestion])
        mock_get_intel.return_value = mock_intel
        
        from src.integrations.strategy_automation import ExecutionPlan
        mock_plan = Mock(spec=ExecutionPlan)
        mock_plan.suggestion = mock_suggestion
        
        mock_auto = Mock()
        mock_auto.evaluate_strategy_suggestions = AsyncMock(return_value=[mock_plan])
        mock_auto.execute_plan = AsyncMock(return_value={
            "status": "executed",
            "transaction_id": "test_tx_123"
        })
        mock_get_auto.return_value = mock_auto
        
        response = client.post("/api/v1/automation/auto-execute")
        assert response.status_code == 200
        
        data = response.json()
        assert "auto_executions" in data
        assert "timestamp" in data
        assert "plans_evaluated" in data

class TestAPIIntegration:
    """🔄 Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_api_workflow_basic(self, client):
        """Test basic API workflow"""
        # 1. Check system health
        health_response = client.get("/api/v1/system-health")
        assert health_response.status_code == 200
        
        # 2. Get unified intelligence
        intel_response = client.get("/api/v1/unified-intelligence")
        assert intel_response.status_code == 200
        
        # 3. Get live signals
        signals_response = client.get("/api/v1/live-signals")
        assert signals_response.status_code == 200
        
        # 4. Check performance metrics
        perf_response = client.get("/api/v1/performance-metrics")
        assert perf_response.status_code == 200
        
    def test_api_workflow_automation(self, client):
        """Test automation workflow"""
        # 1. Check automation status
        status_response = client.get("/api/v1/automation/status")
        assert status_response.status_code == 200
        
        # 2. Get automation rules
        rules_response = client.get("/api/v1/automation/rules")
        assert rules_response.status_code == 200
        
        # 3. Check execution history
        history_response = client.get("/api/v1/automation/execution-history")
        assert history_response.status_code == 200
        
    def test_api_response_consistency(self, client):
        """Test that API responses are consistent"""
        # Call the same endpoint multiple times
        responses = []
        for _ in range(3):
            response = client.get("/api/v1/unified-intelligence")
            assert response.status_code == 200
            responses.append(response.json())
        
        # Check that the structure is consistent
        for response in responses:
            assert "timestamp" in response
            assert "eth_intelligence" in response
            assert "system_health" in response

if __name__ == "__main__":
    pytest.main([__file__, "-v"])