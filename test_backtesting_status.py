#!/usr/bin/env python3
"""
Test script to evaluate current backtesting implementation status in WolfHunt
"""
import sys
import os
import json
from datetime import datetime, timedelta

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_backend_imports():
    """Test if backend components are available"""
    print("Testing Backend Component Availability...")
    results = {}

    # Test by checking file existence instead of imports due to dependency issues
    schema_files = ['backend/src/api/schemas.py']
    for file_path in schema_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'BacktestRequest' in content and 'BacktestResult' in content:
                results['backtest_schemas'] = "Available"
                print("  [OK] Backtest schemas found in schemas.py")
            else:
                results['backtest_schemas'] = "Incomplete"
                print("  [WARN] schemas.py exists but missing backtest schemas")
        else:
            results['backtest_schemas'] = "Missing"
            print(f"  [FAIL] {file_path} not found")

    # Test strategy files
    strategy_files = ['backend/src/trading/strategies/ma_crossover.py']
    for file_path in strategy_files:
        if os.path.exists(file_path):
            results['strategy_engine'] = "Available"
            print("  [OK] Strategy engine files found")
        else:
            results['strategy_engine'] = "Missing"
            print(f"  [FAIL] {file_path} not found")

    # Test market data service
    market_data_files = ['backend/src/integrations/real_market_data.py']
    for file_path in market_data_files:
        if os.path.exists(file_path):
            results['market_data'] = "Available"
            print("  [OK] Market data service file found")
        else:
            results['market_data'] = "Missing"
            print(f"  [FAIL] {file_path} not found")

    return results

def test_paper_trading_implementation():
    """Test paper trading functionality"""
    print("\nTesting Paper Trading Implementation...")
    results = {}

    # Check if simple_main.py has paper trading endpoints
    try:
        with open('backend/simple_main.py', 'r', encoding='utf-8') as f:
            content = f.read()

        paper_trade_endpoints = [
            '/api/v1/paper-trade/execute',
            '/api/v1/paper-trade/portfolio',
            '/api/v1/paper-trade/strategy-execute'
        ]

        for endpoint in paper_trade_endpoints:
            if endpoint in content:
                results[endpoint] = "Implemented"
                print(f"  [OK] {endpoint} endpoint found")
            else:
                results[endpoint] = "Missing"
                print(f"  [FAIL] {endpoint} endpoint missing")

    except FileNotFoundError:
        results['paper_trading_file'] = "simple_main.py not found"
        print("  [FAIL] simple_main.py not found")

    return results

def evaluate_mock_wallet_capabilities():
    """Evaluate current mock wallet implementation"""
    print("\nEvaluating Mock Wallet Capabilities...")
    results = {}

    # Check for wallet/portfolio state management
    portfolio_features = {
        'balance_tracking': False,
        'position_management': False,
        'pnl_calculation': False,
        'trade_history': False
    }

    try:
        # Check database models for portfolio tracking
        with open('backend/src/database/models.py', 'r', encoding='utf-8') as f:
            models_content = f.read()

        if 'Portfolio' in models_content or 'Account' in models_content:
            portfolio_features['balance_tracking'] = True
            results['balance_tracking'] = "Database models exist"
        else:
            results['balance_tracking'] = "No portfolio models found"

        if 'Position' in models_content:
            portfolio_features['position_management'] = True
            results['position_management'] = "Position models exist"
        else:
            results['position_management'] = "No position models found"

        if 'Trade' in models_content:
            portfolio_features['trade_history'] = True
            results['trade_history'] = "Trade models exist"
        else:
            results['trade_history'] = "No trade models found"

    except FileNotFoundError:
        results['database_models'] = "Database models file not found"

    return results, portfolio_features

def assess_backtesting_gaps():
    """Assess what's missing for full backtesting"""
    print("\nAssessing Backtesting Implementation Gaps...")

    required_components = {
        'historical_data_source': False,
        'backtesting_engine': False,
        'mock_wallet_state': False,
        'strategy_simulation': False,
        'performance_metrics': False,
        'time_series_processing': False
    }

    # Check for backtesting-specific files
    backtesting_files = [
        'backend/src/trading/backtesting/',
        'backend/src/trading/backtesting/engine.py',
        'backend/src/trading/backtesting/mock_wallet.py',
        'backend/src/trading/backtesting/historical_data.py'
    ]

    results = {}
    for file_path in backtesting_files:
        if os.path.exists(file_path):
            required_components[file_path.split('/')[-1].replace('.py', '')] = True
            results[file_path] = "Exists"
            print(f"  [OK] {file_path} exists")
        else:
            results[file_path] = "Missing"
            print(f"  [FAIL] {file_path} missing")

    return results, required_components

def main():
    """Main test execution"""
    print("WolfHunt Backtesting Status Assessment")
    print("=" * 50)

    # Test backend components
    backend_results = test_backend_imports()

    # Test paper trading
    paper_results = test_paper_trading_implementation()

    # Evaluate mock wallet
    wallet_results, wallet_features = evaluate_mock_wallet_capabilities()

    # Assess backtesting gaps
    gap_results, required_components = assess_backtesting_gaps()

    # Generate summary
    print("\nSUMMARY REPORT")
    print("=" * 30)

    total_checks = len(backend_results) + len(paper_results) + len(wallet_results) + len(gap_results)
    passed_checks = sum([1 for result in [*backend_results.values(), *paper_results.values(),
                        *wallet_results.values(), *gap_results.values()] if "Available" in result or "Implemented" in result or "exists" in result or "exist" in result])

    print(f"Overall Status: {passed_checks}/{total_checks} components ready")
    print(f"Readiness: {(passed_checks/total_checks)*100:.1f}%")

    # Readiness assessment
    if passed_checks >= total_checks * 0.8:
        print("[HIGH] Backtesting mostly implementable")
    elif passed_checks >= total_checks * 0.6:
        print("[MEDIUM] Some components need implementation")
    else:
        print("[LOW] Significant development needed")

    # Save detailed results
    full_results = {
        'timestamp': datetime.now().isoformat(),
        'backend_components': backend_results,
        'paper_trading': paper_results,
        'mock_wallet': wallet_results,
        'wallet_features': wallet_features,
        'backtesting_gaps': gap_results,
        'required_components': required_components,
        'summary': {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'readiness_percent': (passed_checks/total_checks)*100
        }
    }

    with open('backtesting_assessment.json', 'w') as f:
        json.dump(full_results, f, indent=2)

    print(f"\nDetailed results saved to: backtesting_assessment.json")

    return full_results

if __name__ == "__main__":
    main()