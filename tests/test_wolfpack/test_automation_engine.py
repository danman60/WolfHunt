"""
🤖 WOLF PACK STRATEGY AUTOMATION ENGINE TESTS
Comprehensive test suite for the AI-powered trading automation system
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from src.integrations.strategy_automation import (
    StrategyAutomationEngine,
    ExecutionPlan,
    ExecutionStatus,
    RiskLevel,
    PortfolioState,
    get_automation_engine
)
from src.integrations.wolfpack_intelligence import StrategyAdjustment, WolfPackIntelligenceEngine

class TestStrategyAutomationEngine:
    """🤖 Test suite for Strategy Automation Engine"""
    
    @pytest.fixture
    def mock_intelligence_engine(self):
        """Create a mock intelligence engine"""
        mock_engine = Mock(spec=WolfPackIntelligenceEngine)
        mock_engine.get_db.return_value = Mock()
        return mock_engine
    
    @pytest.fixture
    def automation_engine(self, mock_intelligence_engine):
        """Create a test automation engine instance"""
        with patch.dict(os.environ, {
            'WOLF_PACK_TRADING_ENABLED': 'false',  # Disable real trading for tests
            'GMX_ACCOUNT_ADDRESS': '0x123...test'
        }):
            engine = StrategyAutomationEngine(mock_intelligence_engine)
            # Mock the GMX client to avoid real connections
            engine.gmx_client = Mock()
            return engine
    
    @pytest.fixture
    def sample_strategy_suggestion(self):
        """Create a sample strategy suggestion for testing"""
        return StrategyAdjustment(
            adjustment_type="allocation_increase",
            target_crypto="ETH",
            current_value=33.33,
            suggested_value=42.0,
            confidence=0.85,
            justification="🚀 Strong bullish convergence detected! Technical 78.5, Sentiment 71.8.",
            expected_impact="Potential 15-25% alpha capture in next 7 days",
            risk_assessment="LOW - High conviction signals reduce risk"
        )
    
    @pytest.fixture
    def high_risk_suggestion(self):
        """Create a high-risk strategy suggestion for testing"""
        return StrategyAdjustment(
            adjustment_type="momentum_play",
            target_crypto="BTC",
            current_value=25.0,
            suggested_value=50.0,  # Large increase
            confidence=0.65,  # Lower confidence
            justification="High volatility momentum detected",
            expected_impact="Potential 30-40% upside but increased risk",
            risk_assessment="HIGH - Volatile market conditions present"
        )
    
    def test_engine_initialization(self, automation_engine):
        """Test that the automation engine initializes correctly"""
        assert automation_engine is not None
        assert automation_engine.trading_enabled == False  # Should be disabled in tests
        assert automation_engine.max_daily_executions == 50
        assert len(automation_engine.automation_rules) > 0
        assert automation_engine.gmx_client is not None
        
    def test_default_automation_rules(self, automation_engine):
        """Test that default automation rules are created correctly"""
        rules = automation_engine.automation_rules
        
        assert "conservative" in rules
        assert "aggressive" in rules
        
        conservative = rules["conservative"]
        assert conservative["auto_execute_threshold"] == 0.85
        assert conservative["max_position_size"] == 0.15
        assert conservative["risk_level"] == "LOW"
        
        aggressive = rules["aggressive"]
        assert aggressive["auto_execute_threshold"] == 0.75
        assert aggressive["max_position_size"] == 0.25
        assert aggressive["risk_level"] == "MEDIUM"
        
    @pytest.mark.asyncio
    async def test_assess_suggestion_risk_high_confidence(self, automation_engine, sample_strategy_suggestion):
        """Test risk assessment for high-confidence suggestion"""
        risk_analysis = await automation_engine._assess_suggestion_risk(sample_strategy_suggestion)
        
        assert risk_analysis["approved"] == True
        assert risk_analysis["risk_level"] in ["LOW", "MEDIUM"]
        assert risk_analysis["risk_score"] >= 0.0
        assert isinstance(risk_analysis["risk_factors"], list)
        
    @pytest.mark.asyncio
    async def test_assess_suggestion_risk_high_risk(self, automation_engine, high_risk_suggestion):
        """Test risk assessment for high-risk suggestion"""
        risk_analysis = await automation_engine._assess_suggestion_risk(high_risk_suggestion)
        
        # High risk suggestion should be flagged
        assert risk_analysis["risk_level"] in ["HIGH", "CRITICAL"]
        assert risk_analysis["risk_score"] > 0.3
        assert len(risk_analysis["risk_factors"]) > 0
        
    @pytest.mark.asyncio
    async def test_assess_suggestion_risk_position_size_limit(self, automation_engine):
        """Test risk assessment rejects oversized positions"""
        oversized_suggestion = StrategyAdjustment(
            adjustment_type="allocation_increase",
            target_crypto="ETH",
            current_value=10.0,
            suggested_value=80.0,  # Way too large
            confidence=0.9,
            justification="Test oversized position",
            expected_impact="Test",
            risk_assessment="LOW"
        )
        
        risk_analysis = await automation_engine._assess_suggestion_risk(oversized_suggestion)
        
        assert risk_analysis["approved"] == False
        assert "Position size exceeds risk limits" in risk_analysis["rejection_reason"]
        
    @pytest.mark.asyncio
    async def test_assess_suggestion_risk_cooldown(self, automation_engine, sample_strategy_suggestion):
        """Test risk assessment respects cooldown periods"""
        # Set a recent execution time for ETH
        automation_engine.last_execution_time["ETH"] = datetime.utcnow() - timedelta(minutes=10)
        
        risk_analysis = await automation_engine._assess_suggestion_risk(sample_strategy_suggestion)
        
        assert risk_analysis["approved"] == False
        assert "Cooldown period active" in risk_analysis["rejection_reason"]
        
    @pytest.mark.asyncio
    async def test_assess_suggestion_risk_daily_limit(self, automation_engine, sample_strategy_suggestion):
        """Test risk assessment respects daily execution limits"""
        # Set daily execution count to maximum
        automation_engine.daily_execution_count = automation_engine.automation_rules["conservative"]["max_daily_trades"]
        
        risk_analysis = await automation_engine._assess_suggestion_risk(sample_strategy_suggestion)
        
        assert risk_analysis["approved"] == False
        assert "Daily trade limit reached" in risk_analysis["rejection_reason"]
        
    @pytest.mark.asyncio
    async def test_create_execution_plan_market_order(self, automation_engine, sample_strategy_suggestion):
        """Test creation of execution plan with market order"""
        risk_analysis = {"approved": True, "risk_level": "LOW", "risk_score": 0.2, "risk_factors": []}
        
        execution_plan = await automation_engine._create_execution_plan(sample_strategy_suggestion, risk_analysis)
        
        assert execution_plan.suggestion == sample_strategy_suggestion
        assert execution_plan.execution_method in ["market", "limit", "twap"]
        assert execution_plan.position_sizing > 0
        assert execution_plan.position_sizing <= 0.15  # Conservative limit
        assert len(execution_plan.risk_checks) >= 5
        assert execution_plan.estimated_cost > 0
        
    @pytest.mark.asyncio
    async def test_create_execution_plan_momentum_play(self, automation_engine):
        """Test execution plan for momentum play strategy"""
        momentum_suggestion = StrategyAdjustment(
            adjustment_type="momentum_play",
            target_crypto="ETH",
            current_value=33.33,
            suggested_value=38.0,
            confidence=0.82,
            justification="Volume momentum detected",
            expected_impact="Quick gains expected",
            risk_assessment="MEDIUM"
        )
        
        risk_analysis = {"approved": True, "risk_level": "MEDIUM", "risk_score": 0.3, "risk_factors": []}
        execution_plan = await automation_engine._create_execution_plan(momentum_suggestion, risk_analysis)
        
        assert execution_plan.execution_method == "market"  # Speed important for momentum
        assert execution_plan.execution_timeline == "immediate"
        
    @pytest.mark.asyncio
    async def test_create_execution_plan_support_bounce(self, automation_engine):
        """Test execution plan for support bounce strategy"""
        support_suggestion = StrategyAdjustment(
            adjustment_type="support_bounce",
            target_crypto="LINK",
            current_value=33.33,
            suggested_value=38.0,
            confidence=0.75,
            justification="Near support level",
            expected_impact="Support bounce opportunity",
            risk_assessment="MEDIUM"
        )
        
        risk_analysis = {"approved": True, "risk_level": "MEDIUM", "risk_score": 0.25, "risk_factors": []}
        execution_plan = await automation_engine._create_execution_plan(support_suggestion, risk_analysis)
        
        assert execution_plan.execution_method == "limit"  # Precision important for support bounces
        
    @pytest.mark.asyncio
    async def test_evaluate_strategy_suggestions(self, automation_engine, sample_strategy_suggestion):
        """Test evaluation of multiple strategy suggestions"""
        suggestions = [sample_strategy_suggestion]
        
        # Mock portfolio state
        automation_engine.portfolio_state = PortfolioState(
            total_equity=100000.0,
            available_margin=85000.0,
            current_positions={"ETH": 0.25},
            daily_trades_count=0,
            last_trade_time=None,
            risk_metrics={}
        )
        
        execution_plans = await automation_engine.evaluate_strategy_suggestions(suggestions)
        
        assert len(execution_plans) >= 0  # Should evaluate without error
        
        if execution_plans:
            plan = execution_plans[0]
            assert isinstance(plan, ExecutionPlan)
            assert plan.suggestion == sample_strategy_suggestion
            
    @pytest.mark.asyncio
    async def test_simulate_execution(self, automation_engine, sample_strategy_suggestion):
        """Test simulated execution when trading is disabled"""
        risk_analysis = {"approved": True, "risk_level": "LOW", "risk_score": 0.1, "risk_factors": []}
        execution_plan = await automation_engine._create_execution_plan(sample_strategy_suggestion, risk_analysis)
        
        result = await automation_engine._simulate_execution(execution_plan)
        
        assert result["platform"] == "SIMULATION"
        assert result["network"] == "testnet"
        assert "SIMULATED_WP_" in result["transaction_id"]
        assert result["size"] > 0
        assert result["price"] > 0
        assert "timestamp" in result
        
    @pytest.mark.asyncio
    async def test_calculate_optimal_leverage(self, automation_engine, sample_strategy_suggestion):
        """Test optimal leverage calculation"""
        risk_analysis = {"approved": True, "risk_level": "LOW", "risk_score": 0.1, "risk_factors": []}
        execution_plan = await automation_engine._create_execution_plan(sample_strategy_suggestion, risk_analysis)
        
        leverage = automation_engine._calculate_optimal_leverage(sample_strategy_suggestion, execution_plan)
        
        assert 1.0 <= leverage <= 10.0  # Should be within reasonable bounds
        assert isinstance(leverage, float)
        
    @pytest.mark.asyncio
    async def test_calculate_optimal_leverage_high_confidence(self, automation_engine):
        """Test leverage calculation for high confidence signals"""
        high_conf_suggestion = StrategyAdjustment(
            adjustment_type="allocation_increase",
            target_crypto="ETH",
            current_value=33.33,
            suggested_value=40.0,
            confidence=0.95,  # Very high confidence
            justification="Extremely strong signals",
            expected_impact="High probability gains",
            risk_assessment="LOW"
        )
        high_conf_suggestion.signal_strength = "VERY_STRONG"
        
        risk_analysis = {"approved": True, "risk_level": "LOW", "risk_score": 0.05, "risk_factors": []}
        execution_plan = await automation_engine._create_execution_plan(high_conf_suggestion, risk_analysis)
        
        leverage = automation_engine._calculate_optimal_leverage(high_conf_suggestion, execution_plan)
        
        # High confidence should result in higher leverage
        assert leverage >= 2.0
        
    @pytest.mark.asyncio
    async def test_calculate_optimal_leverage_high_risk(self, automation_engine):
        """Test leverage calculation for high risk scenarios"""
        high_risk_suggestion = StrategyAdjustment(
            adjustment_type="allocation_increase",
            target_crypto="BTC",
            current_value=33.33,
            suggested_value=40.0,
            confidence=0.7,
            justification="Moderate signals",
            expected_impact="Potential gains with risk",
            risk_assessment="HIGH - Volatile conditions"
        )
        
        risk_analysis = {"approved": True, "risk_level": "HIGH", "risk_score": 0.6, "risk_factors": []}
        execution_plan = await automation_engine._create_execution_plan(high_risk_suggestion, risk_analysis)
        
        leverage = automation_engine._calculate_optimal_leverage(high_risk_suggestion, execution_plan)
        
        # High risk should result in lower leverage
        assert leverage <= 3.0
        
    @pytest.mark.asyncio
    async def test_perform_pre_execution_checks(self, automation_engine, sample_strategy_suggestion):
        """Test pre-execution safety checks"""
        risk_analysis = {"approved": True, "risk_level": "LOW", "risk_score": 0.1, "risk_factors": []}
        execution_plan = await automation_engine._create_execution_plan(sample_strategy_suggestion, risk_analysis)
        
        # Set up portfolio state with sufficient margin
        automation_engine.portfolio_state = PortfolioState(
            total_equity=100000.0,
            available_margin=85000.0,
            current_positions={},
            daily_trades_count=0,
            last_trade_time=None,
            risk_metrics={}
        )
        
        check_result = await automation_engine._perform_pre_execution_checks(execution_plan)
        
        assert "passed" in check_result
        assert "checks_passed" in check_result
        assert "checks_failed" in check_result
        assert isinstance(check_result["checks_passed"], list)
        assert isinstance(check_result["checks_failed"], list)
        
    @pytest.mark.asyncio
    async def test_perform_pre_execution_checks_insufficient_margin(self, automation_engine, sample_strategy_suggestion):
        """Test pre-execution checks fail with insufficient margin"""
        risk_analysis = {"approved": True, "risk_level": "LOW", "risk_score": 0.1, "risk_factors": []}
        execution_plan = await automation_engine._create_execution_plan(sample_strategy_suggestion, risk_analysis)
        
        # Set up portfolio state with insufficient margin
        automation_engine.portfolio_state = PortfolioState(
            total_equity=1000.0,  # Very low equity
            available_margin=100.0,  # Very low margin
            current_positions={},
            daily_trades_count=0,
            last_trade_time=None,
            risk_metrics={}
        )
        
        check_result = await automation_engine._perform_pre_execution_checks(execution_plan)
        
        assert check_result["passed"] == False
        assert "insufficient_margin" in check_result["checks_failed"]
        
    @pytest.mark.asyncio
    async def test_update_portfolio_state_simulation(self, automation_engine):
        """Test portfolio state update in simulation mode"""
        await automation_engine._update_portfolio_state()
        
        assert automation_engine.portfolio_state is not None
        assert automation_engine.portfolio_state.total_equity > 0
        assert automation_engine.portfolio_state.available_margin > 0
        assert isinstance(automation_engine.portfolio_state.current_positions, dict)
        
    @pytest.mark.asyncio
    async def test_get_automation_status(self, automation_engine):
        """Test automation status reporting"""
        status = await automation_engine.get_automation_status()
        
        assert "engine_status" in status
        assert "trading_enabled" in status
        assert "daily_executions" in status
        assert "gmx_integration" in status
        assert "capabilities" in status
        assert "risk_thresholds" in status
        
        gmx_status = status["gmx_integration"]
        assert "status" in gmx_status
        assert "network" in gmx_status
        assert gmx_status["network"] == "arbitrum"
        
        capabilities = status["capabilities"]
        assert "real_trading" in capabilities
        assert "risk_management" in capabilities
        assert "auto_execution" in capabilities
        
    @pytest.mark.asyncio
    async def test_execute_plan_trading_disabled(self, automation_engine, sample_strategy_suggestion):
        """Test plan execution when trading is disabled"""
        risk_analysis = {"approved": True, "risk_level": "LOW", "risk_score": 0.1, "risk_factors": []}
        execution_plan = await automation_engine._create_execution_plan(sample_strategy_suggestion, risk_analysis)
        
        result = await automation_engine.execute_plan(execution_plan)
        
        assert result["status"] in ["executed", "failed"]
        assert "timestamp" in result
        
        if result["status"] == "executed":
            assert "transaction_id" in result
            assert "SIMULATED" in result["transaction_id"]

class TestAutomationEngineIntegration:
    """🔄 Integration tests for the Strategy Automation Engine"""
    
    @pytest.mark.asyncio
    async def test_full_automation_cycle(self):
        """Test a complete automation cycle from suggestion to execution"""
        # Create mock intelligence engine
        mock_intelligence = Mock(spec=WolfPackIntelligenceEngine)
        mock_intelligence.get_db.return_value = Mock()
        
        # Create automation engine
        with patch.dict(os.environ, {'WOLF_PACK_TRADING_ENABLED': 'false'}):
            engine = StrategyAutomationEngine(mock_intelligence)
            engine.gmx_client = Mock()
        
        # Create test suggestion
        suggestion = StrategyAdjustment(
            adjustment_type="allocation_increase",
            target_crypto="ETH",
            current_value=30.0,
            suggested_value=35.0,
            confidence=0.8,
            justification="Test automation cycle",
            expected_impact="Test impact",
            risk_assessment="LOW - Test scenario"
        )
        
        # Run full cycle
        execution_plans = await engine.evaluate_strategy_suggestions([suggestion])
        
        if execution_plans:
            plan = execution_plans[0]
            result = await engine.execute_plan(plan)
            assert "status" in result
            
    def test_singleton_pattern(self):
        """Test that get_automation_engine returns the same instance"""
        with patch('src.integrations.strategy_automation.get_intelligence_engine') as mock_get_intel:
            mock_intel = Mock(spec=WolfPackIntelligenceEngine)
            mock_intel.get_db.return_value = Mock()
            mock_get_intel.return_value = mock_intel
            
            engine1 = get_automation_engine()
            engine2 = get_automation_engine()
            
            assert engine1 is engine2
            
    @pytest.mark.asyncio
    async def test_error_handling_gmx_failure(self):
        """Test error handling when GMX operations fail"""
        mock_intelligence = Mock(spec=WolfPackIntelligenceEngine)
        mock_intelligence.get_db.return_value = Mock()
        
        with patch.dict(os.environ, {'WOLF_PACK_TRADING_ENABLED': 'true'}):
            engine = StrategyAutomationEngine(mock_intelligence)
            
            # Mock GMX client to raise exceptions
            engine.gmx_client = Mock()
            engine.gmx_client.get_oracle_prices = AsyncMock(side_effect=Exception("GMX API Error"))
            engine.gmx_client.create_order = AsyncMock(side_effect=Exception("Order Failed"))
            
            suggestion = StrategyAdjustment(
                adjustment_type="allocation_increase",
                target_crypto="ETH",
                current_value=30.0,
                suggested_value=35.0,
                confidence=0.8,
                justification="Test error handling",
                expected_impact="Test",
                risk_assessment="LOW"
            )
            
            # Should fallback to simulation on error
            risk_analysis = {"approved": True, "risk_level": "LOW", "risk_score": 0.1, "risk_factors": []}
            execution_plan = await engine._create_execution_plan(suggestion, risk_analysis)
            
            result = await engine._execute_strategy(execution_plan)
            
            # Should fallback to simulation
            assert result["platform"] == "SIMULATION"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])