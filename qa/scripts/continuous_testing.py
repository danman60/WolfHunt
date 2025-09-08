#!/usr/bin/env python3
"""Continuous testing automation script."""

import os
import sys
import time
import subprocess
import json
import schedule
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart


class ContinuousTestingManager:
    """Manages continuous testing processes and schedules."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.qa_root = self.project_root / "qa"
        self.reports_dir = self.qa_root / "reports"
        self.config = self.load_config()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.qa_root / "continuous_testing.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """Load continuous testing configuration."""
        config_file = self.qa_root / "continuous_testing_config.json"
        
        default_config = {
            "schedules": {
                "unit_tests": {"interval": "commit", "enabled": True},
                "integration_tests": {"interval": "hourly", "enabled": True},
                "e2e_tests": {"interval": "daily", "enabled": True},
                "load_tests": {"interval": "daily", "enabled": True},
                "security_tests": {"interval": "daily", "enabled": True},
                "performance_tests": {"interval": "weekly", "enabled": True}
            },
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": ""
                }
            },
            "quality_gates": {
                "unit_test_coverage": 90,
                "critical_test_failure_threshold": 0,
                "performance_regression_threshold": 10
            },
            "environments": {
                "development": {
                    "api_url": "http://localhost:8000",
                    "frontend_url": "http://localhost:3000"
                },
                "staging": {
                    "api_url": "https://staging-api.example.com",
                    "frontend_url": "https://staging.example.com"
                }
            }
        }
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = default_config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        
        return config
    
    def run_test_suite(self, suite_name: str, environment: str = "development") -> Dict[str, Any]:
        """Run a specific test suite."""
        self.logger.info(f"Running {suite_name} test suite in {environment} environment")
        
        env_config = self.config["environments"].get(environment, {})
        
        # Set environment variables
        os.environ["TEST_API_URL"] = env_config.get("api_url", "http://localhost:8000")
        os.environ["TEST_FRONTEND_URL"] = env_config.get("frontend_url", "http://localhost:3000")
        
        # Run the appropriate test command
        test_commands = {
            "unit": ["python", "-m", "pytest", "tests/", "-m", "not integration and not e2e", "--cov=backend/src", "--cov-report=json"],
            "integration": ["python", "-m", "pytest", "tests/test_integration/", "tests/test_api/", "--tb=short"],
            "e2e": ["python", "-m", "pytest", "qa/e2e_tests/", "--browser", "chromium", "--headless"],
            "load": ["python", "qa/load_tests/locustfile.py", "normal_load"],
            "security": ["python", "qa/security_tests/run_security_tests.py"],
            "performance": ["python", "-m", "pytest", "tests/test_performance/", "-m", "performance"]
        }
        
        if suite_name not in test_commands:
            self.logger.error(f"Unknown test suite: {suite_name}")
            return {"success": False, "error": f"Unknown test suite: {suite_name}"}
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                test_commands[suite_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            test_result = {
                "suite": suite_name,
                "environment": environment,
                "success": success,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
            # Store result
            self.store_test_result(test_result)
            
            # Send notifications if configured
            if not success:
                self.send_failure_notification(test_result)
            
            return test_result
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Test suite {suite_name} timed out")
            return {"success": False, "error": "Test suite timed out", "duration": time.time() - start_time}
        
        except Exception as e:
            self.logger.error(f"Error running test suite {suite_name}: {e}")
            return {"success": False, "error": str(e), "duration": time.time() - start_time}
    
    def store_test_result(self, result: Dict[str, Any]):
        """Store test result for historical tracking."""
        results_dir = self.reports_dir / "continuous"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = results_dir / f"{result['suite']}_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Also append to daily log
        daily_log_file = results_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(daily_log_file, 'a') as f:
            f.write(json.dumps(result) + '\n')
    
    def send_failure_notification(self, result: Dict[str, Any]):
        """Send notification for test failures."""
        if self.config["notifications"]["email"]["enabled"]:
            self.send_email_notification(result)
        
        if self.config["notifications"]["slack"]["enabled"]:
            self.send_slack_notification(result)
    
    def send_email_notification(self, result: Dict[str, Any]):
        """Send email notification for test failure."""
        try:
            email_config = self.config["notifications"]["email"]
            
            msg = MimeMultipart()
            msg['From'] = email_config["username"]
            msg['To'] = ", ".join(email_config["recipients"])
            msg['Subject'] = f"🚨 Test Failure: {result['suite']} suite failed"
            
            body = f"""
            Test Suite: {result['suite']}
            Environment: {result['environment']}
            Duration: {result['duration']:.2f}s
            Timestamp: {result['timestamp']}
            
            Error Output:
            {result.get('stderr', 'No error output')}
            
            Please check the continuous testing dashboard for more details.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Email notification sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
    
    def send_slack_notification(self, result: Dict[str, Any]):
        """Send Slack notification for test failure."""
        try:
            import requests
            
            webhook_url = self.config["notifications"]["slack"]["webhook_url"]
            
            message = {
                "text": f"🚨 Test Failure Alert",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {"title": "Test Suite", "value": result['suite'], "short": True},
                            {"title": "Environment", "value": result['environment'], "short": True},
                            {"title": "Duration", "value": f"{result['duration']:.2f}s", "short": True},
                            {"title": "Timestamp", "value": result['timestamp'], "short": True},
                        ]
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=message)
            if response.status_code == 200:
                self.logger.info("Slack notification sent")
            else:
                self.logger.error(f"Failed to send Slack notification: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
    
    def check_quality_gates(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if quality gates are met."""
        gates = self.config["quality_gates"]
        
        # Check critical test failures
        critical_failures = sum(1 for r in results if not r["success"] and r["suite"] in ["unit", "integration", "security"])
        
        # Check unit test coverage (if available)
        coverage_met = True  # Would check actual coverage from reports
        
        # Check performance regressions (simplified)
        performance_regression = False  # Would check actual performance metrics
        
        quality_gates_passed = (
            critical_failures <= gates["critical_test_failure_threshold"] and
            coverage_met and
            not performance_regression
        )
        
        return {
            "passed": quality_gates_passed,
            "critical_failures": critical_failures,
            "coverage_met": coverage_met,
            "performance_regression": performance_regression
        }
    
    def generate_trend_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate trend report for the last N days."""
        results_dir = self.reports_dir / "continuous"
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        trends = {}
        
        # Analyze daily logs
        for i in range(days):
            date = start_date + timedelta(days=i)
            daily_log_file = results_dir / f"daily_{date.strftime('%Y%m%d')}.jsonl"
            
            if daily_log_file.exists():
                daily_results = []
                with open(daily_log_file, 'r') as f:
                    for line in f:
                        try:
                            result = json.loads(line.strip())
                            daily_results.append(result)
                        except json.JSONDecodeError:
                            continue
                
                # Calculate daily metrics
                total_tests = len(daily_results)
                passed_tests = sum(1 for r in daily_results if r["success"])
                avg_duration = sum(r["duration"] for r in daily_results) / total_tests if total_tests > 0 else 0
                
                trends[date.strftime('%Y-%m-%d')] = {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                    "avg_duration": avg_duration
                }
        
        return trends
    
    def run_scheduled_tests(self):
        """Run tests based on schedule configuration."""
        current_time = datetime.now()
        
        for suite_name, schedule_config in self.config["schedules"].items():
            if not schedule_config["enabled"]:
                continue
            
            interval = schedule_config["interval"]
            
            # Simple scheduling logic (in production, would use more sophisticated scheduling)
            should_run = False
            
            if interval == "hourly":
                should_run = current_time.minute == 0
            elif interval == "daily":
                should_run = current_time.hour == 6 and current_time.minute == 0  # Run at 6 AM
            elif interval == "weekly":
                should_run = current_time.weekday() == 0 and current_time.hour == 6 and current_time.minute == 0  # Monday 6 AM
            
            if should_run:
                self.logger.info(f"Running scheduled test: {suite_name}")
                result = self.run_test_suite(suite_name)
                
                if not result["success"]:
                    self.logger.error(f"Scheduled test {suite_name} failed")
    
    def start_continuous_testing(self):
        """Start the continuous testing daemon."""
        self.logger.info("Starting continuous testing daemon")
        
        # Schedule tests based on configuration
        for suite_name, schedule_config in self.config["schedules"].items():
            if not schedule_config["enabled"]:
                continue
            
            interval = schedule_config["interval"]
            
            if interval == "hourly":
                schedule.every().hour.do(self.run_test_suite, suite_name)
            elif interval == "daily":
                schedule.every().day.at("06:00").do(self.run_test_suite, suite_name)
            elif interval == "weekly":
                schedule.every().monday.at("06:00").do(self.run_test_suite, suite_name)
        
        # Main loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.info("Continuous testing daemon stopped")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous testing daemon: {e}")
                time.sleep(60)


def main():
    """Main entry point for continuous testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous testing manager")
    parser.add_argument(
        "command",
        choices=["start", "run", "report", "config"],
        help="Command to execute"
    )
    parser.add_argument(
        "--suite",
        choices=["unit", "integration", "e2e", "load", "security", "performance"],
        help="Test suite to run (for 'run' command)"
    )
    parser.add_argument(
        "--environment",
        default="development",
        help="Environment to test against"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days for trend report"
    )
    
    args = parser.parse_args()
    
    manager = ContinuousTestingManager()
    
    if args.command == "start":
        manager.start_continuous_testing()
    
    elif args.command == "run":
        if not args.suite:
            print("Error: --suite is required for 'run' command")
            sys.exit(1)
        
        result = manager.run_test_suite(args.suite, args.environment)
        
        if result["success"]:
            print(f"✅ Test suite {args.suite} passed")
            sys.exit(0)
        else:
            print(f"❌ Test suite {args.suite} failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    elif args.command == "report":
        trends = manager.generate_trend_report(args.days)
        
        print(f"📊 Test Trends Report ({args.days} days)")
        print("=" * 50)
        
        for date, metrics in trends.items():
            print(f"{date}: {metrics['total_tests']} tests, "
                  f"{metrics['success_rate']:.1f}% success rate, "
                  f"{metrics['avg_duration']:.1f}s avg duration")
    
    elif args.command == "config":
        print("📝 Continuous Testing Configuration")
        print(json.dumps(manager.config, indent=2))


if __name__ == "__main__":
    main()