"""Performance tests for trading strategies."""

import pytest
import time
from decimal import Decimal
from unittest.mock import Mock
import statistics

from backend.src.trading.strategies.ma_crossover import MovingAverageCrossoverStrategy
from tests.test_utils.test_data_factory import TestDataFactory


class TestStrategyPerformance:
    """Test trading strategy performance."""
    
    @pytest.mark.performance
    def test_strategy_analysis_speed(self):
        """Test strategy analysis performance with large datasets."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Test with different dataset sizes
        dataset_sizes = [100, 500, 1000, 2000]
        results = []
        
        for size in dataset_sizes:
            # Create test data
            candles = TestDataFactory.create_mock_candle_data(count=size)
            
            # Measure analysis time
            start_time = time.time()
            signal = strategy.analyze(candles)
            end_time = time.time()
            
            analysis_time = end_time - start_time
            results.append({
                'dataset_size': size,
                'analysis_time': analysis_time,
                'signal_type': signal.signal_type.name if signal else None
            })
            
            print(f"Dataset size: {size}, Analysis time: {analysis_time:.4f}s")
        
        # Performance assertions
        for result in results:
            # Analysis should complete within reasonable time
            assert result['analysis_time'] < 1.0  # Less than 1 second
            
            # Time should scale reasonably with dataset size
            if result['dataset_size'] <= 1000:
                assert result['analysis_time'] < 0.5  # Less than 500ms for smaller datasets
    
    @pytest.mark.performance
    def test_strategy_memory_usage(self):
        """Test strategy memory usage with large datasets."""
        import tracemalloc
        
        strategy = MovingAverageCrossoverStrategy()
        
        # Start memory tracing
        tracemalloc.start()
        
        # Process large dataset
        large_dataset = TestDataFactory.create_mock_candle_data(count=5000)
        
        # Take memory snapshot before analysis
        snapshot1 = tracemalloc.take_snapshot()
        
        # Run analysis
        signal = strategy.analyze(large_dataset)
        
        # Take memory snapshot after analysis
        snapshot2 = tracemalloc.take_snapshot()
        
        # Calculate memory usage
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        memory_usage = sum(stat.size_diff for stat in top_stats)
        
        tracemalloc.stop()
        
        print(f"Memory usage: {memory_usage / 1024 / 1024:.2f} MB")
        
        # Memory usage should be reasonable (less than 100MB for this test)
        assert memory_usage < 100 * 1024 * 1024  # 100MB
        assert signal is not None
    
    @pytest.mark.performance
    def test_concurrent_strategy_analysis(self):
        """Test concurrent strategy analysis performance."""
        import asyncio
        import concurrent.futures
        
        strategy = MovingAverageCrossoverStrategy()
        
        def analyze_dataset():
            candles = TestDataFactory.create_mock_candle_data(count=1000)
            return strategy.analyze(candles)
        
        # Test concurrent execution
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(analyze_dataset) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Test sequential execution
        start_time = time.time()
        sequential_results = [analyze_dataset() for _ in range(10)]
        end_time = time.time()
        sequential_time = end_time - start_time
        
        print(f"Concurrent time: {concurrent_time:.2f}s")
        print(f"Sequential time: {sequential_time:.2f}s")
        print(f"Speedup: {sequential_time / concurrent_time:.2f}x")
        
        # Concurrent execution should be faster (or at least not much slower)
        assert concurrent_time <= sequential_time * 1.2  # Allow 20% overhead
        assert len(results) == 10
        assert len(sequential_results) == 10
    
    @pytest.mark.performance
    def test_strategy_indicator_calculation_performance(self):
        """Test performance of individual indicator calculations."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Test EMA calculation performance
        price_data = [float(i + 45000) for i in range(10000)]  # Large price dataset
        
        start_time = time.time()
        ema_fast = strategy._calculate_ema(price_data, period=12)
        ema_calculation_time = time.time() - start_time
        
        # Test RSI calculation performance
        start_time = time.time()
        rsi = strategy._calculate_rsi(price_data, period=14)
        rsi_calculation_time = time.time() - start_time
        
        print(f"EMA calculation time: {ema_calculation_time:.4f}s")
        print(f"RSI calculation time: {rsi_calculation_time:.4f}s")
        
        # Indicator calculations should be fast
        assert ema_calculation_time < 0.1  # Less than 100ms
        assert rsi_calculation_time < 0.2  # Less than 200ms
        assert len(ema_fast) == len(price_data)
        assert len(rsi) == len(price_data)
    
    @pytest.mark.performance
    def test_strategy_scaling_with_symbols(self):
        """Test strategy performance when analyzing multiple symbols."""
        strategy = MovingAverageCrossoverStrategy()
        
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'MATIC-USD']
        symbol_results = {}
        
        total_start_time = time.time()
        
        for symbol in symbols:
            candles = TestDataFactory.create_mock_candle_data(symbol=symbol, count=1000)
            
            start_time = time.time()
            signal = strategy.analyze(candles)
            end_time = time.time()
            
            symbol_results[symbol] = {
                'analysis_time': end_time - start_time,
                'signal': signal
            }
        
        total_time = time.time() - total_start_time
        avg_time_per_symbol = total_time / len(symbols)
        
        print(f"Total time for {len(symbols)} symbols: {total_time:.2f}s")
        print(f"Average time per symbol: {avg_time_per_symbol:.4f}s")
        
        # Performance should scale linearly
        assert total_time < len(symbols) * 1.0  # Less than 1 second per symbol
        assert avg_time_per_symbol < 0.5  # Less than 500ms per symbol
        
        # All symbols should have been processed
        assert len(symbol_results) == len(symbols)
        for result in symbol_results.values():
            assert result['signal'] is not None
    
    @pytest.mark.performance
    def test_strategy_backtesting_performance(self):
        """Test strategy performance during backtesting scenarios."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Simulate backtesting with historical data
        backtest_periods = [30, 90, 180, 365]  # Days of data
        performance_results = []
        
        for period_days in backtest_periods:
            # Create historical data (24 candles per day)
            candle_count = period_days * 24
            historical_data = TestDataFactory.create_trending_candle_data(
                count=candle_count,
                trend='up'
            )
            
            # Measure backtesting performance
            start_time = time.time()
            
            # Simulate incremental analysis (like in real backtesting)
            signals = []
            for i in range(50, len(historical_data), 24):  # Analyze once per day
                subset_data = historical_data[:i]
                signal = strategy.analyze(subset_data)
                if signal:
                    signals.append(signal)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            performance_results.append({
                'period_days': period_days,
                'candle_count': candle_count,
                'analysis_count': len(signals),
                'total_time': total_time,
                'avg_time_per_analysis': total_time / len(signals) if signals else 0
            })
        
        # Print performance results
        for result in performance_results:
            print(f"Period: {result['period_days']} days, "
                  f"Analyses: {result['analysis_count']}, "
                  f"Total time: {result['total_time']:.2f}s, "
                  f"Avg per analysis: {result['avg_time_per_analysis']:.4f}s")
        
        # Performance assertions
        for result in performance_results:
            # Backtesting should complete in reasonable time
            assert result['total_time'] < result['period_days'] * 0.1  # Less than 0.1s per day
            assert result['avg_time_per_analysis'] < 0.5  # Less than 500ms per analysis
    
    @pytest.mark.performance
    def test_position_sizing_performance(self):
        """Test position sizing calculation performance."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Test position sizing with many different scenarios
        test_scenarios = []
        for i in range(1000):
            account_balance = Decimal(str(10000 + i * 100))  # Varying balances
            test_scenarios.append(account_balance)
        
        start_time = time.time()
        
        position_sizes = []
        for balance in test_scenarios:
            # Mock signal for position sizing
            mock_signal = Mock()
            mock_signal.strength = Decimal('0.8')
            mock_signal.confidence = Decimal('0.75')
            
            position_size = strategy.calculate_position_size(mock_signal, balance)
            position_sizes.append(position_size)
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        avg_time_per_calculation = calculation_time / len(test_scenarios)
        
        print(f"Position sizing calculations: {len(test_scenarios)}")
        print(f"Total time: {calculation_time:.4f}s")
        print(f"Average time per calculation: {avg_time_per_calculation:.6f}s")
        
        # Position sizing should be very fast
        assert calculation_time < 0.1  # Less than 100ms for 1000 calculations
        assert avg_time_per_calculation < 0.0001  # Less than 0.1ms per calculation
        assert len(position_sizes) == len(test_scenarios)
        assert all(size >= 0 for size in position_sizes)  # All sizes should be non-negative
    
    @pytest.mark.performance
    def test_strategy_warm_up_time(self):
        """Test strategy warm-up time with insufficient data."""
        strategy = MovingAverageCrossoverStrategy()
        
        # Test with gradually increasing dataset sizes
        warm_up_results = []
        
        for size in range(10, 60, 5):  # 10 to 55 candles
            candles = TestDataFactory.create_mock_candle_data(count=size)
            
            start_time = time.time()
            signal = strategy.analyze(candles)
            end_time = time.time()
            
            analysis_time = end_time - start_time
            has_signal = signal is not None and signal.confidence > 0.1
            
            warm_up_results.append({
                'dataset_size': size,
                'analysis_time': analysis_time,
                'has_valid_signal': has_signal,
                'signal_confidence': signal.confidence if signal else 0
            })
        
        # Print warm-up analysis
        print("Strategy warm-up analysis:")
        for result in warm_up_results:
            print(f"Size: {result['dataset_size']:2d}, "
                  f"Time: {result['analysis_time']:.4f}s, "
                  f"Valid signal: {result['has_valid_signal']}, "
                  f"Confidence: {result['signal_confidence']:.2f}")
        
        # Performance should be consistent regardless of dataset size
        analysis_times = [r['analysis_time'] for r in warm_up_results]
        max_time = max(analysis_times)
        min_time = min(analysis_times)
        
        assert max_time < 0.1  # All analyses should be fast
        assert max_time / min_time < 10  # Performance shouldn't vary too much
    
    @pytest.mark.performance
    def test_memory_efficiency_over_time(self):
        """Test memory efficiency during continuous operation."""
        import gc
        import tracemalloc
        
        strategy = MovingAverageCrossoverStrategy()
        
        tracemalloc.start()
        initial_snapshot = tracemalloc.take_snapshot()
        
        # Simulate continuous operation
        memory_snapshots = []
        
        for iteration in range(50):
            # Create new data each iteration (simulating real-time data)
            candles = TestDataFactory.create_mock_candle_data(count=100)
            signal = strategy.analyze(candles)
            
            # Force garbage collection
            gc.collect()
            
            if iteration % 10 == 0:  # Take snapshot every 10 iterations
                snapshot = tracemalloc.take_snapshot()
                memory_usage = sum(stat.size for stat in snapshot.statistics('lineno'))
                memory_snapshots.append({
                    'iteration': iteration,
                    'memory_usage_mb': memory_usage / 1024 / 1024
                })
        
        tracemalloc.stop()
        
        # Analyze memory usage trend
        print("Memory usage over time:")
        for snapshot in memory_snapshots:
            print(f"Iteration {snapshot['iteration']:2d}: {snapshot['memory_usage_mb']:.2f} MB")
        
        # Memory usage should not continuously increase (no memory leaks)
        memory_values = [s['memory_usage_mb'] for s in memory_snapshots]
        
        if len(memory_values) >= 2:
            # Memory growth should be bounded
            memory_growth = memory_values[-1] - memory_values[0]
            assert memory_growth < 50  # Less than 50MB growth over test
            
            # Should not have runaway memory usage
            max_memory = max(memory_values)
            assert max_memory < 200  # Less than 200MB total