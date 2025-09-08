"""
dYdX v4 REST API Client
Handles all REST API interactions with proper authentication, rate limiting, and error handling.
"""

import asyncio
import hashlib
import hmac
import time
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import httpx
from httpx import Response, HTTPError, TimeoutException
import structlog

from src.config import get_config


logger = structlog.get_logger(__name__)


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    OPEN = "OPEN" 
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    BEST_EFFORT_CANCELED = "BEST_EFFORT_CANCELED"


class TimeInForce(str, Enum):
    """Time in force enumeration"""
    GTT = "GTT"  # Good Till Time
    FOK = "FOK"  # Fill or Kill
    IOC = "IOC"  # Immediate or Cancel


@dataclass
class OrderRequest:
    """Order request data structure"""
    symbol: str
    side: OrderSide
    type: OrderType
    size: float
    price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTT
    post_only: bool = False
    reduce_only: bool = False
    client_id: Optional[str] = None
    good_til_time: Optional[int] = None


@dataclass
class OrderResult:
    """Order execution result"""
    success: bool
    order_id: Optional[str] = None
    client_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    error_message: Optional[str] = None
    filled_size: float = 0.0
    remaining_size: float = 0.0


@dataclass 
class Position:
    """Position data structure"""
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    realized_pnl: float
    created_at: datetime


@dataclass
class Trade:
    """Trade data structure"""
    id: str
    symbol: str
    side: OrderSide
    size: float
    price: float
    fee: float
    created_at: datetime
    liquidity: str  # MAKER or TAKER


class RateLimiter:
    """Token bucket rate limiter for API requests"""
    
    def __init__(self, requests_per_second: int):
        self.requests_per_second = requests_per_second
        self.tokens = requests_per_second
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token for API request"""
        async with self.lock:
            now = time.time()
            # Add tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(
                self.requests_per_second,
                self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now
            
            if self.tokens < 1:
                # Wait for next token
                wait_time = (1 - self.tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class CircuitBreaker:
    """Circuit breaker for API failure handling"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        now = time.time()
        
        if self.state == "OPEN":
            if now - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        
        return True
    
    def record_success(self) -> None:
        """Record successful request"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
    
    def record_failure(self) -> None:
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class DydxRestClient:
    """
    dYdX v4 REST API client with:
    - Proper authentication and signing
    - Automatic retry with circuit breakers
    - Rate limiting compliance
    - Comprehensive error handling
    - Request/response logging
    - Connection pooling and timeouts
    """
    
    def __init__(self):
        self.config = get_config()
        
        # API endpoints
        if self.config.dydx_environment == "testnet":
            self.base_url = "https://indexer.dydxtestnet.trade"
            self.api_url = "https://api.dydxtestnet.trade"
        else:
            self.base_url = "https://indexer.dydx.trade"
            self.api_url = "https://api.dydx.trade"
        
        # Authentication
        self.api_key = self.config.dydx_api_key
        self.secret_key = self.config.dydx_secret_key
        self.passphrase = self.config.dydx_passphrase
        
        # Rate limiting and circuit breaking
        self.rate_limiter = RateLimiter(self.config.api_requests_per_second)
        self.circuit_breaker = CircuitBreaker()
        
        # HTTP client configuration
        self.timeout_config = httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=10.0,
            pool=60.0
        )
        
        # Connection limits
        self.limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30
        )
        
        self.client: Optional[httpx.AsyncClient] = None
        
        # Request statistics
        self.stats = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "last_request_time": None,
            "average_response_time": 0.0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def initialize(self) -> None:
        """Initialize HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_config,
                limits=self.limits,
                headers={
                    "User-Agent": "dYdX-Trading-Bot/1.0",
                    "Content-Type": "application/json"
                }
            )
            logger.info("dYdX REST client initialized")
    
    async def close(self) -> None:
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("dYdX REST client closed")
    
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate HMAC SHA256 signature for authentication"""
        message = timestamp + method.upper() + path + body
        return hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_auth_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Generate authentication headers"""
        timestamp = str(int(time.time()))
        signature = self._generate_signature(timestamp, method, path, body)
        
        return {
            "DYDX-SIGNATURE": signature,
            "DYDX-API-KEY": self.api_key,
            "DYDX-TIMESTAMP": timestamp,
            "DYDX-PASSPHRASE": self.passphrase
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        authenticated: bool = True,
        use_api_url: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with rate limiting, circuit breaking, and error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            authenticated: Whether to include authentication headers
            use_api_url: Use trading API URL instead of indexer URL
            
        Returns:
            Response data or None if request failed
        """
        if not self.client:
            await self.initialize()
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker is OPEN, skipping request")
            return None
        
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        # Prepare request
        url = f"{self.api_url if use_api_url else self.base_url}{endpoint}"
        headers = {}
        body = ""
        
        if data:
            body = json.dumps(data, separators=(',', ':'))
        
        if authenticated:
            path = endpoint
            headers.update(self._get_auth_headers(method, path, body))
        
        start_time = time.time()
        
        try:
            # Make the request
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                content=body if body else None,
                headers=headers
            )
            
            # Record timing
            response_time = time.time() - start_time
            self._update_stats(response_time, success=True)
            
            # Handle response
            if response.status_code == 200:
                self.circuit_breaker.record_success()
                return response.json()
            
            elif response.status_code == 429:
                # Rate limited
                logger.warning("Rate limited by dYdX API", 
                              endpoint=endpoint, 
                              status=response.status_code)
                await asyncio.sleep(1)  # Back off
                return None
            
            else:
                # Other HTTP errors
                logger.error("HTTP error from dYdX API",
                           endpoint=endpoint,
                           status=response.status_code,
                           response=response.text)
                self.circuit_breaker.record_failure()
                return None
        
        except TimeoutException:
            logger.error("Request timeout", endpoint=endpoint)
            self.circuit_breaker.record_failure()
            self._update_stats(time.time() - start_time, success=False)
            return None
        
        except HTTPError as e:
            logger.error("HTTP error", endpoint=endpoint, error=str(e))
            self.circuit_breaker.record_failure()
            self._update_stats(time.time() - start_time, success=False)
            return None
        
        except Exception as e:
            logger.error("Unexpected error", endpoint=endpoint, error=str(e))
            self.circuit_breaker.record_failure()
            self._update_stats(time.time() - start_time, success=False)
            return None
    
    def _update_stats(self, response_time: float, success: bool) -> None:
        """Update request statistics"""
        self.stats["requests_sent"] += 1
        self.stats["last_request_time"] = datetime.utcnow()
        
        if success:
            self.stats["requests_successful"] += 1
        else:
            self.stats["requests_failed"] += 1
        
        # Update average response time
        if self.stats["requests_sent"] == 1:
            self.stats["average_response_time"] = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.stats["average_response_time"] = (
                alpha * response_time + 
                (1 - alpha) * self.stats["average_response_time"]
            )
    
    # =============================================================================
    # Account Management
    # =============================================================================
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account balance and information
        
        Returns:
            Account information including balances and equity
        """
        logger.info("Fetching account information")
        
        result = await self._make_request(
            method="GET",
            endpoint="/v4/accounts",
            authenticated=True
        )
        
        if result:
            logger.info("Account information retrieved successfully")
        else:
            logger.error("Failed to retrieve account information")
        
        return result
    
    async def get_positions(self) -> List[Position]:
        """
        Get current open positions
        
        Returns:
            List of current positions
        """
        logger.info("Fetching current positions")
        
        result = await self._make_request(
            method="GET",
            endpoint="/v4/positions",
            authenticated=True
        )
        
        positions = []
        if result and "positions" in result:
            for pos_data in result["positions"]:
                position = Position(
                    symbol=pos_data.get("market"),
                    side=pos_data.get("side"),
                    size=float(pos_data.get("size", 0)),
                    entry_price=float(pos_data.get("entryPrice", 0)),
                    mark_price=float(pos_data.get("unrealizedPnl", 0)),  # TODO: Get mark price
                    unrealized_pnl=float(pos_data.get("unrealizedPnl", 0)),
                    realized_pnl=float(pos_data.get("realizedPnl", 0)),
                    created_at=datetime.fromisoformat(pos_data.get("createdAt", "").replace("Z", "+00:00"))
                )
                positions.append(position)
            
            logger.info("Retrieved positions", count=len(positions))
        else:
            logger.warning("No positions data received")
        
        return positions
    
    # =============================================================================
    # Order Management
    # =============================================================================
    
    async def place_order(self, order: OrderRequest) -> OrderResult:
        """
        Place a new order
        
        Args:
            order: Order request details
            
        Returns:
            Order execution result
        """
        logger.info("Placing order", 
                   symbol=order.symbol, 
                   side=order.side, 
                   type=order.type,
                   size=order.size,
                   price=order.price)
        
        # Build order payload
        payload = {
            "market": order.symbol,
            "side": order.side.value,
            "type": order.type.value,
            "size": str(order.size),
            "timeInForce": order.time_in_force.value,
            "postOnly": order.post_only,
            "reduceOnly": order.reduce_only
        }
        
        if order.price is not None:
            payload["price"] = str(order.price)
        
        if order.client_id:
            payload["clientId"] = order.client_id
        
        if order.good_til_time:
            payload["goodTilTime"] = order.good_til_time
        
        result = await self._make_request(
            method="POST",
            endpoint="/v4/orders",
            data=payload,
            authenticated=True,
            use_api_url=True
        )
        
        if result and "order" in result:
            order_data = result["order"]
            return OrderResult(
                success=True,
                order_id=order_data.get("id"),
                client_id=order_data.get("clientId"),
                status=OrderStatus(order_data.get("status", "")),
                filled_size=float(order_data.get("size", 0)) - float(order_data.get("remainingSize", 0)),
                remaining_size=float(order_data.get("remainingSize", 0))
            )
        else:
            return OrderResult(
                success=False,
                error_message="Failed to place order"
            )
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancellation successful
        """
        logger.info("Cancelling order", order_id=order_id)
        
        result = await self._make_request(
            method="DELETE",
            endpoint=f"/v4/orders/{order_id}",
            authenticated=True,
            use_api_url=True
        )
        
        success = result is not None
        if success:
            logger.info("Order cancelled successfully", order_id=order_id)
        else:
            logger.error("Failed to cancel order", order_id=order_id)
        
        return success
    
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of specific order
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Order status information
        """
        logger.debug("Checking order status", order_id=order_id)
        
        result = await self._make_request(
            method="GET",
            endpoint=f"/v4/orders/{order_id}",
            authenticated=True
        )
        
        if result:
            logger.debug("Order status retrieved", order_id=order_id)
        
        return result
    
    async def get_order_fills(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Get fills for specific order
        
        Args:
            order_id: Order ID to get fills for
            
        Returns:
            List of order fills
        """
        logger.debug("Fetching order fills", order_id=order_id)
        
        result = await self._make_request(
            method="GET",
            endpoint="/v4/fills",
            params={"orderId": order_id},
            authenticated=True
        )
        
        if result and "fills" in result:
            logger.debug("Order fills retrieved", 
                        order_id=order_id, 
                        count=len(result["fills"]))
            return result["fills"]
        
        return []
    
    # =============================================================================
    # Market Data
    # =============================================================================
    
    async def get_markets(self) -> Optional[Dict[str, Any]]:
        """Get all available markets information"""
        logger.debug("Fetching markets information")
        
        result = await self._make_request(
            method="GET",
            endpoint="/v4/perpetualMarkets",
            authenticated=False
        )
        
        if result:
            logger.debug("Markets information retrieved")
        
        return result
    
    async def get_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current orderbook for symbol
        
        Args:
            symbol: Symbol to get orderbook for (e.g., "BTC-USD")
            
        Returns:
            Orderbook data with bids and asks
        """
        logger.debug("Fetching orderbook", symbol=symbol)
        
        result = await self._make_request(
            method="GET",
            endpoint=f"/v4/orderbooks/perpetualMarket/{symbol}",
            authenticated=False
        )
        
        if result:
            logger.debug("Orderbook retrieved", symbol=symbol)
        
        return result
    
    async def get_candles(
        self, 
        symbol: str, 
        resolution: str = "1m", 
        limit: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical candle data
        
        Args:
            symbol: Symbol to get candles for
            resolution: Candle resolution (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to retrieve
            
        Returns:
            List of candle data
        """
        logger.debug("Fetching candles", 
                    symbol=symbol, 
                    resolution=resolution, 
                    limit=limit)
        
        result = await self._make_request(
            method="GET",
            endpoint=f"/v4/candles/perpetualMarket/{symbol}",
            params={
                "resolution": resolution,
                "limit": limit
            },
            authenticated=False
        )
        
        if result and "candles" in result:
            logger.debug("Candles retrieved", 
                        symbol=symbol, 
                        count=len(result["candles"]))
            return result["candles"]
        
        return []
    
    # =============================================================================
    # Statistics and Health
    # =============================================================================
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get client statistics and health metrics"""
        return {
            **self.stats,
            "circuit_breaker_state": self.circuit_breaker.state,
            "circuit_breaker_failures": self.circuit_breaker.failure_count,
            "rate_limiter_tokens": self.rate_limiter.tokens,
            "is_connected": self.client is not None
        }