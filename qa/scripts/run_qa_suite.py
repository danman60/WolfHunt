#!/usr/bin/env python3
"""QA Suite Runner - Comprehensive quality assurance testing."""

import sys
import subprocess
import argparse
import os
import time
import json
from pathlib import Path
from datetime import datetime
import concurrent.futures
from typing import Dict, List, Any


class QATestRunner:
    """Comprehensive QA test runner."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.qa_root = self.project_root / "qa"
        self.reports_dir = self.qa_root / "reports"
        self.results = {}
        
        # Ensure reports directory exists
        self.reports_dir.mkdir(exist_ok=True)
        
        # Test suites configuration
        self.test_suites = {
            "unit": {
                "description": "Unit Tests",
                "command": "python -m pytest tests/ -m 'not integration and not e2e and not performance' --tb=short",
                "timeout": 300,  # 5 minutes
                "critical": True
            },
            "integration": {
                "description": "Integration Tests", 
                "command": "python -m pytest tests/test_integration/ tests/test_api/ -v --tb=short",
                "timeout": 900,  # 15 minutes
                "critical": True
            },
            "e2e": {
                "description": "End-to-End Tests",
                "command": "python -m pytest qa/e2e_tests/ -v --tb=short --browser chromium",
                "timeout": 1800,  # 30 minutes
                "critical": False
            },
            "load": {
                "description": "Load Tests",
                "command": "python qa/load_tests/run_load_tests.py",
                "timeout": 1200,  # 20 minutes
                "critical": False
            },
            "security": {
                "description": "Security Tests",
                "command": "python qa/security_tests/run_security_tests.py",
                "timeout": 600,  # 10 minutes
                "critical": True
            },
            "performance": {
                "description": "Performance Tests",
                "command": "python -m pytest tests/test_performance/ -m performance --tb=short",
                "timeout": 900,  # 15 minutes
                "critical": False
            }
        }
    
    def run_command(self, command: str, timeout: int = 300, description: str = "") -> Dict[str, Any]:
        """Run a command with timeout and capture results."""
        print(f"\n{'='*60}")
        print(f"Running: {description or command}")
        print(f"Timeout: {timeout}s")
        print('='*60)
        
        start_time = time.time()
        
        try:
            # Change to project root
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.returncode == 0
            
            test_result = {
                "command": command,
                "description": description,
                "success": success,
                "return_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "start_time": start_time,
                "end_time": end_time
            }
            
            if success:
                print(f"✅ {description} completed successfully in {duration:.1f}s")
            else:
                print(f"❌ {description} failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error output:\n{result.stderr[:500]}...")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏰ {description} timed out after {duration:.1f}s")
            
            return {
                "command": command,
                "description": description,
                "success": False,
                "return_code": -1,
                "duration": duration,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "start_time": start_time,
                "end_time": end_time,
                "timeout": True
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"💥 {description} failed with exception: {e}")
            
            return {
                "command": command,
                "description": description,
                "success": False,
                "return_code": -1,
                "duration": duration,
                "stdout": "",
                "stderr": str(e),
                "start_time": start_time,
                "end_time": end_time,
                "exception": True
            }
    
    def run_suite(self, suite_name: str) -> Dict[str, Any]:
        """Run a specific test suite."""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite_config = self.test_suites[suite_name]
        
        return self.run_command(
            command=suite_config["command"],
            timeout=suite_config["timeout"],
            description=suite_config["description"]
        )
    
    def run_parallel_suites(self, suite_names: List[str]) -> Dict[str, Any]:
        """Run multiple test suites in parallel."""
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_suite = {
                executor.submit(self.run_suite, suite_name): suite_name
                for suite_name in suite_names
            }
            
            for future in concurrent.futures.as_completed(future_to_suite):
                suite_name = future_to_suite[future]
                try:
                    result = future.result()
                    results[suite_name] = result
                except Exception as exc:
                    print(f"Suite {suite_name} generated an exception: {exc}")
                    results[suite_name] = {
                        "success": False,
                        "error": str(exc),
                        "exception": True
                    }
        
        return results
    
    def run_sequential_suites(self, suite_names: List[str]) -> Dict[str, Any]:
        """Run multiple test suites sequentially."""
        results = {}
        
        for suite_name in suite_names:
            print(f"\n🚀 Running {suite_name} test suite...")
            result = self.run_suite(suite_name)
            results[suite_name] = result
            
            # Stop on critical failure if configured
            if not result["success"] and self.test_suites[suite_name].get("critical", False):
                print(f"💥 Critical test suite {suite_name} failed. Stopping execution.")
                break
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive QA report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.reports_dir / timestamp
        report_dir.mkdir(exist_ok=True)
        
        # Calculate overall statistics
        total_suites = len(results)
        passed_suites = sum(1 for r in results.values() if r.get("success", False))
        failed_suites = total_suites - passed_suites
        total_duration = sum(r.get("duration", 0) for r in results.values())
        
        # Generate HTML report
        html_report = self._generate_html_report(results, {
            "total_suites": total_suites,
            "passed_suites": passed_suites,
            "failed_suites": failed_suites,
            "total_duration": total_duration,
            "timestamp": timestamp
        })
        
        # Write HTML report
        html_file = report_dir / "index.html"
        with open(html_file, 'w') as f:
            f.write(html_report)
        
        # Write JSON report for programmatic access
        json_file = report_dir / "results.json"
        with open(json_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "summary": {
                    "total_suites": total_suites,
                    "passed_suites": passed_suites,
                    "failed_suites": failed_suites,
                    "total_duration": total_duration,
                    "success_rate": passed_suites / total_suites if total_suites > 0 else 0
                },
                "results": results
            }, f, indent=2, default=str)
        
        # Create symlink to latest report
        latest_link = self.reports_dir / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(report_dir)
        
        print(f"\n📊 QA Report generated:")
        print(f"  HTML: {html_file}")
        print(f"  JSON: {json_file}")
        print(f"  Latest: {latest_link}")
        
        return str(html_file)
    
    def _generate_html_report(self, results: Dict[str, Any], summary: Dict[str, Any]) -> str:
        """Generate HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>dYdX Trading Bot - QA Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
                .summary-card h3 {{ margin: 0; color: #495057; }}
                .summary-card .value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
                .success {{ color: #28a745; }}
                .failure {{ color: #dc3545; }}
                .warning {{ color: #ffc107; }}
                .results {{ margin-top: 30px; }}
                .suite-result {{ margin-bottom: 20px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
                .suite-header {{ padding: 15px; cursor: pointer; }}
                .suite-header.success {{ background-color: #d4edda; }}
                .suite-header.failure {{ background-color: #f8d7da; }}
                .suite-details {{ padding: 15px; display: none; background-color: #f8f9fa; }}
                .suite-details.show {{ display: block; }}
                .output {{ background: #f1f3f4; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
                .timestamp {{ color: #6c757d; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>dYdX Trading Bot - QA Report</h1>
                    <p class="timestamp">Generated: {summary['timestamp']}</p>
                </div>
                
                <div class="summary">
                    <div class="summary-card">
                        <h3>Total Suites</h3>
                        <div class="value">{summary['total_suites']}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Passed</h3>
                        <div class="value success">{summary['passed_suites']}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Failed</h3>
                        <div class="value failure">{summary['failed_suites']}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Duration</h3>
                        <div class="value">{summary['total_duration']:.1f}s</div>
                    </div>
                </div>
                
                <div class="results">
                    <h2>Test Suite Results</h2>
        """
        
        for suite_name, result in results.items():
            status_class = "success" if result.get("success", False) else "failure"
            status_icon = "✅" if result.get("success", False) else "❌"
            
            html += f"""
                    <div class="suite-result">
                        <div class="suite-header {status_class}" onclick="toggleDetails('{suite_name}')">
                            <strong>{status_icon} {result.get('description', suite_name)}</strong>
                            <span style="float: right;">Duration: {result.get('duration', 0):.1f}s</span>
                        </div>
                        <div class="suite-details" id="{suite_name}-details">
                            <p><strong>Command:</strong> <code>{result.get('command', 'N/A')}</code></p>
                            <p><strong>Return Code:</strong> {result.get('return_code', 'N/A')}</p>
                            
                            {f'<h4>Output:</h4><div class="output">{result.get("stdout", "")[:2000]}</div>' if result.get("stdout") else ''}
                            
                            {f'<h4>Errors:</h4><div class="output">{result.get("stderr", "")[:2000]}</div>' if result.get("stderr") else ''}
                        </div>
                    </div>
            """
        
        html += """
                </div>
            </div>
            
            <script>
                function toggleDetails(suiteId) {
                    const details = document.getElementById(suiteId + '-details');
                    if (details.classList.contains('show')) {
                        details.classList.remove('show');
                    } else {
                        details.classList.add('show');
                    }
                }
            </script>
        </body>
        </html>
        """
        
        return html
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test execution summary."""
        print(f"\n{'='*60}")
        print("🎯 QA SUITE EXECUTION SUMMARY")
        print('='*60)
        
        total_suites = len(results)
        passed_suites = sum(1 for r in results.values() if r.get("success", False))
        failed_suites = total_suites - passed_suites
        total_duration = sum(r.get("duration", 0) for r in results.values())
        
        print(f"Total Suites: {total_suites}")
        print(f"Passed: {passed_suites} ✅")
        print(f"Failed: {failed_suites} ❌")
        print(f"Success Rate: {(passed_suites/total_suites)*100:.1f}%")
        print(f"Total Duration: {total_duration:.1f}s")
        
        print(f"\n{'Suite Results':<20} {'Status':<10} {'Duration':<10}")
        print('-' * 45)
        
        for suite_name, result in results.items():
            status = "PASSED" if result.get("success", False) else "FAILED"
            duration = result.get("duration", 0)
            print(f"{suite_name:<20} {status:<10} {duration:<10.1f}s")
        
        # Quality Gates Assessment
        print(f"\n{'Quality Gates Assessment'}")
        print('-' * 30)
        
        critical_failures = []
        for suite_name, result in results.items():
            if not result.get("success", False) and self.test_suites[suite_name].get("critical", False):
                critical_failures.append(suite_name)
        
        if critical_failures:
            print(f"🚨 CRITICAL FAILURES: {', '.join(critical_failures)}")
            print("❌ Quality gates FAILED - Do not deploy")
        else:
            print("✅ All critical tests passed")
            if failed_suites == 0:
                print("🎉 All quality gates PASSED - Safe to deploy")
            else:
                print("⚠️  Non-critical tests failed - Review before deploy")


def main():
    parser = argparse.ArgumentParser(description="Run comprehensive QA test suite")
    parser.add_argument(
        '--category',
        choices=['unit', 'integration', 'e2e', 'load', 'security', 'performance', 'all'],
        default='all',
        help='Test category to run'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run compatible test suites in parallel'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report from existing results'
    )
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first critical failure'
    )
    
    args = parser.parse_args()
    
    runner = QATestRunner()
    
    print("🚀 dYdX Trading Bot - QA Suite Runner")
    print(f"Category: {args.category}")
    print(f"Parallel: {args.parallel}")
    
    # Determine which suites to run
    if args.category == 'all':
        suite_names = list(runner.test_suites.keys())
    else:
        suite_names = [args.category]
    
    # Run tests
    if args.report_only:
        # Load existing results (placeholder - would need implementation)
        print("Report-only mode not implemented yet")
        return
    
    start_time = time.time()
    
    if args.parallel and len(suite_names) > 1:
        # Run compatible suites in parallel
        parallel_suites = ['unit', 'integration']  # Safe to run in parallel
        sequential_suites = [s for s in suite_names if s not in parallel_suites]
        
        results = {}
        
        if any(s in suite_names for s in parallel_suites):
            parallel_to_run = [s for s in parallel_suites if s in suite_names]
            parallel_results = runner.run_parallel_suites(parallel_to_run)
            results.update(parallel_results)
        
        if sequential_suites:
            sequential_results = runner.run_sequential_suites(sequential_suites)
            results.update(sequential_results)
    else:
        results = runner.run_sequential_suites(suite_names)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Generate report
    report_file = runner.generate_report(results)
    
    # Print summary
    runner.print_summary(results)
    
    print(f"\n⏱️  Total execution time: {total_time:.1f}s")
    
    # Determine exit code
    critical_failures = any(
        not result.get("success", False) and runner.test_suites[suite_name].get("critical", False)
        for suite_name, result in results.items()
    )
    
    if critical_failures:
        print("\n💥 QA Suite FAILED - Critical tests failed")
        sys.exit(1)
    else:
        print("\n🎉 QA Suite COMPLETED")
        sys.exit(0)


if __name__ == "__main__":
    main()