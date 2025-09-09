#!/usr/bin/env python3
"""
🚀 WOLF PACK TEST RUNNER
Comprehensive test execution for the Wolf Pack Intelligence System
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

def run_tests(test_type="all", verbose=False, coverage=False):
    """Run Wolf Pack test suite"""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directories
    test_dir = Path(__file__).parent
    
    if test_type == "all":
        cmd.append(str(test_dir))
    elif test_type == "intelligence":
        cmd.append(str(test_dir / "test_intelligence_engine.py"))
    elif test_type == "automation":
        cmd.append(str(test_dir / "test_automation_engine.py"))
    elif test_type == "api":
        cmd.append(str(test_dir / "test_api_endpoints.py"))
    else:
        cmd.append(str(test_dir / f"test_{test_type}.py"))
    
    # Add options
    if verbose:
        cmd.extend(["-v", "-s"])
    
    if coverage:
        cmd.extend([
            "--cov=src.integrations.wolfpack_intelligence",
            "--cov=src.integrations.strategy_automation", 
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Add markers for better test organization
    cmd.extend([
        "--tb=short",
        "--durations=10",
        "-p", "no:warnings"  # Suppress warnings for cleaner output
    ])
    
    print(f"Running Wolf Pack tests: {test_type}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1

def check_dependencies():
    """Check if required test dependencies are available"""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov",
        "httpx",
        "fastapi[all]"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.split('[')[0].replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required test dependencies:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False
    
    print("All test dependencies are available")
    return True

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Wolf Pack Test Runner")
    parser.add_argument(
        "test_type", 
        choices=["all", "intelligence", "automation", "api", "unit", "integration"],
        default="all",
        nargs="?",
        help="Type of tests to run"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies only")
    
    args = parser.parse_args()
    
    if args.check_deps:
        return 0 if check_dependencies() else 1
    
    print("WOLF PACK INTELLIGENCE TEST SUITE")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        return 1
    
    # Run tests
    return run_tests(args.test_type, args.verbose, args.coverage)

if __name__ == "__main__":
    sys.exit(main())