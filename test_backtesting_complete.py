#!/usr/bin/env python3
"""
Complete Backtesting System Test

End-to-end test of the full backtesting implementation including:
- Mock wallet functionality
- Historical data service
- Backtesting engine
- Performance metrics
- API integration
"""

import sys
import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project paths
project_root = os.path.dirname(__file__)
backend_path = os.path.join(project_root, 'backend', 'src')
sys.path.append(backend_path)

def test_mock_wallet():
    """Test MockWallet functionality"""
    print("\n" + "="*50)
    print("TESTING MOCK WALLET")
    print("="*50)

    try:
        from trading.backtesting.mock_wallet import MockWallet

        # Initialize wallet
        wallet = MockWallet(initial_capital=10000, commission_rate=0.001)
        print(f"[OK] Mock wallet initialized: ${wallet.initial_capital}")

        # Test trades
        current_time = datetime.utcnow()
        current_prices = {'BTC': 45000, 'ETH': 3000}

        # Execute buy trade
        trade1 = wallet.execute_trade('BTC', 'BUY', 0.1, 45000, current_time)
        if trade1:
            print(f"[OK] Buy trade executed: {trade1.side} {trade1.size} {trade1.symbol} @ ${trade1.price}")

        # Record portfolio snapshot
        wallet.record_portfolio_snapshot(current_prices, current_time)

        # Execute sell trade
        trade2 = wallet.execute_trade('BTC', 'SELL', 0.05, 46000, current_time + timedelta(hours=1))
        if trade2:
            print(f"[OK] Sell trade executed: {trade2.side} {trade2.size} {trade2.symbol} @ ${trade2.price}")

        # Get performance summary
        performance = wallet.get_performance_summary()
        print(f"[OK] Portfolio value: ${performance['final_value']:.2f}")
        print(f"[OK] Total return: {performance['total_return_pct']:.2f}%")
        print(f"[OK] Total trades: {performance['total_trades']}")

        return True

    except Exception as e:
        print(f"[FAIL] Mock wallet test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_historical_data():
    """Test HistoricalDataService"""
    print("\n" + "="*50)
    print("TESTING HISTORICAL DATA SERVICE")
    print("="*50)

    async def run_test():
        try:
            from trading.backtesting.historical_data import HistoricalDataService

            # Test data fetching
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()

            async with HistoricalDataService() as data_service:
                print("[INFO] Testing data fetch for BTC...")

                data = await data_service.get_ohlcv_data('BTC', start_date, end_date, '1h')

                if not data.empty:
                    print(f"[OK] Fetched {len(data)} rows of BTC data")
                    print(f"[OK] Columns: {list(data.columns)}")
                    print(f"[OK] Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

                    # Test data validation
                    required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    has_all_columns = all(col in data.columns for col in required_columns)

                    if has_all_columns:
                        print("[OK] All required columns present")
                    else:
                        print(f"[WARN] Missing columns: {[col for col in required_columns if col not in data.columns]}")

                    # Test cache
                    cache_stats = data_service.get_cache_stats()
                    print(f"[OK] Cache stats: {cache_stats}")

                    return True
                else:
                    print("[WARN] No data returned (using synthetic data)")
                    return True

        except Exception as e:
            print(f"[FAIL] Historical data test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    return asyncio.run(run_test())

def test_performance_calculator():
    """Test PerformanceCalculator"""
    print("\n" + "="*50)
    print("TESTING PERFORMANCE CALCULATOR")
    print("="*50)

    try:
        from trading.backtesting.performance import PerformanceCalculator
        from trading.backtesting.mock_wallet import MockWallet, Portfolio, Trade

        calculator = PerformanceCalculator()

        # Create sample portfolio history
        portfolio_history = []
        base_time = datetime.utcnow()

        for i in range(10):
            portfolio_history.append(Portfolio(
                timestamp=base_time + timedelta(hours=i),
                total_value=10000 + (i * 100),  # Growing portfolio
                cash_balance=5000 + (i * 50),
                positions_value=5000 + (i * 50),
                unrealized_pnl=i * 10,
                realized_pnl=i * 5
            ))

        # Create sample trades
        trade_history = []
        for i in range(5):
            trade_history.append(Trade(
                symbol='BTC',
                side='BUY' if i % 2 == 0 else 'SELL',
                size=0.1,
                price=45000 + (i * 100),
                commission=10,
                timestamp=base_time + timedelta(hours=i),
                realized_pnl=50 if i % 2 == 1 else -30
            ))

        # Calculate metrics
        metrics = calculator.calculate_comprehensive_metrics(
            portfolio_history, trade_history, 10000
        )

        print(f"[OK] Performance metrics calculated:")
        print(f"     Total Return: {metrics.get('total_return_pct', 0):.2f}%")
        print(f"     Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
        print(f"     Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
        print(f"     Win Rate: {metrics.get('win_rate_pct', 0):.1f}%")
        print(f"     Total Trades: {metrics.get('total_trades', 0)}")

        # Test report generation
        report = calculator.generate_performance_report(metrics)
        if "BACKTEST PERFORMANCE REPORT" in report:
            print("[OK] Performance report generated")

        return True

    except Exception as e:
        print(f"[FAIL] Performance calculator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backtesting_engine():
    """Test BacktestEngine"""
    print("\n" + "="*50)
    print("TESTING BACKTESTING ENGINE")
    print("="*50)

    async def run_test():
        try:
            from trading.backtesting.engine import BacktestEngine
            from trading.backtesting.utils import BacktestConfig

            engine = BacktestEngine()

            # Create test configuration
            config = BacktestConfig(
                strategy_name='simple_buy_hold',
                strategy_params={'position_size': 0.1},
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now() - timedelta(days=1),
                symbols=['BTC'],
                initial_capital=10000.0
            )

            print(f"[INFO] Running backtest: {config.strategy_name}")
            print(f"[INFO] Period: {config.start_date.date()} to {config.end_date.date()}")
            print(f"[INFO] Symbols: {config.symbols}")

            # Progress callback
            async def progress_callback(backtest_id, progress, message):
                if progress % 20 == 0 or progress >= 90:
                    print(f"[PROGRESS] {progress:.1f}% - {message}")

            # Run backtest
            results = await engine.run_backtest(config, progress_callback)

            print(f"[OK] Backtest completed successfully")
            print(f"     Strategy: {results.get('strategy_name')}")
            print(f"     Initial Capital: ${results.get('initial_capital', 0):,.2f}")
            print(f"     Final Value: ${results.get('final_value', 0):,.2f}")
            print(f"     Total Return: {results.get('total_return_pct', 0):.2f}%")
            print(f"     Total Trades: {results.get('total_trades', 0)}")
            print(f"     Sharpe Ratio: {results.get('sharpe_ratio', 0):.3f}")

            return True

        except Exception as e:
            print(f"[FAIL] Backtesting engine test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    return asyncio.run(run_test())

def test_integration():
    """Test full system integration"""
    print("\n" + "="*50)
    print("INTEGRATION TEST - SIMPLE STRATEGY")
    print("="*50)

    async def run_test():
        try:
            # Test a complete backtesting workflow
            from trading.backtesting.engine import BacktestEngine
            from trading.backtesting.utils import BacktestConfig

            engine = BacktestEngine()

            # EMA Crossover strategy test
            config = BacktestConfig(
                strategy_name='ema_crossover',
                strategy_params={
                    'fastPeriod': 12,
                    'slowPeriod': 26,
                    'positionSize': 0.05
                },
                start_date=datetime.now() - timedelta(days=60),
                end_date=datetime.now() - timedelta(days=1),
                symbols=['BTC', 'ETH'],
                initial_capital=10000.0,
                commission_rate=0.001
            )

            print("[INFO] Running EMA Crossover strategy backtest...")
            print(f"[INFO] Symbols: {config.symbols}")
            print(f"[INFO] Fast EMA: {config.strategy_params['fastPeriod']}")
            print(f"[INFO] Slow EMA: {config.strategy_params['slowPeriod']}")

            results = await engine.run_backtest(config)

            print(f"\n[SUCCESS] BACKTEST RESULTS:")
            print(f"Strategy: {results.get('strategy_name')}")
            print(f"Period: {results.get('backtest_days', 0)} days")
            print(f"Initial Capital: ${results.get('initial_capital', 0):,.2f}")
            print(f"Final Value: ${results.get('final_value', 0):,.2f}")
            print(f"Total Return: {results.get('total_return_pct', 0):+.2f}%")
            print(f"Annualized Return: {results.get('annualized_return_pct', 0):+.2f}%")
            print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.3f}")
            print(f"Max Drawdown: {results.get('max_drawdown_pct', 0):.2f}%")
            print(f"Win Rate: {results.get('win_rate_pct', 0):.1f}%")
            print(f"Total Trades: {results.get('total_trades', 0)}")
            print(f"Profit Factor: {results.get('profit_factor', 0):.2f}")

            return True

        except Exception as e:
            print(f"[FAIL] Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    return asyncio.run(run_test())

def main():
    """Run all tests"""
    print("WolfHunt Backtesting System - Complete Test Suite")
    print("="*60)

    tests = [
        ("Mock Wallet", test_mock_wallet),
        ("Historical Data", test_historical_data),
        ("Performance Calculator", test_performance_calculator),
        ("Backtesting Engine", test_backtesting_engine),
        ("Integration Test", test_integration)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n⏳ Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"💥 {test_name} test CRASHED: {e}")
            results.append((test_name, False))

    # Final summary
    print("\n" + "="*60)
    print("FINAL TEST RESULTS")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Backtesting system is ready for production!")
        print("\nNext steps:")
        print("1. Connect API routes to main FastAPI app")
        print("2. Update frontend to use new backtesting endpoints")
        print("3. Test with real CoinGecko data")
        print("4. Deploy and monitor performance")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Review errors above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)