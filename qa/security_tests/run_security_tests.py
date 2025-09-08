#!/usr/bin/env python3
"""Security testing suite for the dYdX trading bot."""

import sys
import requests
import json
import time
import subprocess
from typing import Dict, List, Any
import concurrent.futures
from urllib.parse import urljoin


class SecurityTester:
    """Comprehensive security testing framework."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
        # Test credentials
        self.test_credentials = {
            "valid": {
                "email": "security_test@example.com",
                "password": "SecurePassword123!"
            },
            "invalid": {
                "email": "invalid@example.com",
                "password": "wrongpassword"
            }
        }
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> Dict[str, Any]:
        """Run a security test and record results."""
        print(f"Running: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func(*args, **kwargs)
            success = result.get("passed", False)
            
            test_result = {
                "test_name": test_name,
                "passed": success,
                "duration": time.time() - start_time,
                "details": result,
                "timestamp": time.time()
            }
            
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {status} - {test_name}")
            
            if not success and result.get("details"):
                print(f"    Details: {result['details']}")
            
            self.results.append(test_result)
            return test_result
            
        except Exception as e:
            test_result = {
                "test_name": test_name,
                "passed": False,
                "duration": time.time() - start_time,
                "details": {"error": str(e)},
                "exception": True,
                "timestamp": time.time()
            }
            
            print(f"  ❌ FAILED - {test_name}: {e}")
            self.results.append(test_result)
            return test_result
    
    def test_authentication_security(self) -> Dict[str, Any]:
        """Test authentication security measures."""
        tests = []
        
        # Test 1: Login with invalid credentials
        response = self.session.post(
            urljoin(self.base_url, "/api/auth/login"),
            json=self.test_credentials["invalid"]
        )
        tests.append({
            "name": "Invalid credentials rejection",
            "passed": response.status_code == 401,
            "details": f"Status: {response.status_code}"
        })
        
        # Test 2: Brute force protection
        failed_attempts = 0
        for _ in range(6):  # Try 6 failed login attempts
            response = self.session.post(
                urljoin(self.base_url, "/api/auth/login"),
                json=self.test_credentials["invalid"]
            )
            if response.status_code == 429:  # Too Many Requests
                break
            failed_attempts += 1
        
        tests.append({
            "name": "Brute force protection",
            "passed": failed_attempts < 6,  # Should be blocked before 6 attempts
            "details": f"Failed attempts before blocking: {failed_attempts}"
        })
        
        # Test 3: Token expiration
        # First, get a valid token
        login_response = self.session.post(
            urljoin(self.base_url, "/api/auth/login"),
            json=self.test_credentials["valid"]
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            
            # Try to use token immediately (should work)
            headers = {"Authorization": f"Bearer {token}"}
            immediate_response = self.session.get(
                urljoin(self.base_url, "/api/trading/dashboard"),
                headers=headers
            )
            
            # Test with expired/invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token"}
            invalid_response = self.session.get(
                urljoin(self.base_url, "/api/trading/dashboard"),
                headers=invalid_headers
            )
            
            tests.append({
                "name": "Token validation",
                "passed": immediate_response.status_code == 200 and invalid_response.status_code == 401,
                "details": f"Valid token: {immediate_response.status_code}, Invalid token: {invalid_response.status_code}"
            })
        
        return {
            "passed": all(test["passed"] for test in tests),
            "details": tests
        }
    
    def test_input_validation(self) -> Dict[str, Any]:
        """Test input validation and sanitization."""
        tests = []
        
        # Get authentication token
        login_response = self.session.post(
            urljoin(self.base_url, "/api/auth/login"),
            json=self.test_credentials["valid"]
        )
        
        if login_response.status_code != 200:
            return {"passed": False, "details": "Could not authenticate for input validation tests"}
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: SQL Injection attempts
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
            "'; SELECT * FROM users; --"
        ]
        
        sql_injection_blocked = 0
        for payload in sql_payloads:
            response = self.session.get(
                urljoin(self.base_url, f"/api/trading/trades?symbol={payload}"),
                headers=headers
            )
            if response.status_code in [400, 422]:  # Bad request or validation error
                sql_injection_blocked += 1
        
        tests.append({
            "name": "SQL Injection protection",
            "passed": sql_injection_blocked == len(sql_payloads),
            "details": f"Blocked {sql_injection_blocked}/{len(sql_payloads)} SQL injection attempts"
        })
        
        # Test 2: XSS attempts
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        xss_blocked = 0
        for payload in xss_payloads:
            # Try to submit XSS in various fields
            order_data = {
                "symbol": payload,
                "side": "BUY",
                "order_type": "MARKET",
                "size": 0.001
            }
            
            response = self.session.post(
                urljoin(self.base_url, "/api/trading/place-order"),
                json=order_data,
                headers=headers
            )
            
            if response.status_code in [400, 422]:
                xss_blocked += 1
        
        tests.append({
            "name": "XSS protection",
            "passed": xss_blocked == len(xss_payloads),
            "details": f"Blocked {xss_blocked}/{len(xss_payloads)} XSS attempts"
        })
        
        # Test 3: Oversized payload protection
        large_payload = "A" * 10000  # 10KB string
        response = self.session.post(
            urljoin(self.base_url, "/api/trading/place-order"),
            json={"symbol": large_payload, "side": "BUY", "size": 0.001},
            headers=headers
        )
        
        tests.append({
            "name": "Oversized payload protection",
            "passed": response.status_code in [400, 413, 422],  # Bad Request or Payload Too Large
            "details": f"Large payload response: {response.status_code}"
        })
        
        # Test 4: Invalid data types
        invalid_data = {
            "symbol": 123,  # Should be string
            "side": ["BUY"],  # Should be string
            "size": "invalid",  # Should be number
            "price": None
        }
        
        response = self.session.post(
            urljoin(self.base_url, "/api/trading/place-order"),
            json=invalid_data,
            headers=headers
        )
        
        tests.append({
            "name": "Data type validation",
            "passed": response.status_code in [400, 422],
            "details": f"Invalid data types response: {response.status_code}"
        })
        
        return {
            "passed": all(test["passed"] for test in tests),
            "details": tests
        }
    
    def test_authorization_security(self) -> Dict[str, Any]:
        """Test authorization and access control."""
        tests = []
        
        # Test 1: Unauthorized access to protected endpoints
        protected_endpoints = [
            "/api/trading/dashboard",
            "/api/trading/positions",
            "/api/trading/place-order",
            "/api/trading/strategy/config",
            "/api/health/detailed"
        ]
        
        unauthorized_blocked = 0
        for endpoint in protected_endpoints:
            response = self.session.get(urljoin(self.base_url, endpoint))
            if response.status_code == 401:
                unauthorized_blocked += 1
        
        tests.append({
            "name": "Unauthorized access protection",
            "passed": unauthorized_blocked == len(protected_endpoints),
            "details": f"Blocked {unauthorized_blocked}/{len(protected_endpoints)} unauthorized requests"
        })
        
        # Test 2: Token manipulation
        # Get valid token
        login_response = self.session.post(
            urljoin(self.base_url, "/api/auth/login"),
            json=self.test_credentials["valid"]
        )
        
        if login_response.status_code == 200:
            original_token = login_response.json().get("access_token")
            
            # Manipulate token
            manipulated_tokens = [
                original_token[:-5] + "XXXXX",  # Changed ending
                original_token.replace(".", "X"),  # Changed structure
                "Bearer " + original_token,  # Double bearer
                original_token + ".extra"  # Added extra part
            ]
            
            token_manipulation_blocked = 0
            for token in manipulated_tokens:
                headers = {"Authorization": f"Bearer {token}"}
                response = self.session.get(
                    urljoin(self.base_url, "/api/trading/dashboard"),
                    headers=headers
                )
                if response.status_code == 401:
                    token_manipulation_blocked += 1
            
            tests.append({
                "name": "Token manipulation protection",
                "passed": token_manipulation_blocked == len(manipulated_tokens),
                "details": f"Blocked {token_manipulation_blocked}/{len(manipulated_tokens)} manipulated tokens"
            })
        
        return {
            "passed": all(test["passed"] for test in tests),
            "details": tests
        }
    
    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting and DoS protection."""
        tests = []
        
        # Get authentication token
        login_response = self.session.post(
            urljoin(self.base_url, "/api/auth/login"),
            json=self.test_credentials["valid"]
        )
        
        if login_response.status_code != 200:
            return {"passed": False, "details": "Could not authenticate for rate limiting tests"}
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: API rate limiting
        rapid_requests = 0
        rate_limited = False
        
        for i in range(100):  # Send 100 rapid requests
            response = self.session.get(
                urljoin(self.base_url, "/api/trading/dashboard"),
                headers=headers
            )
            rapid_requests += 1
            
            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                break
            
            # Small delay to avoid overwhelming
            time.sleep(0.01)
        
        tests.append({
            "name": "API rate limiting",
            "passed": rate_limited,
            "details": f"Rate limited after {rapid_requests} requests"
        })
        
        # Test 2: Order placement rate limiting
        order_attempts = 0
        order_rate_limited = False
        
        for i in range(20):  # Try to place 20 rapid orders
            order_data = {
                "symbol": "BTC-USD",
                "side": "BUY",
                "order_type": "MARKET",
                "size": 0.001,
                "paper_trade": True
            }
            
            response = self.session.post(
                urljoin(self.base_url, "/api/trading/place-order"),
                json=order_data,
                headers=headers
            )
            order_attempts += 1
            
            if response.status_code == 429:
                order_rate_limited = True
                break
            
            time.sleep(0.1)  # Brief delay
        
        tests.append({
            "name": "Order placement rate limiting",
            "passed": order_rate_limited or order_attempts < 10,  # Should be limited quickly
            "details": f"Rate limited after {order_attempts} order attempts"
        })
        
        return {
            "passed": all(test["passed"] for test in tests),
            "details": tests
        }
    
    def test_data_encryption(self) -> Dict[str, Any]:
        """Test data encryption and sensitive data protection."""
        tests = []
        
        # Test 1: HTTPS enforcement (if applicable)
        if self.base_url.startswith("https"):
            # Test HTTP redirect to HTTPS
            http_url = self.base_url.replace("https://", "http://")
            try:
                response = requests.get(http_url, allow_redirects=False, timeout=5)
                https_redirect = response.status_code in [301, 302, 307, 308]
                
                tests.append({
                    "name": "HTTPS enforcement",
                    "passed": https_redirect,
                    "details": f"HTTP redirect status: {response.status_code}"
                })
            except requests.exceptions.RequestException:
                tests.append({
                    "name": "HTTPS enforcement",
                    "passed": True,  # HTTP not available is good
                    "details": "HTTP not accessible"
                })
        
        # Test 2: Sensitive data in responses
        login_response = self.session.post(
            urljoin(self.base_url, "/api/auth/login"),
            json=self.test_credentials["valid"]
        )
        
        if login_response.status_code == 200:
            response_text = login_response.text.lower()
            
            # Check that passwords and sensitive data are not in response
            sensitive_keywords = ["password", "secret", "key", "private"]
            sensitive_found = any(keyword in response_text for keyword in sensitive_keywords)
            
            tests.append({
                "name": "Sensitive data exposure",
                "passed": not sensitive_found,
                "details": f"Sensitive keywords found: {sensitive_found}"
            })
        
        # Test 3: Error message information disclosure
        # Try to trigger various errors and check if they reveal sensitive info
        error_responses = []
        
        # Database error
        response = self.session.get(urljoin(self.base_url, "/api/trading/nonexistent"))
        error_responses.append(response.text.lower())
        
        # Authentication error
        response = self.session.post(
            urljoin(self.base_url, "/api/auth/login"),
            json={"email": "test", "password": "test"}
        )
        error_responses.append(response.text.lower())
        
        # Check for information disclosure in errors
        disclosure_keywords = ["stack trace", "internal error", "database", "sql", "exception"]
        information_disclosed = any(
            keyword in error_text 
            for error_text in error_responses 
            for keyword in disclosure_keywords
        )
        
        tests.append({
            "name": "Error message information disclosure",
            "passed": not information_disclosed,
            "details": f"Information disclosure found: {information_disclosed}"
        })
        
        return {
            "passed": all(test["passed"] for test in tests),
            "details": tests
        }
    
    def test_session_security(self) -> Dict[str, Any]:
        """Test session management security."""
        tests = []
        
        # Test 1: Session fixation
        # Get initial session
        initial_response = self.session.get(urljoin(self.base_url, "/api/health/"))
        initial_cookies = self.session.cookies.get_dict()
        
        # Login
        login_response = self.session.post(
            urljoin(self.base_url, "/api/auth/login"),
            json=self.test_credentials["valid"]
        )
        
        if login_response.status_code == 200:
            post_login_cookies = self.session.cookies.get_dict()
            
            # Session should change after login
            session_changed = initial_cookies != post_login_cookies
            
            tests.append({
                "name": "Session fixation protection",
                "passed": session_changed,
                "details": f"Session changed after login: {session_changed}"
            })
        
        # Test 2: Concurrent session handling
        # Create second session
        session2 = requests.Session()
        login_response2 = session2.post(
            urljoin(self.base_url, "/api/auth/login"),
            json=self.test_credentials["valid"]
        )
        
        if login_response2.status_code == 200:
            token1 = login_response.json().get("access_token")
            token2 = login_response2.json().get("access_token")
            
            # Both sessions should work (unless explicitly prevented)
            headers1 = {"Authorization": f"Bearer {token1}"}
            headers2 = {"Authorization": f"Bearer {token2}"}
            
            response1 = self.session.get(
                urljoin(self.base_url, "/api/trading/dashboard"),
                headers=headers1
            )
            response2 = session2.get(
                urljoin(self.base_url, "/api/trading/dashboard"),
                headers=headers2
            )
            
            concurrent_allowed = response1.status_code == 200 and response2.status_code == 200
            
            tests.append({
                "name": "Concurrent session handling",
                "passed": True,  # This test is informational
                "details": f"Concurrent sessions allowed: {concurrent_allowed}"
            })
        
        return {
            "passed": all(test["passed"] for test in tests),
            "details": tests
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests."""
        print("🔒 Starting Security Test Suite")
        print("="*50)
        
        # Run all test categories
        test_categories = [
            ("Authentication Security", self.test_authentication_security),
            ("Input Validation", self.test_input_validation),
            ("Authorization Security", self.test_authorization_security),
            ("Rate Limiting", self.test_rate_limiting),
            ("Data Encryption", self.test_data_encryption),
            ("Session Security", self.test_session_security)
        ]
        
        for category_name, test_func in test_categories:
            print(f"\n📋 {category_name}")
            print("-" * 30)
            self.run_test(category_name, test_func)
        
        # Calculate overall results
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result["passed"])
        
        print(f"\n🎯 Security Test Summary")
        print("="*30)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
            "results": self.results
        }
    
    def generate_report(self) -> str:
        """Generate security test report."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"security_test_report_{timestamp}.json"
        
        report_data = {
            "timestamp": timestamp,
            "target": self.base_url,
            "summary": {
                "total_tests": len(self.results),
                "passed_tests": sum(1 for r in self.results if r["passed"]),
                "failed_tests": sum(1 for r in self.results if not r["passed"])
            },
            "results": self.results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n📊 Security report saved: {report_file}")
        return report_file


def main():
    """Main entry point for security testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run security tests")
    parser.add_argument(
        "--host",
        default="http://localhost:8000",
        help="Target host for testing"
    )
    parser.add_argument(
        "--category",
        choices=["auth", "input", "authz", "rate", "encryption", "session", "all"],
        default="all",
        help="Test category to run"
    )
    
    args = parser.parse_args()
    
    tester = SecurityTester(args.host)
    
    if args.category == "all":
        results = tester.run_all_tests()
    else:
        # Run specific category
        category_map = {
            "auth": tester.test_authentication_security,
            "input": tester.test_input_validation,
            "authz": tester.test_authorization_security,
            "rate": tester.test_rate_limiting,
            "encryption": tester.test_data_encryption,
            "session": tester.test_session_security
        }
        
        if args.category in category_map:
            print(f"Running {args.category} security tests...")
            result = tester.run_test(args.category, category_map[args.category])
            results = {"results": [result]}
        else:
            print(f"Unknown category: {args.category}")
            sys.exit(1)
    
    # Generate report
    tester.generate_report()
    
    # Exit with appropriate code
    failed_tests = results.get("summary", {}).get("failed_tests", 0)
    if failed_tests > 0:
        print(f"\n❌ Security tests FAILED - {failed_tests} test(s) failed")
        sys.exit(1)
    else:
        print(f"\n✅ All security tests PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()