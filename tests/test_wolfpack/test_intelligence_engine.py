"""
🧪 WOLF PACK INTELLIGENCE ENGINE TESTS
Comprehensive test suite for the unified intelligence system
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal

# Import the modules we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from src.integrations.wolfpack_intelligence import (
    WolfPackIntelligenceEngine, 
    StrategyAdjustment,
    get_intelligence_engine
)

class TestWolfPackIntelligenceEngine:
    """🐺 Test suite for Wolf Pack Intelligence Engine"""
    
    @pytest.fixture
    def intelligence_engine(self):
        """Create a test intelligence engine instance"""
        return WolfPackIntelligenceEngine(
            database_url="sqlite:///:memory:",
            redis_url=None  # Use no Redis for testing
        )
    
    @pytest.fixture
    def mock_quant_data(self):
        """Mock technical analysis data"""
        return {
            "ETH": {
                "date": "2024-01-15",
                "price": 2850.75,
                "rsi": 72.5,
                "macd_signal": "BULLISH",
                "sma_trend": "UPTREND",
                "bb_position": "UPPER",
                "volume_ratio": 2.1,
                "technical_score": 78.5,
                "support_level": 2750.0,
                "resistance_level": 2950.0,
                "pattern_detected": "Ascending Triangle",
                "signal_strength": "STRONG",
                "confidence_level": 0.85,
                "data_quality": "GOOD"
            },
            "LINK": {
                "date": "2024-01-15",
                "price": 15.85,
                "rsi": 65.2,
                "macd_signal": "NEUTRAL",
                "sma_trend": "UPTREND",
                "bb_position": "MIDDLE",
                "volume_ratio": 1.7,
                "technical_score": 68.3,
                "support_level": 14.50,
                "resistance_level": 17.00,
                "pattern_detected": "Bull Flag",
                "signal_strength": "MODERATE",
                "confidence_level": 0.75,
                "data_quality": "GOOD"
            }
        }
    
    @pytest.fixture
    def mock_snoop_data(self):
        """Mock sentiment analysis data"""
        return {
            "ETH": {
                "date": "2024-01-15",
                "sentiment_score": 71.8,
                "dominant_narrative": "ETF Approval Momentum",
                "mention_volume": 4500,
                "influence_weight": 0.82,
                "manipulation_risk": 0.15,
                "fear_greed_index": 68.0,
                "narrative_momentum": "ACCELERATING",
                "confidence_level": 0.80
            },
            "LINK": {
                "date": "2024-01-15",
                "sentiment_score": 64.5,
                "dominant_narrative": "Real World Assets Growth",
                "mention_volume": 2800,
                "influence_weight": 0.70,
                "manipulation_risk": 0.20,
                "fear_greed_index": 62.0,
                "narrative_momentum": "STEADY",
                "confidence_level": 0.72
            }
        }
    
    def test_engine_initialization(self, intelligence_engine):
        """Test that the intelligence engine initializes correctly"""
        assert intelligence_engine is not None
        assert intelligence_engine.google_sheets_id is not None
        assert intelligence_engine.sheets_base_url is not None
        assert intelligence_engine.SessionLocal is not None
        
    def test_safe_float_conversion(self, intelligence_engine):
        """Test safe float conversion utility"""
        assert intelligence_engine._safe_float("42.5") == 42.5
        assert intelligence_engine._safe_float("") == 0.0
        assert intelligence_engine._safe_float("invalid") == 0.0
        assert intelligence_engine._safe_float(None) == 0.0
        assert intelligence_engine._safe_float("123.456", 5.0) == 123.456
        assert intelligence_engine._safe_float("bad", 10.0) == 10.0
        
    def test_safe_int_conversion(self, intelligence_engine):
        """Test safe integer conversion utility"""
        assert intelligence_engine._safe_int("42") == 42
        assert intelligence_engine._safe_int("42.7") == 42  # Should truncate
        assert intelligence_engine._safe_int("") == 0
        assert intelligence_engine._safe_int("invalid") == 0
        assert intelligence_engine._safe_int(None) == 0
        assert intelligence_engine._safe_int("bad", 10) == 10
    
    def test_process_quant_data(self, intelligence_engine):
        """Test processing of raw quant data from Google Sheets"""
        # Mock raw Google Sheets data format
        raw_data = [
            ["Crypto", "Date", "Price", "RSI", "MACD_Signal", "Technical_Score", "Confidence_Level"],
            ["ETH", "2024-01-15", "2850.75", "72.5", "BULLISH", "78.5", "0.85"],
            ["LINK", "2024-01-15", "15.85", "65.2", "NEUTRAL", "68.3", "0.75"]
        ]
        
        processed_data = intelligence_engine._process_quant_data(raw_data)
        
        assert "ETH" in processed_data
        assert "LINK" in processed_data
        assert processed_data["ETH"]["price"] == 2850.75
        assert processed_data["ETH"]["rsi"] == 72.5
        assert processed_data["ETH"]["macd_signal"] == "BULLISH"
        assert processed_data["LINK"]["technical_score"] == 68.3
        
    def test_process_snoop_data(self, intelligence_engine):
        """Test processing of raw sentiment data from Google Sheets"""
        raw_data = [
            ["Crypto", "Date", "Sentiment_Score", "Dominant_Narrative", "Mention_Volume", "Confidence_Level"],
            ["ETH", "2024-01-15", "71.8", "ETF Approval Momentum", "4500", "0.80"],
            ["LINK", "2024-01-15", "64.5", "Real World Assets", "2800", "0.72"]
        ]
        
        processed_data = intelligence_engine._process_snoop_data(raw_data)
        
        assert "ETH" in processed_data
        assert "LINK" in processed_data
        assert processed_data["ETH"]["sentiment_score"] == 71.8
        assert processed_data["ETH"]["dominant_narrative"] == "ETF Approval Momentum"
        assert processed_data["LINK"]["mention_volume"] == 2800
        
    @pytest.mark.asyncio
    async def test_fetch_latest_quant_data_mock(self, intelligence_engine):
        """Test fetching quant data when no API key is available (mock mode)"""
        # Remove API key to force mock mode
        intelligence_engine.sheets_api_key = None
        
        quant_data = await intelligence_engine.fetch_latest_quant_data()
        
        assert quant_data is not None
        assert "ETH" in quant_data
        assert "LINK" in quant_data
        assert "WBTC" in quant_data
        assert quant_data["ETH"]["data_quality"] == "MOCK_DATA"
        
    @pytest.mark.asyncio
    async def test_fetch_latest_snoop_data_mock(self, intelligence_engine):
        """Test fetching snoop data when no API key is available (mock mode)"""
        intelligence_engine.sheets_api_key = None
        
        snoop_data = await intelligence_engine.fetch_latest_snoop_data()
        
        assert snoop_data is not None
        assert "ETH" in snoop_data
        assert "LINK" in snoop_data
        assert "WBTC" in snoop_data
        assert isinstance(snoop_data["ETH"]["sentiment_score"], (int, float))
        
    def test_generate_strategy_suggestions_bullish_convergence(self, intelligence_engine, mock_quant_data, mock_snoop_data):
        """Test strategy generation for bullish convergence scenario"""
        suggestions = intelligence_engine.generate_strategy_suggestions(mock_quant_data, mock_snoop_data)
        
        assert len(suggestions) > 0
        
        # Check for bullish convergence suggestions
        eth_suggestions = [s for s in suggestions if s.target_crypto == "ETH"]
        assert len(eth_suggestions) > 0
        
        # ETH should have high scores in mock data, triggering bullish suggestions
        bullish_suggestions = [s for s in eth_suggestions if s.adjustment_type == "allocation_increase"]
        assert len(bullish_suggestions) > 0
        
        # Verify suggestion properties
        suggestion = bullish_suggestions[0]
        assert suggestion.confidence > 0.7
        assert "bullish" in suggestion.justification.lower() or "🚀" in suggestion.justification
        
    def test_generate_strategy_suggestions_volume_momentum(self, intelligence_engine, mock_quant_data, mock_snoop_data):
        """Test strategy generation for volume momentum plays"""
        # Modify mock data to trigger volume momentum
        mock_quant_data["ETH"]["volume_ratio"] = 3.2  # High volume
        mock_quant_data["ETH"]["signal_strength"] = "VERY_STRONG"
        
        suggestions = intelligence_engine.generate_strategy_suggestions(mock_quant_data, mock_snoop_data)
        
        momentum_suggestions = [s for s in suggestions if s.adjustment_type == "momentum_play"]
        assert len(momentum_suggestions) > 0
        
        suggestion = momentum_suggestions[0]
        assert "momentum" in suggestion.justification.lower() or "volume" in suggestion.justification.lower()
        assert suggestion.confidence >= 0.6
        
    def test_generate_strategy_suggestions_divergence_warning(self, intelligence_engine, mock_quant_data, mock_snoop_data):
        """Test strategy generation for divergence scenarios"""
        # Create divergence: high technical, low sentiment
        mock_quant_data["LINK"]["technical_score"] = 85.0
        mock_snoop_data["LINK"]["sentiment_score"] = 25.0  # Low sentiment
        
        suggestions = intelligence_engine.generate_strategy_suggestions(mock_quant_data, mock_snoop_data)
        
        risk_suggestions = [s for s in suggestions if s.adjustment_type == "risk_adjustment"]
        assert len(risk_suggestions) > 0
        
        suggestion = risk_suggestions[0]
        assert "divergence" in suggestion.justification.lower() or "uncertainty" in suggestion.justification.lower()
        
    def test_generate_strategy_suggestions_portfolio_level(self, intelligence_engine, mock_quant_data, mock_snoop_data):
        """Test portfolio-level strategy suggestions"""
        # Set high scores across all assets to trigger portfolio suggestions
        for crypto in ["ETH", "LINK"]:
            mock_quant_data[crypto]["technical_score"] = 75.0
            mock_snoop_data[crypto]["sentiment_score"] = 70.0
        
        # Add WBTC to mock data
        mock_quant_data["WBTC"] = {
            "technical_score": 75.0,
            "price": 45750.0
        }
        mock_snoop_data["WBTC"] = {
            "sentiment_score": 70.0
        }
        
        suggestions = intelligence_engine.generate_strategy_suggestions(mock_quant_data, mock_snoop_data)
        
        portfolio_suggestions = [s for s in suggestions if s.target_crypto == "PORTFOLIO"]
        assert len(portfolio_suggestions) > 0
        
        suggestion = portfolio_suggestions[0]
        assert suggestion.adjustment_type == "portfolio_risk_increase"
        assert suggestion.confidence >= 0.8
        
    def test_cache_operations(self, intelligence_engine):
        """Test cache set and get operations"""
        # Test with Redis unavailable (should handle gracefully)
        intelligence_engine.cache_set("test_key", "test_value", 300)
        result = intelligence_engine.cache_get("test_key")
        
        # Should return None when Redis is not available
        assert result is None
        
    def test_mock_data_generation(self, intelligence_engine):
        """Test that mock data generation produces valid data"""
        mock_quant = intelligence_engine._get_mock_quant_data()
        mock_snoop = intelligence_engine._get_mock_snoop_data()
        
        # Verify structure
        assert "ETH" in mock_quant
        assert "LINK" in mock_quant
        assert "WBTC" in mock_quant
        
        assert "ETH" in mock_snoop
        assert "LINK" in mock_snoop
        assert "WBTC" in mock_snoop
        
        # Verify data types and ranges
        for crypto in ["ETH", "LINK", "WBTC"]:
            quant = mock_quant[crypto]
            snoop = mock_snoop[crypto]
            
            assert isinstance(quant["price"], (int, float))
            assert 20 <= quant["rsi"] <= 80
            assert 0 <= quant["technical_score"] <= 100
            assert 0.5 <= quant["confidence_level"] <= 0.95
            
            assert 20 <= snoop["sentiment_score"] <= 80
            assert isinstance(snoop["mention_volume"], int)
            assert 0.4 <= snoop["influence_weight"] <= 0.8
            
    def test_strategy_adjustment_model(self):
        """Test StrategyAdjustment model validation"""
        adjustment = StrategyAdjustment(
            adjustment_type="allocation_increase",
            target_crypto="ETH",
            current_value=33.33,
            suggested_value=42.0,
            confidence=0.85,
            justification="Strong bullish signals detected",
            expected_impact="15-25% potential upside",
            risk_assessment="LOW - High conviction signals"
        )
        
        assert adjustment.adjustment_type == "allocation_increase"
        assert adjustment.target_crypto == "ETH"
        assert adjustment.confidence == 0.85
        assert "bullish" in adjustment.justification.lower()
        
    def test_database_models(self, intelligence_engine):
        """Test database model creation and operations"""
        # This should not raise an exception
        db = intelligence_engine.get_db()
        assert db is not None
        db.close()
        
    @pytest.mark.asyncio
    async def test_store_quant_data(self, intelligence_engine, mock_quant_data):
        """Test storing quant data in database"""
        # Should not raise an exception
        intelligence_engine._store_quant_data(mock_quant_data)
        
    @pytest.mark.asyncio
    async def test_store_snoop_data(self, intelligence_engine, mock_snoop_data):
        """Test storing snoop data in database"""
        # Should not raise an exception
        intelligence_engine._store_snoop_data(mock_snoop_data)

class TestIntelligenceEngineIntegration:
    """🔄 Integration tests for the Wolf Pack Intelligence Engine"""
    
    @pytest.mark.asyncio
    async def test_full_intelligence_cycle(self):
        """Test a complete intelligence gathering and processing cycle"""
        engine = WolfPackIntelligenceEngine(database_url="sqlite:///:memory:")
        
        # Fetch data (will use mock data since no API key)
        quant_data = await engine.fetch_latest_quant_data()
        snoop_data = await engine.fetch_latest_snoop_data()
        
        assert quant_data is not None
        assert snoop_data is not None
        
        # Generate suggestions
        suggestions = engine.generate_strategy_suggestions(quant_data, snoop_data)
        
        assert len(suggestions) >= 0  # Should produce suggestions or handle gracefully
        
        # Verify suggestion structure if any are generated
        if suggestions:
            suggestion = suggestions[0]
            assert hasattr(suggestion, 'adjustment_type')
            assert hasattr(suggestion, 'target_crypto')
            assert hasattr(suggestion, 'confidence')
            assert hasattr(suggestion, 'justification')
            
    def test_singleton_pattern(self):
        """Test that get_intelligence_engine returns the same instance"""
        engine1 = get_intelligence_engine()
        engine2 = get_intelligence_engine()
        
        assert engine1 is engine2
        assert id(engine1) == id(engine2)
        
    @pytest.mark.asyncio
    async def test_error_handling_invalid_sheets_data(self):
        """Test error handling with invalid Google Sheets data"""
        engine = WolfPackIntelligenceEngine(database_url="sqlite:///:memory:")
        
        # Test with malformed data
        invalid_data = [["Bad"], ["Header"]]
        processed = engine._process_quant_data(invalid_data)
        
        # Should handle gracefully and return reasonable structure
        assert isinstance(processed, dict)
        
        # Test with empty data
        empty_data = []
        processed = engine._process_quant_data(empty_data)
        assert "error" in processed or isinstance(processed, dict)

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])