"""Tests for trading strategies."""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from backend.src.trading.strategies.ma_crossover import MovingAverageCrossoverStrategy
from backend.src.trading.strategies.base import Signal, SignalType


class TestMovingAverageCrossoverStrategy:
    """Test Moving Average Crossover Strategy."""
    
    def test_strategy_initialization(self):
        """Test strategy initialization with default parameters."""
        strategy = MovingAverageCrossoverStrategy()
        
        assert strategy.fast_period == 12
        assert strategy.slow_period == 26
        assert strategy.rsi_period == 14
        assert strategy.rsi_oversold == 30
        assert strategy.rsi_overbought == 70
    
    def test_strategy_custom_parameters(self):
        """Test strategy initialization with custom parameters."""
        strategy = MovingAverageCrossoverStrategy(
            fast_period=10,
            slow_period=20,
            rsi_period=21,
            rsi_oversold=25,
            rsi_overbought=75
        )
        
        assert strategy.fast_period == 10
        assert strategy.slow_period == 20
        assert strategy.rsi_period == 21
        assert strategy.rsi_oversold == 25
        assert strategy.rsi_overbought == 75
    
    def test_ema_calculation(self):
        """Test EMA calculation."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Sample price data
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        
        ema = strategy._calculate_ema(prices, period=5)
        
        # EMA should be calculated and have same length as input
        assert len(ema) == len(prices)
        assert not np.isnan(ema[-1])  # Last value should not be NaN
        
        # EMA should be ascending for ascending price series
        assert ema[-1] > ema[4]  # Compare last value with first non-NaN value
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Sample price data with some volatility
        prices = [100, 102, 101, 105, 103, 108, 106, 110, 107, 112, 109]
        
        rsi = strategy._calculate_rsi(prices, period=5)
        
        # RSI should be between 0 and 100
        assert len(rsi) == len(prices)
        valid_rsi = rsi[~np.isnan(rsi)]
        assert all(0 <= x <= 100 for x in valid_rsi)
    
    def test_signal_generation_buy(self):
        """Test BUY signal generation."""
        strategy = MovingAverageCrossoverStrategy(fast_period=3, slow_period=5)
        
        # Create candle data that should generate a BUY signal
        # Fast EMA crossing above slow EMA with moderate RSI
        candles = []
        prices = [100, 101, 102, 105, 108, 110, 112]  # Uptrend
        
        for i, price in enumerate(prices):
            candles.append({
                'timestamp': f'2024-01-01T{i:02d}:00:00',
                'open': price - 0.5,
                'high': price + 1,
                'low': price - 1,
                'close': price,
                'volume': 1000
            })
        
        signal = strategy.analyze(candles)
        
        # Should generate a signal (BUY or HOLD depending on exact calculations)
        assert isinstance(signal, Signal)
        assert signal.signal_type in [SignalType.BUY, SignalType.HOLD]
    
    def test_signal_generation_sell(self):
        """Test SELL signal generation."""
        strategy = MovingAverageCrossoverStrategy(fast_period=3, slow_period=5)
        
        # Create candle data that should generate a SELL signal
        # Fast EMA crossing below slow EMA with high RSI
        candles = []
        prices = [112, 110, 108, 105, 102, 100, 98]  # Downtrend
        
        for i, price in enumerate(prices):
            candles.append({
                'timestamp': f'2024-01-01T{i:02d}:00:00',
                'open': price + 0.5,
                'high': price + 1,
                'low': price - 1,
                'close': price,
                'volume': 1000
            })
        
        signal = strategy.analyze(candles)
        
        # Should generate a signal
        assert isinstance(signal, Signal)
        assert signal.signal_type in [SignalType.SELL, SignalType.HOLD]
    
    def test_signal_generation_insufficient_data(self):
        """Test signal generation with insufficient data."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Only provide 5 candles, but strategy needs 26 for slow EMA
        candles = []
        for i in range(5):
            candles.append({
                'timestamp': f'2024-01-01T{i:02d}:00:00',
                'open': 100,
                'high': 101,
                'low': 99,
                'close': 100,
                'volume': 1000
            })
        
        signal = strategy.analyze(candles)
        
        # Should return HOLD signal with low confidence
        assert signal.signal_type == SignalType.HOLD
        assert signal.confidence < 0.5
    
    def test_position_size_calculation(self):
        """Test position size calculation."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Create a BUY signal
        signal = Signal(
            signal_type=SignalType.BUY,
            strength=0.8,
            confidence=0.75,
            timestamp="2024-01-01T00:00:00",
            metadata={"ema_cross": True, "rsi": 55}
        )
        
        account_balance = 10000.0
        position_size = strategy.calculate_position_size(signal, account_balance)
        
        # Position size should be reasonable (based on default 0.5% risk)
        assert position_size > 0
        assert position_size < account_balance * 0.1  # Should be less than 10% of balance
    
    def test_should_exit_position_profit_target(self):
        """Test position exit on profit target."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Mock position that has reached profit target
        position = Mock()
        position.side = "LONG"
        position.entry_price = 100.0
        position.size = 0.001
        position.unrealized_pnl_percent = 3.5  # Above typical take profit
        
        current_price = 103.5  # 3.5% profit
        
        should_exit = strategy.should_exit(position, current_price)
        assert should_exit is True
    
    def test_should_exit_position_stop_loss(self):
        """Test position exit on stop loss."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Mock position that has hit stop loss
        position = Mock()
        position.side = "LONG"
        position.entry_price = 100.0
        position.size = 0.001
        position.unrealized_pnl_percent = -2.5  # Below stop loss threshold
        
        current_price = 97.5  # 2.5% loss
        
        should_exit = strategy.should_exit(position, current_price)
        assert should_exit is True
    
    def test_should_not_exit_position_normal(self):
        """Test that position is not exited under normal conditions."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Mock position with normal P&L
        position = Mock()
        position.side = "LONG"
        position.entry_price = 100.0
        position.size = 0.001
        position.unrealized_pnl_percent = 0.5  # Small profit, not at target
        
        current_price = 100.5  # 0.5% profit
        
        should_exit = strategy.should_exit(position, current_price)
        assert should_exit is False
    
    def test_strategy_backtest_integration(self):
        """Test strategy integration with backtesting framework."""
        strategy = MovingAverageCrossoverStrategy()
        
        # This would be expanded to test full backtesting integration
        # For now, just ensure the strategy can be instantiated and used
        assert hasattr(strategy, 'analyze')
        assert hasattr(strategy, 'calculate_position_size')
        assert hasattr(strategy, 'should_exit')
    
    @patch('backend.src.trading.strategies.ma_crossover.logger')
    def test_strategy_logging(self, mock_logger):
        """Test that strategy logs important events."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Create minimal candle data
        candles = [{
            'timestamp': '2024-01-01T00:00:00',
            'open': 100,
            'high': 101,
            'low': 99,
            'close': 100,
            'volume': 1000
        }]
        
        signal = strategy.analyze(candles)
        
        # Strategy should log analysis attempts
        assert mock_logger.debug.called or mock_logger.info.called
    
    def test_strategy_performance_metrics(self):
        """Test strategy performance tracking."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Strategy should track performance metrics
        assert hasattr(strategy, 'total_signals')
        assert hasattr(strategy, 'successful_signals')
        assert hasattr(strategy, 'failed_signals')
        
        # Initial values should be zero
        assert strategy.total_signals == 0
        assert strategy.successful_signals == 0
        assert strategy.failed_signals == 0