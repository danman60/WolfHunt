"""Tests for utility helpers."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from backend.src.utils.helpers import (
    calculate_percentage_change,
    format_currency,
    validate_symbol,
    calculate_position_size,
    is_market_hours,
    round_to_tick_size,
    calculate_pnl,
    format_timestamp
)


class TestUtilityHelpers:
    """Test utility helper functions."""
    
    def test_calculate_percentage_change(self):
        """Test percentage change calculation."""
        # Positive change
        change = calculate_percentage_change(100, 110)
        assert change == 10.0
        
        # Negative change
        change = calculate_percentage_change(100, 90)
        assert change == -10.0
        
        # No change
        change = calculate_percentage_change(100, 100)
        assert change == 0.0
        
        # Zero original value
        change = calculate_percentage_change(0, 100)
        assert change == 0.0  # Should handle division by zero
    
    def test_format_currency(self):
        """Test currency formatting."""
        # Positive amount
        formatted = format_currency(1234.56)
        assert formatted == "$1,234.56"
        
        # Negative amount
        formatted = format_currency(-1234.56)
        assert formatted == "-$1,234.56"
        
        # Zero amount
        formatted = format_currency(0)
        assert formatted == "$0.00"
        
        # Large amount
        formatted = format_currency(1000000.123)
        assert formatted == "$1,000,000.12"
    
    def test_validate_symbol(self):
        """Test symbol validation."""
        # Valid symbols
        assert validate_symbol("BTC-USD") is True
        assert validate_symbol("ETH-USD") is True
        assert validate_symbol("SOL-USD") is True
        
        # Invalid symbols
        assert validate_symbol("INVALID") is False
        assert validate_symbol("BTC") is False
        assert validate_symbol("") is False
        assert validate_symbol(None) is False
    
    def test_calculate_position_size(self):
        """Test position size calculation."""
        account_balance = Decimal('10000.0')
        risk_percent = Decimal('0.02')  # 2%
        stop_loss_percent = Decimal('0.05')  # 5%
        
        position_size = calculate_position_size(
            account_balance, risk_percent, stop_loss_percent
        )
        
        # Should risk 2% of account balance
        # Position size = (account_balance * risk_percent) / stop_loss_percent
        expected_size = (account_balance * risk_percent) / stop_loss_percent
        assert position_size == expected_size
    
    def test_calculate_position_size_edge_cases(self):
        """Test position size calculation edge cases."""
        # Zero stop loss
        position_size = calculate_position_size(
            Decimal('10000.0'), Decimal('0.02'), Decimal('0')
        )
        assert position_size == Decimal('0')
        
        # Zero risk percent
        position_size = calculate_position_size(
            Decimal('10000.0'), Decimal('0'), Decimal('0.05')
        )
        assert position_size == Decimal('0')
        
        # Zero account balance
        position_size = calculate_position_size(
            Decimal('0'), Decimal('0.02'), Decimal('0.05')
        )
        assert position_size == Decimal('0')
    
    def test_is_market_hours(self):
        """Test market hours checking."""
        # Test during US market hours (9:30 AM - 4:00 PM ET)
        # Note: This is a simplified test - real implementation would be more complex
        
        # Monday 2 PM ET (market open)
        market_time = datetime(2024, 1, 1, 14, 0, 0)  # Assuming ET timezone
        assert is_market_hours(market_time) is True
        
        # Saturday (market closed)
        weekend_time = datetime(2024, 1, 6, 14, 0, 0)
        assert is_market_hours(weekend_time) is False
        
        # Note: Crypto markets are 24/7, so this function behavior depends on implementation
    
    def test_round_to_tick_size(self):
        """Test rounding to tick size."""
        # Standard tick size
        price = Decimal('45123.456789')
        tick_size = Decimal('0.01')
        
        rounded = round_to_tick_size(price, tick_size)
        assert rounded == Decimal('45123.46')
        
        # Larger tick size
        price = Decimal('45123.456789')
        tick_size = Decimal('1.0')
        
        rounded = round_to_tick_size(price, tick_size)
        assert rounded == Decimal('45123')
        
        # Fractional tick size
        price = Decimal('45123.456789')
        tick_size = Decimal('0.25')
        
        rounded = round_to_tick_size(price, tick_size)
        assert rounded == Decimal('45123.50')
    
    def test_calculate_pnl_long_position(self):
        """Test P&L calculation for long position."""
        entry_price = Decimal('45000.0')
        current_price = Decimal('46000.0')
        size = Decimal('0.001')
        
        pnl = calculate_pnl('LONG', entry_price, current_price, size)
        
        # P&L = (current_price - entry_price) * size
        expected_pnl = (current_price - entry_price) * size
        assert pnl == expected_pnl
    
    def test_calculate_pnl_short_position(self):
        """Test P&L calculation for short position."""
        entry_price = Decimal('45000.0')
        current_price = Decimal('44000.0')
        size = Decimal('0.001')
        
        pnl = calculate_pnl('SHORT', entry_price, current_price, size)
        
        # P&L = (entry_price - current_price) * size
        expected_pnl = (entry_price - current_price) * size
        assert pnl == expected_pnl
    
    def test_calculate_pnl_edge_cases(self):
        """Test P&L calculation edge cases."""
        # Zero size
        pnl = calculate_pnl('LONG', Decimal('45000'), Decimal('46000'), Decimal('0'))
        assert pnl == Decimal('0')
        
        # Same entry and current price
        pnl = calculate_pnl('LONG', Decimal('45000'), Decimal('45000'), Decimal('0.001'))
        assert pnl == Decimal('0')
        
        # Negative size (should handle gracefully)
        pnl = calculate_pnl('LONG', Decimal('45000'), Decimal('46000'), Decimal('-0.001'))
        assert pnl < 0  # Negative size should reverse P&L
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        # ISO format
        timestamp = datetime(2024, 1, 1, 12, 30, 45)
        formatted = format_timestamp(timestamp, format_type='iso')
        assert formatted == '2024-01-01T12:30:45'
        
        # Human readable format
        formatted = format_timestamp(timestamp, format_type='human')
        assert 'Jan 1, 2024' in formatted
        
        # Unix timestamp
        formatted = format_timestamp(timestamp, format_type='unix')
        assert isinstance(formatted, int)
        
        # Default format
        formatted = format_timestamp(timestamp)
        assert isinstance(formatted, str)
    
    def test_format_timestamp_with_timezone(self):
        """Test timestamp formatting with timezone."""
        timestamp = datetime(2024, 1, 1, 12, 30, 45)
        
        # With timezone
        formatted = format_timestamp(timestamp, timezone='UTC')
        assert 'UTC' in formatted or 'Z' in formatted
        
        # With different timezone
        formatted = format_timestamp(timestamp, timezone='EST')
        assert isinstance(formatted, str)
    
    def test_validation_helpers(self):
        """Test validation helper functions."""
        from backend.src.utils.helpers import (
            validate_email,
            validate_password_strength,
            validate_decimal_precision
        )
        
        # Email validation
        assert validate_email('test@example.com') is True
        assert validate_email('invalid-email') is False
        
        # Password strength
        assert validate_password_strength('weak') is False
        assert validate_password_strength('StrongP@ssw0rd123') is True
        
        # Decimal precision
        assert validate_decimal_precision(Decimal('123.45'), 2) is True
        assert validate_decimal_precision(Decimal('123.456'), 2) is False
    
    def test_conversion_helpers(self):
        """Test conversion helper functions."""
        from backend.src.utils.helpers import (
            decimal_to_float,
            float_to_decimal,
            safe_division
        )
        
        # Decimal to float
        decimal_val = Decimal('123.45')
        float_val = decimal_to_float(decimal_val)
        assert isinstance(float_val, float)
        assert float_val == 123.45
        
        # Float to decimal
        float_val = 123.45
        decimal_val = float_to_decimal(float_val)
        assert isinstance(decimal_val, Decimal)
        
        # Safe division
        result = safe_division(Decimal('10'), Decimal('2'))
        assert result == Decimal('5')
        
        # Division by zero
        result = safe_division(Decimal('10'), Decimal('0'))
        assert result == Decimal('0')  # Should return 0 instead of error
    
    def test_time_helpers(self):
        """Test time-related helper functions."""
        from backend.src.utils.helpers import (
            get_utc_timestamp,
            is_weekend,
            time_until_market_open,
            get_trading_days_between
        )
        
        # UTC timestamp
        timestamp = get_utc_timestamp()
        assert isinstance(timestamp, datetime)
        
        # Weekend check
        saturday = datetime(2024, 1, 6)  # Saturday
        sunday = datetime(2024, 1, 7)   # Sunday
        monday = datetime(2024, 1, 8)   # Monday
        
        assert is_weekend(saturday) is True
        assert is_weekend(sunday) is True
        assert is_weekend(monday) is False
        
        # Trading days calculation
        start_date = datetime(2024, 1, 1)  # Monday
        end_date = datetime(2024, 1, 8)    # Monday (1 week later)
        
        trading_days = get_trading_days_between(start_date, end_date)
        assert trading_days == 5  # 5 weekdays
    
    def test_math_helpers(self):
        """Test mathematical helper functions."""
        from backend.src.utils.helpers import (
            calculate_compound_return,
            calculate_sharpe_ratio,
            calculate_volatility,
            calculate_correlation
        )
        
        # Compound return
        initial_value = Decimal('1000')
        final_value = Decimal('1100')
        periods = 12
        
        compound_return = calculate_compound_return(initial_value, final_value, periods)
        assert compound_return > 0
        
        # Sample returns for statistical calculations
        returns = [0.01, 0.02, -0.01, 0.015, -0.005, 0.02, 0.01]
        risk_free_rate = 0.02
        
        # Sharpe ratio
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate)
        assert isinstance(sharpe, float)
        
        # Volatility
        volatility = calculate_volatility(returns)
        assert volatility > 0
        
        # Correlation
        returns2 = [0.015, 0.018, -0.008, 0.012, -0.003, 0.022, 0.008]
        correlation = calculate_correlation(returns, returns2)
        assert -1 <= correlation <= 1