"""Tests for risk management system."""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal

from backend.src.trading.risk_manager import RiskManager, RiskViolation, RiskCheckResult
from backend.src.database.models import User, Position, Trade


class TestRiskManager:
    """Test Risk Manager."""
    
    def test_risk_manager_initialization(self):
        """Test risk manager initialization."""
        risk_manager = RiskManager()
        
        assert risk_manager.max_position_size == Decimal('0.1')
        assert risk_manager.max_daily_loss == Decimal('1000.0')
        assert risk_manager.max_drawdown == Decimal('0.05')
        assert risk_manager.max_positions_per_symbol == 1
    
    def test_risk_manager_custom_config(self):
        """Test risk manager with custom configuration."""
        config = {
            'max_position_size': Decimal('0.2'),
            'max_daily_loss': Decimal('2000.0'),
            'max_drawdown': Decimal('0.1'),
            'max_positions_per_symbol': 2
        }
        
        risk_manager = RiskManager(config)
        
        assert risk_manager.max_position_size == Decimal('0.2')
        assert risk_manager.max_daily_loss == Decimal('2000.0')
        assert risk_manager.max_drawdown == Decimal('0.1')
        assert risk_manager.max_positions_per_symbol == 2
    
    def test_position_size_check_pass(self):
        """Test position size check - passing case."""
        risk_manager = RiskManager()
        
        # Mock user with sufficient balance
        user = Mock()
        user.account_balance = Decimal('10000.0')
        
        # Request position size within limits
        requested_size = Decimal('0.05')
        
        result = risk_manager.check_position_size(user, 'BTC-USD', requested_size)
        
        assert result.approved is True
        assert result.violations == []
    
    def test_position_size_check_fail(self):
        """Test position size check - failing case."""
        risk_manager = RiskManager()
        
        # Mock user with limited balance
        user = Mock()
        user.account_balance = Decimal('1000.0')
        
        # Request position size exceeding limits
        requested_size = Decimal('0.15')
        
        result = risk_manager.check_position_size(user, 'BTC-USD', requested_size)
        
        assert result.approved is False
        assert len(result.violations) > 0
        assert any(v.violation_type == 'POSITION_SIZE_EXCEEDED' for v in result.violations)
    
    def test_daily_loss_check_pass(self):
        """Test daily loss check - passing case."""
        risk_manager = RiskManager()
        
        # Mock user with small daily loss
        user = Mock()
        user.id = 1
        
        with patch('backend.src.trading.risk_manager.get_daily_pnl') as mock_get_pnl:
            mock_get_pnl.return_value = Decimal('-100.0')
            
            result = risk_manager.check_daily_loss(user)
            
            assert result.approved is True
            assert result.violations == []
    
    def test_daily_loss_check_fail(self):
        """Test daily loss check - failing case."""
        risk_manager = RiskManager()
        
        # Mock user with excessive daily loss
        user = Mock()
        user.id = 1
        
        with patch('backend.src.trading.risk_manager.get_daily_pnl') as mock_get_pnl:
            mock_get_pnl.return_value = Decimal('-1500.0')
            
            result = risk_manager.check_daily_loss(user)
            
            assert result.approved is False
            assert len(result.violations) > 0
            assert any(v.violation_type == 'DAILY_LOSS_EXCEEDED' for v in result.violations)
    
    def test_drawdown_check_pass(self):
        """Test drawdown check - passing case."""
        risk_manager = RiskManager()
        
        # Mock user with acceptable drawdown
        user = Mock()
        user.id = 1
        user.account_balance = Decimal('10000.0')
        user.peak_balance = Decimal('10200.0')
        
        result = risk_manager.check_drawdown(user)
        
        assert result.approved is True
        assert result.violations == []
    
    def test_drawdown_check_fail(self):
        """Test drawdown check - failing case."""
        risk_manager = RiskManager()
        
        # Mock user with excessive drawdown
        user = Mock()
        user.id = 1
        user.account_balance = Decimal('9000.0')
        user.peak_balance = Decimal('10000.0')
        
        result = risk_manager.check_drawdown(user)
        
        assert result.approved is False
        assert len(result.violations) > 0
        assert any(v.violation_type == 'MAX_DRAWDOWN_EXCEEDED' for v in result.violations)
    
    def test_comprehensive_risk_check_pass(self):
        """Test comprehensive risk check - all checks pass."""
        risk_manager = RiskManager()
        
        # Mock user with good risk profile
        user = Mock()
        user.id = 1
        user.account_balance = Decimal('10000.0')
        user.peak_balance = Decimal('10000.0')
        
        # Mock trade request
        trade_request = {
            'symbol': 'BTC-USD',
            'side': 'BUY',
            'size': Decimal('0.05'),
            'price': Decimal('45000.0')
        }
        
        with patch('backend.src.trading.risk_manager.get_daily_pnl') as mock_get_pnl:
            mock_get_pnl.return_value = Decimal('-50.0')
            
            with patch('backend.src.trading.risk_manager.get_open_positions') as mock_positions:
                mock_positions.return_value = []
                
                result = risk_manager.comprehensive_risk_check(user, trade_request)
                
                assert result.approved is True
                assert result.violations == []
    
    def test_comprehensive_risk_check_fail(self):
        """Test comprehensive risk check - multiple violations."""
        risk_manager = RiskManager()
        
        # Mock user with poor risk profile
        user = Mock()
        user.id = 1
        user.account_balance = Decimal('5000.0')
        user.peak_balance = Decimal('10000.0')  # 50% drawdown
        
        # Mock risky trade request
        trade_request = {
            'symbol': 'BTC-USD',
            'side': 'BUY',
            'size': Decimal('0.15'),  # Excessive size
            'price': Decimal('45000.0')
        }
        
        with patch('backend.src.trading.risk_manager.get_daily_pnl') as mock_get_pnl:
            mock_get_pnl.return_value = Decimal('-1200.0')  # Excessive daily loss
            
            with patch('backend.src.trading.risk_manager.get_open_positions') as mock_positions:
                mock_positions.return_value = []
                
                result = risk_manager.comprehensive_risk_check(user, trade_request)
                
                assert result.approved is False
                assert len(result.violations) > 1
    
    def test_position_correlation_check(self):
        """Test position correlation risk check."""
        risk_manager = RiskManager()
        
        user = Mock()
        user.id = 1
        
        # Mock existing correlated positions
        existing_positions = [
            Mock(symbol='BTC-USD', side='LONG', size=Decimal('0.05')),
            Mock(symbol='ETH-USD', side='LONG', size=Decimal('0.03'))
        ]
        
        trade_request = {
            'symbol': 'LTC-USD',
            'side': 'BUY',
            'size': Decimal('0.08')
        }
        
        with patch('backend.src.trading.risk_manager.get_open_positions') as mock_positions:
            mock_positions.return_value = existing_positions
            
            result = risk_manager.check_position_correlation(user, trade_request)
            
            # Should detect high crypto correlation
            assert isinstance(result, RiskCheckResult)
    
    def test_emergency_stop_activation(self):
        """Test emergency stop activation."""
        risk_manager = RiskManager()
        
        user = Mock()
        user.id = 1
        
        # Trigger emergency stop
        result = risk_manager.activate_emergency_stop(user, "Test emergency stop")
        
        assert result is True
        assert user.id in risk_manager._emergency_stops
    
    def test_emergency_stop_check(self):
        """Test emergency stop check."""
        risk_manager = RiskManager()
        
        user = Mock()
        user.id = 1
        
        # Activate emergency stop
        risk_manager.activate_emergency_stop(user, "Test")
        
        # Check if trading is blocked
        result = risk_manager.check_emergency_stop(user)
        
        assert result.approved is False
        assert len(result.violations) > 0
        assert any(v.violation_type == 'EMERGENCY_STOP_ACTIVE' for v in result.violations)
    
    def test_position_sizing_calculation(self):
        """Test position sizing based on risk parameters."""
        risk_manager = RiskManager()
        
        user = Mock()
        user.account_balance = Decimal('10000.0')
        
        # Test 1% risk per trade
        risk_percent = Decimal('0.01')
        stop_loss_distance = Decimal('0.02')  # 2% stop loss
        
        position_size = risk_manager.calculate_position_size(
            user, risk_percent, stop_loss_distance
        )
        
        # Should be 0.5% of account balance (1% risk / 2% stop loss)
        expected_size = user.account_balance * Decimal('0.005')
        assert abs(position_size - expected_size) < Decimal('0.01')
    
    def test_risk_metrics_calculation(self):
        """Test risk metrics calculation."""
        risk_manager = RiskManager()
        
        user = Mock()
        user.id = 1
        
        with patch('backend.src.trading.risk_manager.get_user_trades') as mock_trades:
            # Mock trade history
            mock_trades.return_value = [
                Mock(pnl=Decimal('100.0'), timestamp='2024-01-01'),
                Mock(pnl=Decimal('-50.0'), timestamp='2024-01-02'),
                Mock(pnl=Decimal('75.0'), timestamp='2024-01-03')
            ]
            
            metrics = risk_manager.calculate_risk_metrics(user)
            
            assert 'sharpe_ratio' in metrics
            assert 'max_drawdown' in metrics
            assert 'win_rate' in metrics
            assert 'avg_win' in metrics
            assert 'avg_loss' in metrics
    
    def test_circuit_breaker_activation(self):
        """Test circuit breaker activation on rapid losses."""
        risk_manager = RiskManager()
        
        user = Mock()
        user.id = 1
        
        # Simulate rapid consecutive losses
        for i in range(5):
            trade_result = Mock(pnl=Decimal('-100.0'), timestamp=f'2024-01-01T{i:02d}:00:00')
            risk_manager.record_trade_result(user, trade_result)
        
        # Check if circuit breaker is triggered
        result = risk_manager.check_circuit_breaker(user)
        
        assert result.approved is False
        assert any(v.violation_type == 'CIRCUIT_BREAKER_TRIGGERED' for v in result.violations)
    
    def test_risk_limit_updates(self):
        """Test dynamic risk limit updates."""
        risk_manager = RiskManager()
        
        user = Mock()
        user.id = 1
        
        # Update risk limits
        new_limits = {
            'max_position_size': Decimal('0.2'),
            'max_daily_loss': Decimal('2000.0')
        }
        
        result = risk_manager.update_risk_limits(user, new_limits)
        
        assert result is True
        assert user.id in risk_manager._user_risk_limits
        assert risk_manager._user_risk_limits[user.id]['max_position_size'] == Decimal('0.2')