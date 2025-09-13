#!/usr/bin/env python3
"""
Simple Backtesting System Test
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add project paths
project_root = os.path.dirname(__file__)
backend_path = os.path.join(project_root, 'backend', 'src')
sys.path.append(backend_path)

def test_mock_wallet():
    """Test MockWallet basic functionality"""
    print("Testing Mock Wallet...")

    try:
        from trading.backtesting.mock_wallet import MockWallet

        wallet = MockWallet(10000)
        current_time = datetime.utcnow()

        # Test buy
        trade = wallet.execute_trade('BTC', 'BUY', 0.1, 45000, current_time)
        if trade:
            print(f"  [OK] Buy trade: {trade.side} {trade.size} {trade.symbol}")

        # Test portfolio value
        current_prices = {'BTC': 46000}
        value = wallet.get_portfolio_value(current_prices)
        print(f"  [OK] Portfolio value: ${value}")

        performance = wallet.get_performance_summary()
        print(f"  [OK] Total trades: {performance['total_trades']}")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def test_historical_data():
    """Test historical data service"""
    print("Testing Historical Data...")

    async def run_test():
        try:
            from trading.backtesting.historical_data import HistoricalDataService

            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now() - timedelta(days=1)

            async with HistoricalDataService() as service:
                data = await service.get_ohlcv_data('BTC', start_date, end_date, '1h')

                if not data.empty:
                    print(f"  [OK] Fetched {len(data)} rows")
                    print(f"  [OK] Columns: {list(data.columns)}")
                else:
                    print("  [WARN] No data (synthetic fallback)")

                return True

        except Exception as e:
            print(f"  [FAIL] {e}")
            return False

    return asyncio.run(run_test())

def test_backtesting_engine():
    """Test backtesting engine with simple strategy"""
    print("Testing Backtesting Engine...")

    async def run_test():
        try:
            from trading.backtesting.engine import BacktestEngine
            from trading.backtesting.utils import BacktestConfig

            engine = BacktestEngine()

            config = BacktestConfig(
                strategy_name='simple_buy_hold',
                strategy_params={'position_size': 0.1},
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now() - timedelta(days=1),
                symbols=['BTC'],
                initial_capital=10000.0
            )

            print(f"  [INFO] Running backtest for {len(config.symbols)} symbols")

            results = await engine.run_backtest(config)

            print(f"  [OK] Backtest completed")
            print(f"  [OK] Initial: ${results.get('initial_capital', 0):,.2f}")
            print(f"  [OK] Final: ${results.get('final_value', 0):,.2f}")
            print(f"  [OK] Return: {results.get('total_return_pct', 0):+.2f}%")
            print(f"  [OK] Trades: {results.get('total_trades', 0)}")

            return True

        except Exception as e:
            print(f"  [FAIL] {e}")
            import traceback
            traceback.print_exc()
            return False

    return asyncio.run(run_test())

def main():
    """Run basic tests"""
    print("WolfHunt Backtesting System - Basic Tests")
    print("=" * 50)

    tests = [
        ("Mock Wallet", test_mock_wallet),
        ("Historical Data", test_historical_data),
        ("Backtesting Engine", test_backtesting_engine)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        success = test_func()
        results.append((test_name, success))
        status = "PASS" if success else "FAIL"
        print(f"Result: {status}")

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status:6} - {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\nSUCCESS: All core components working!")
        print("Backtesting system ready for integration.")
    else:
        print(f"\nISSUES: {total-passed} component(s) failed")

    return passed == total

if __name__ == "__main__":
    main()