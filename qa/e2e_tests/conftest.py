"""Playwright configuration for E2E tests."""

import pytest
import asyncio
from playwright.async_api import async_playwright
from typing import AsyncGenerator
import os


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def browser():
    """Launch browser for the test session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        yield browser
        await browser.close()


@pytest.fixture(scope="session")
async def context(browser):
    """Create browser context for the test session."""
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
        permissions=["notifications"]
    )
    yield context
    await context.close()


@pytest.fixture
async def page(context):
    """Create a new page for each test."""
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture
def base_url():
    """Base URL for the application."""
    return os.getenv("BASE_URL", "http://localhost:3000")


@pytest.fixture
def api_base_url():
    """Base URL for the API."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
async def authenticated_page(page, base_url):
    """Create an authenticated page session."""
    # Navigate to login page
    await page.goto(f"{base_url}/login")
    
    # Fill in login credentials
    await page.fill('[data-testid="email-input"]', "test@example.com")
    await page.fill('[data-testid="password-input"]', "TestPassword123!")
    
    # Click login button
    await page.click('[data-testid="login-button"]')
    
    # Wait for navigation to dashboard
    await page.wait_for_url(f"{base_url}/dashboard", timeout=10000)
    
    return page


@pytest.fixture
def test_user_credentials():
    """Test user credentials for authentication."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "username": "testuser"
    }


@pytest.fixture
def mock_api_responses():
    """Mock API responses for E2E tests."""
    return {
        "user_profile": {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "is_active": True,
            "trading_enabled": True,
            "paper_trading_mode": True,
            "account_balance": 10000.00
        },
        "dashboard_data": {
            "portfolio_stats": {
                "account_balance": 10000.00,
                "total_pnl": 150.50,
                "total_pnl_percent": 1.51,
                "open_positions_count": 2,
                "total_trades": 45,
                "win_rate": 68.9
            },
            "open_positions": [
                {
                    "id": 1,
                    "symbol": "BTC-USD",
                    "side": "LONG",
                    "size": 0.001,
                    "entry_price": 45000.00,
                    "mark_price": 46000.00,
                    "unrealized_pnl": 1.00,
                    "unrealized_pnl_percent": 2.22
                }
            ],
            "recent_trades": [
                {
                    "id": 1,
                    "order_id": "test_order_123",
                    "symbol": "BTC-USD",
                    "side": "BUY",
                    "size": 0.001,
                    "price": 45000.00,
                    "status": "FILLED",
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            ]
        }
    }


@pytest.fixture
async def mock_websocket_server(unused_tcp_port):
    """Start mock WebSocket server for testing real-time updates."""
    import websockets
    import json
    
    connected_clients = set()
    
    async def handler(websocket, path):
        connected_clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            connected_clients.discard(websocket)
    
    async def broadcast_update():
        """Broadcast test updates to connected clients."""
        if connected_clients:
            message = json.dumps({
                "type": "position_update",
                "data": {
                    "symbol": "BTC-USD",
                    "unrealized_pnl": 2.50,
                    "unrealized_pnl_percent": 5.56
                }
            })
            await asyncio.gather(
                *[client.send(message) for client in connected_clients],
                return_exceptions=True
            )
    
    server = await websockets.serve(handler, "localhost", unused_tcp_port)
    
    # Start broadcasting test updates
    broadcast_task = asyncio.create_task(
        asyncio.sleep(1) and broadcast_update()
    )
    
    yield f"ws://localhost:{unused_tcp_port}"
    
    broadcast_task.cancel()
    server.close()
    await server.wait_closed()


@pytest.fixture
def trading_test_data():
    """Test data for trading scenarios."""
    return {
        "symbols": ["BTC-USD", "ETH-USD", "SOL-USD"],
        "order_types": ["MARKET", "LIMIT"],
        "sides": ["BUY", "SELL"],
        "test_orders": [
            {
                "symbol": "BTC-USD",
                "side": "BUY",
                "order_type": "MARKET",
                "size": 0.001,
                "expected_outcome": "success"
            },
            {
                "symbol": "ETH-USD",
                "side": "SELL",
                "order_type": "LIMIT",
                "size": 0.01,
                "price": 3000.00,
                "expected_outcome": "pending"
            }
        ]
    }


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for E2E tests."""
    return {
        "page_load_time": 3000,  # 3 seconds
        "api_response_time": 1000,  # 1 second
        "websocket_connection_time": 2000,  # 2 seconds
        "chart_render_time": 2000,  # 2 seconds
        "navigation_time": 1000  # 1 second
    }


@pytest.fixture(autouse=True)
async def setup_test_environment(page):
    """Set up test environment for each test."""
    # Set up console log capture
    page.on("console", lambda msg: print(f"Console [{msg.type}]: {msg.text}"))
    
    # Set up error handling
    page.on("pageerror", lambda error: print(f"Page Error: {error}"))
    
    # Set up request/response logging for debugging
    page.on("request", lambda request: print(f"Request: {request.method} {request.url}"))
    page.on("response", lambda response: print(f"Response: {response.status} {response.url}"))


@pytest.fixture
def screenshot_on_failure(request, page):
    """Take screenshot on test failure."""
    yield
    if request.node.rep_call.failed:
        screenshot_dir = "qa/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        
        test_name = request.node.name
        screenshot_path = f"{screenshot_dir}/{test_name}_failure.png"
        
        asyncio.create_task(page.screenshot(path=screenshot_path))
        print(f"Screenshot saved: {screenshot_path}")


# Pytest hooks for better reporting
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results for screenshot handling."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
    return rep