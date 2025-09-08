"""Load testing configuration using Locust."""

import json
import random
from locust import HttpUser, task, between
from locust.exception import StopUser


class TradingBotUser(HttpUser):
    """Simulates a trading bot user for load testing."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize user session."""
        self.token = None
        self.user_id = None
        self.login()
    
    def login(self):
        """Authenticate user."""
        login_data = {
            "email": f"loadtest_user_{random.randint(1, 1000)}@example.com",
            "password": "LoadTestPassword123!"
        }
        
        with self.client.post(
            "/api/auth/login",
            json=login_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                response.success()
            else:
                response.failure(f"Login failed: {response.text}")
                raise StopUser()
    
    @task(3)
    def get_dashboard_data(self):
        """Load dashboard data - most common operation."""
        with self.client.get(
            "/api/trading/dashboard",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "portfolio_stats" in data:
                    response.success()
                else:
                    response.failure("Invalid dashboard data")
            else:
                response.failure(f"Dashboard request failed: {response.status_code}")
    
    @task(2)
    def get_positions(self):
        """Get current positions."""
        with self.client.get(
            "/api/trading/positions",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Positions request failed: {response.status_code}")
    
    @task(2)
    def get_trades(self):
        """Get recent trades."""
        with self.client.get(
            "/api/trading/trades?limit=20",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Trades request failed: {response.status_code}")
    
    @task(1)
    def get_market_data(self):
        """Get market data for symbols."""
        symbols = ["BTC-USD", "ETH-USD", "SOL-USD"]
        symbol = random.choice(symbols)
        
        with self.client.get(
            f"/api/market/data/{symbol}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Market data request failed: {response.status_code}")
    
    @task(1)
    def place_test_order(self):
        """Place a test order (paper trading)."""
        order_data = {
            "symbol": random.choice(["BTC-USD", "ETH-USD"]),
            "side": random.choice(["BUY", "SELL"]),
            "order_type": "MARKET",
            "size": round(random.uniform(0.001, 0.01), 3),
            "paper_trade": True
        }
        
        with self.client.post(
            "/api/trading/place-order",
            json=order_data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 400:
                # Risk management rejection is expected
                response.success()
            else:
                response.failure(f"Order placement failed: {response.status_code}")
    
    @task(1)
    def get_strategy_config(self):
        """Get strategy configuration."""
        with self.client.get(
            "/api/trading/strategy/config",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Strategy config request failed: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Check system health."""
        with self.client.get(
            "/api/health/",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"System unhealthy: {data.get('status')}")
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    def on_stop(self):
        """Cleanup on user stop."""
        if self.token:
            # Logout if needed
            self.client.post("/api/auth/logout")


class HighVolumeUser(HttpUser):
    """High-frequency user for stress testing."""
    
    wait_time = between(0.1, 0.5)  # Very frequent requests
    weight = 1  # Lower weight - fewer of these users
    
    def on_start(self):
        """Initialize high-volume user."""
        self.token = None
        self.login()
    
    def login(self):
        """Quick login for high-volume user."""
        login_data = {
            "email": f"highvolume_user_{random.randint(1, 100)}@example.com",
            "password": "HighVolumePassword123!"
        }
        
        response = self.client.post("/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            raise StopUser()
    
    @task(5)
    def rapid_dashboard_requests(self):
        """Rapid dashboard requests to test caching."""
        self.client.get("/api/trading/dashboard")
    
    @task(3)
    def rapid_market_data_requests(self):
        """Rapid market data requests."""
        symbol = random.choice(["BTC-USD", "ETH-USD", "SOL-USD"])
        self.client.get(f"/api/market/data/{symbol}")
    
    @task(2)
    def rapid_position_checks(self):
        """Rapid position checking."""
        self.client.get("/api/trading/positions")


class WebSocketUser(HttpUser):
    """User testing WebSocket connections."""
    
    wait_time = between(2, 5)
    weight = 2  # Moderate number of WebSocket users
    
    def on_start(self):
        """Initialize WebSocket user."""
        self.token = None
        self.ws = None
        self.login()
        # Note: Real WebSocket testing would require additional setup
        # This is a placeholder for WebSocket load testing
    
    def login(self):
        """Login for WebSocket user."""
        login_data = {
            "email": f"websocket_user_{random.randint(1, 500)}@example.com",
            "password": "WebSocketPassword123!"
        }
        
        response = self.client.post("/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            raise StopUser()
    
    @task(1)
    def simulate_websocket_activity(self):
        """Simulate WebSocket connection activity."""
        # In a real implementation, this would establish WebSocket connections
        # and test real-time updates. For now, we'll simulate with HTTP requests
        
        # Simulate subscription to real-time updates
        self.client.get("/api/trading/positions")
        self.client.get("/api/trading/dashboard")
        
        # Small delay to simulate real-time data processing
        import time
        time.sleep(0.1)


# Custom load test scenarios
class StressTestUser(TradingBotUser):
    """User for stress testing scenarios."""
    
    wait_time = between(0.5, 1.0)  # Faster requests
    weight = 1  # Fewer stress test users
    
    @task(5)
    def heavy_dashboard_load(self):
        """Heavy dashboard loading."""
        # Simulate complex dashboard queries
        self.client.get("/api/trading/dashboard")
        self.client.get("/api/trading/positions")  
        self.client.get("/api/trading/trades?limit=100")
        self.client.get("/api/trading/strategy/performance")
    
    @task(2)
    def complex_order_scenarios(self):
        """Complex order placement scenarios."""
        # Multiple rapid order attempts (should be rate limited)
        for _ in range(3):
            order_data = {
                "symbol": "BTC-USD",
                "side": "BUY",
                "order_type": "MARKET",
                "size": 0.001,
                "paper_trade": True
            }
            self.client.post("/api/trading/place-order", json=order_data)


# Load test configuration
class LoadTestConfig:
    """Load test configuration and scenarios."""
    
    SCENARIOS = {
        "normal_load": {
            "description": "Normal user load simulation",
            "users": 50,
            "spawn_rate": 5,
            "run_time": "5m",
            "user_classes": [TradingBotUser]
        },
        "high_load": {
            "description": "High load simulation",
            "users": 200,
            "spawn_rate": 10,
            "run_time": "10m",
            "user_classes": [TradingBotUser, HighVolumeUser]
        },
        "stress_test": {
            "description": "Stress testing",
            "users": 500,
            "spawn_rate": 20,
            "run_time": "15m",
            "user_classes": [TradingBotUser, HighVolumeUser, StressTestUser]
        },
        "websocket_test": {
            "description": "WebSocket load testing",
            "users": 100,
            "spawn_rate": 10,
            "run_time": "10m",
            "user_classes": [WebSocketUser]
        },
        "endurance_test": {
            "description": "Endurance testing",
            "users": 100,
            "spawn_rate": 5,
            "run_time": "60m",
            "user_classes": [TradingBotUser]
        }
    }


if __name__ == "__main__":
    # This allows running specific scenarios
    import sys
    import subprocess
    
    scenario = sys.argv[1] if len(sys.argv) > 1 else "normal_load"
    
    if scenario in LoadTestConfig.SCENARIOS:
        config = LoadTestConfig.SCENARIOS[scenario]
        
        cmd = [
            "locust",
            "-f", __file__,
            "--host", "http://localhost:8000",
            "--users", str(config["users"]),
            "--spawn-rate", str(config["spawn_rate"]),
            "--run-time", config["run_time"],
            "--headless",
            "--html", f"load_test_report_{scenario}.html"
        ]
        
        print(f"Running load test scenario: {config['description']}")
        subprocess.run(cmd)
    else:
        print(f"Unknown scenario: {scenario}")
        print(f"Available scenarios: {list(LoadTestConfig.SCENARIOS.keys())}")