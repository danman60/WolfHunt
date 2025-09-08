#!/usr/bin/env python3
"""Test runner script for the dYdX trading bot."""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle output."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✅ {description or 'Command'} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for dYdX trading bot")
    parser.add_argument(
        '--suite',
        choices=['unit', 'integration', 'api', 'performance', 'all'],
        default='all',
        help='Test suite to run'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run with coverage reporting'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--parallel',
        '-p',
        type=int,
        default=1,
        help='Number of parallel workers'
    )
    parser.add_argument(
        '--markers',
        help='Run tests with specific markers (e.g., "not slow")'
    )
    
    args = parser.parse_args()
    
    # Change to project directory
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    print("🚀 dYdX Trading Bot Test Runner")
    print(f"Project root: {project_root}")
    print(f"Test suite: {args.suite}")
    
    # Build base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Add test paths based on suite
    if args.suite == 'unit':
        pytest_cmd.extend([
            "tests/test_trading/test_strategies.py",
            "tests/test_trading/test_risk_manager.py",
            "tests/test_trading/test_market_data.py",
            "tests/test_database/test_models.py",
            "tests/test_utils/"
        ])
    elif args.suite == 'integration':
        pytest_cmd.extend([
            "tests/test_integration/"
        ])
    elif args.suite == 'api':
        pytest_cmd.extend([
            "tests/test_api/"
        ])
    elif args.suite == 'performance':
        pytest_cmd.extend([
            "tests/test_performance/",
            "-m", "performance"
        ])
    else:  # all
        pytest_cmd.append("tests/")
    
    # Add options
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.coverage:
        pytest_cmd.extend([
            "--cov=backend/src",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    if args.parallel > 1:
        pytest_cmd.extend(["-n", str(args.parallel)])
    
    if args.markers:
        pytest_cmd.extend(["-m", args.markers])
    
    # Add additional options
    pytest_cmd.extend([
        "--tb=short",
        "--strict-markers"
    ])
    
    # Run the tests
    command = " ".join(pytest_cmd)
    success = run_command(command, f"Running {args.suite} tests")
    
    if success:
        print("\n🎉 All tests completed successfully!")
        
        if args.coverage:
            print("\n📊 Coverage report generated:")
            print("  - HTML: htmlcov/index.html")
            print("  - XML: coverage.xml")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)
    
    # Additional commands based on suite
    if args.suite in ['all', 'api'] and success:
        print("\n🔍 Running additional API validation...")
        # Could add API smoke tests here
    
    if args.suite in ['all', 'performance'] and success:
        print("\n📈 Performance test results available in test output above")


if __name__ == "__main__":
    main()