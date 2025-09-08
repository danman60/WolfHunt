"""
dYdX v4 WebSocket Manager
Handles real-time market data feeds with automatic reconnection and robust error handling.
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
import structlog

from src.config import get_config


logger = structlog.get_logger(__name__)


class SubscriptionType(str, Enum):
    """WebSocket subscription types"""
    ORDERBOOK = "v4_orderbook"
    TRADES = "v4_trades"
    CANDLES = "v4_candles"
    MARKETS = "v4_markets"


@dataclass
class WebSocketSubscription:
    """WebSocket subscription configuration"""
    channel: SubscriptionType
    id: str
    symbol: Optional[str] = None
    resolution: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None


class ConnectionState(str, Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class DydxWebSocketManager:
    """
    dYdX v4 WebSocket manager with:
    - Automatic reconnection with exponential backoff
    - Subscription management for multiple data types
    - Real-time data processing and distribution
    - Connection health monitoring
    - Rate limiting compliance
    - Comprehensive error handling
    """
    
    def __init__(self):
        self.config = get_config()
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connection_state = ConnectionState.DISCONNECTED
        
        # Connection settings
        if self.config.dydx_environment == "testnet":
            self.ws_url = "wss://indexer.dydxtestnet.trade/v4/ws"
        else:
            self.ws_url = "wss://indexer.dydx.trade/v4/ws"
        
        # Reconnection settings
        self.reconnect_delay = self.config.websocket_reconnect_delay
        self.max_reconnect_attempts = self.config.websocket_max_reconnect_attempts
        self.current_reconnect_attempt = 0
        self.last_ping_time = 0
        self.ping_interval = 30  # seconds
        
        # Subscription management
        self.subscriptions: Dict[str, WebSocketSubscription] = {}
        self.active_subscriptions: Set[str] = set()
        self.message_handlers: Dict[SubscriptionType, List[Callable]] = {
            subscription_type: [] for subscription_type in SubscriptionType
        }
        
        # Message processing
        self.message_queue = asyncio.Queue(maxsize=1000)
        self.stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "connection_count": 0,
            "last_message_time": None,
            "errors": 0
        }
        
        # Tasks
        self._connection_task: Optional[asyncio.Task] = None
        self._message_processor_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        self._shutdown_event = asyncio.Event()
        
    async def connect(self) -> bool:
        """
        Establish WebSocket connection to dYdX v4
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.connection_state == ConnectionState.CONNECTED:
            logger.info("WebSocket already connected")
            return True
        
        self.connection_state = ConnectionState.CONNECTING
        logger.info("Connecting to dYdX WebSocket", url=self.ws_url)
        
        try:
            # Connect with timeout and custom headers
            self.websocket = await websockets.connect(
                self.ws_url,
                timeout=10,
                ping_interval=20,
                ping_timeout=10,
                extra_headers={
                    "User-Agent": "dYdX-Trading-Bot/1.0"
                }
            )
            
            self.connection_state = ConnectionState.CONNECTED
            self.current_reconnect_attempt = 0
            self.stats["connection_count"] += 1
            self.last_ping_time = time.time()
            
            logger.info("WebSocket connection established successfully")
            
            # Start background tasks
            self._start_background_tasks()
            
            # Re-subscribe to previous subscriptions if any
            await self._resubscribe_all()
            
            return True
            
        except Exception as e:
            self.connection_state = ConnectionState.FAILED
            self.stats["errors"] += 1
            logger.error("Failed to connect to WebSocket", error=str(e))
            return False
    
    async def disconnect(self) -> None:
        """Gracefully disconnect from WebSocket"""
        logger.info("Disconnecting from WebSocket")
        
        self._shutdown_event.set()
        self.connection_state = ConnectionState.DISCONNECTED
        
        # Cancel background tasks
        await self._cancel_background_tasks()
        
        # Close WebSocket connection
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning("Error closing WebSocket", error=str(e))
            finally:
                self.websocket = None
        
        logger.info("WebSocket disconnected successfully")
    
    async def subscribe_orderbook(self, symbols: List[str]) -> bool:
        """
        Subscribe to real-time orderbook data
        
        Args:
            symbols: List of symbols to subscribe to (e.g., ["BTC-USD", "ETH-USD"])
            
        Returns:
            bool: True if subscription successful
        """
        success = True
        
        for symbol in symbols:
            subscription = WebSocketSubscription(
                channel=SubscriptionType.ORDERBOOK,
                id=f"orderbook_{symbol}",
                symbol=symbol,
                params={"batched": True}
            )
            
            if await self._subscribe(subscription):
                logger.info("Subscribed to orderbook", symbol=symbol)
            else:
                logger.error("Failed to subscribe to orderbook", symbol=symbol)
                success = False
        
        return success
    
    async def subscribe_trades(self, symbols: List[str]) -> bool:
        """
        Subscribe to real-time trade data
        
        Args:
            symbols: List of symbols to subscribe to
            
        Returns:
            bool: True if subscription successful
        """
        success = True
        
        for symbol in symbols:
            subscription = WebSocketSubscription(
                channel=SubscriptionType.TRADES,
                id=f"trades_{symbol}",
                symbol=symbol
            )
            
            if await self._subscribe(subscription):
                logger.info("Subscribed to trades", symbol=symbol)
            else:
                logger.error("Failed to subscribe to trades", symbol=symbol)
                success = False
        
        return success
    
    async def subscribe_candles(self, symbols: List[str], resolution: str = "1m") -> bool:
        """
        Subscribe to real-time candlestick data
        
        Args:
            symbols: List of symbols to subscribe to
            resolution: Candle resolution (1m, 5m, 15m, 1h, 4h, 1d)
            
        Returns:
            bool: True if subscription successful
        """
        if resolution not in self.config.candle_timeframes:
            logger.error("Invalid candle resolution", resolution=resolution)
            return False
        
        success = True
        
        for symbol in symbols:
            subscription = WebSocketSubscription(
                channel=SubscriptionType.CANDLES,
                id=f"candles_{symbol}_{resolution}",
                symbol=symbol,
                resolution=resolution
            )
            
            if await self._subscribe(subscription):
                logger.info("Subscribed to candles", symbol=symbol, resolution=resolution)
            else:
                logger.error("Failed to subscribe to candles", symbol=symbol)
                success = False
        
        return success
    
    def add_message_handler(self, subscription_type: SubscriptionType, handler: Callable) -> None:
        """
        Add message handler for specific subscription type
        
        Args:
            subscription_type: Type of subscription to handle
            handler: Async function to handle messages
        """
        self.message_handlers[subscription_type].append(handler)
        logger.info("Added message handler", subscription_type=subscription_type)
    
    async def _subscribe(self, subscription: WebSocketSubscription) -> bool:
        """Send subscription request to WebSocket"""
        if self.connection_state != ConnectionState.CONNECTED:
            logger.warning("Cannot subscribe: WebSocket not connected")
            return False
        
        # Build subscription message based on channel type
        message = {
            "type": "subscribe",
            "channel": subscription.channel.value,
            "id": subscription.id,
        }
        
        if subscription.symbol:
            message["id"] = subscription.symbol
        
        if subscription.resolution:
            message["resolution"] = subscription.resolution
        
        # Add any additional parameters
        message.update(subscription.params)
        
        try:
            await self.websocket.send(json.dumps(message))
            self.subscriptions[subscription.id] = subscription
            self.active_subscriptions.add(subscription.id)
            return True
            
        except Exception as e:
            logger.error("Failed to send subscription", error=str(e))
            return False
    
    async def _resubscribe_all(self) -> None:
        """Re-subscribe to all active subscriptions after reconnection"""
        if not self.subscriptions:
            return
        
        logger.info("Re-subscribing to active subscriptions", 
                   count=len(self.subscriptions))
        
        for subscription in self.subscriptions.values():
            await self._subscribe(subscription)
    
    def _start_background_tasks(self) -> None:
        """Start background tasks for message processing and health monitoring"""
        self._message_processor_task = asyncio.create_task(
            self._message_processor_loop()
        )
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop()
        )
        
        # Start connection monitoring task
        self._connection_task = asyncio.create_task(
            self._connection_monitor_loop()
        )
    
    async def _cancel_background_tasks(self) -> None:
        """Cancel all background tasks"""
        tasks = [
            self._message_processor_task,
            self._heartbeat_task,
            self._connection_task
        ]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def _connection_monitor_loop(self) -> None:
        """Monitor connection and handle incoming messages"""
        while not self._shutdown_event.is_set():
            try:
                if self.websocket and self.connection_state == ConnectionState.CONNECTED:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(
                            self.websocket.recv(), 
                            timeout=1.0
                        )
                        
                        self.stats["messages_received"] += 1
                        self.stats["last_message_time"] = datetime.utcnow()
                        
                        # Add to processing queue
                        try:
                            self.message_queue.put_nowait(message)
                        except asyncio.QueueFull:
                            logger.warning("Message queue full, dropping message")
                            
                    except asyncio.TimeoutError:
                        # No message received, continue monitoring
                        continue
                        
                    except ConnectionClosed:
                        logger.warning("WebSocket connection closed")
                        await self._handle_disconnection()
                        
                    except WebSocketException as e:
                        logger.error("WebSocket error", error=str(e))
                        await self._handle_disconnection()
                        
                else:
                    # Not connected, wait and try to reconnect
                    await asyncio.sleep(1)
                    if self.connection_state == ConnectionState.DISCONNECTED:
                        await self._attempt_reconnection()
                        
            except Exception as e:
                logger.error("Error in connection monitor", error=str(e))
                self.stats["errors"] += 1
                await asyncio.sleep(1)
    
    async def _message_processor_loop(self) -> None:
        """Process incoming messages from the queue"""
        while not self._shutdown_event.is_set():
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                
                await self._process_message(message)
                self.stats["messages_processed"] += 1
                
            except asyncio.TimeoutError:
                # No message in queue, continue
                continue
            except Exception as e:
                logger.error("Error processing message", error=str(e))
                self.stats["errors"] += 1
    
    async def _process_message(self, raw_message: str) -> None:
        """Process individual WebSocket message"""
        try:
            message = json.loads(raw_message)
            
            # Handle different message types
            if message.get("type") == "connected":
                logger.info("WebSocket connection confirmed")
                return
            
            if message.get("type") == "subscribed":
                channel_id = message.get("id", "")
                logger.info("Subscription confirmed", channel_id=channel_id)
                return
            
            if message.get("type") == "unsubscribed":
                channel_id = message.get("id", "")
                logger.info("Unsubscription confirmed", channel_id=channel_id)
                if channel_id in self.active_subscriptions:
                    self.active_subscriptions.remove(channel_id)
                return
            
            if message.get("type") == "channel_data":
                await self._handle_channel_data(message)
                return
            
            # Handle error messages
            if message.get("type") == "error":
                logger.error("WebSocket error message", error=message)
                return
            
            logger.debug("Unhandled message type", message_type=message.get("type"))
            
        except json.JSONDecodeError as e:
            logger.error("Failed to decode WebSocket message", error=str(e))
        except Exception as e:
            logger.error("Error processing WebSocket message", error=str(e))
    
    async def _handle_channel_data(self, message: Dict[str, Any]) -> None:
        """Handle channel data messages and route to appropriate handlers"""
        channel = message.get("channel")
        
        if not channel:
            logger.warning("Received channel data without channel identifier")
            return
        
        # Determine subscription type from channel
        subscription_type = None
        for sub_type in SubscriptionType:
            if channel.startswith(sub_type.value):
                subscription_type = sub_type
                break
        
        if not subscription_type:
            logger.warning("Unknown channel type", channel=channel)
            return
        
        # Route to registered handlers
        handlers = self.message_handlers.get(subscription_type, [])
        if handlers:
            # Execute all handlers concurrently
            await asyncio.gather(
                *[handler(message) for handler in handlers],
                return_exceptions=True
            )
        else:
            logger.debug("No handlers registered for channel", 
                        subscription_type=subscription_type)
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat/ping messages"""
        while not self._shutdown_event.is_set():
            try:
                if (self.connection_state == ConnectionState.CONNECTED and 
                    self.websocket and 
                    time.time() - self.last_ping_time > self.ping_interval):
                    
                    # Send ping
                    ping_message = {
                        "type": "ping",
                        "timestamp": int(time.time() * 1000)
                    }
                    
                    await self.websocket.send(json.dumps(ping_message))
                    self.last_ping_time = time.time()
                    
                    logger.debug("Sent WebSocket ping")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error("Error in heartbeat loop", error=str(e))
                await asyncio.sleep(10)
    
    async def _handle_disconnection(self) -> None:
        """Handle WebSocket disconnection"""
        if self.connection_state != ConnectionState.DISCONNECTED:
            logger.warning("WebSocket disconnected unexpectedly")
            self.connection_state = ConnectionState.DISCONNECTED
            self.websocket = None
            
            # Start reconnection process
            await self._attempt_reconnection()
    
    async def _attempt_reconnection(self) -> None:
        """Attempt to reconnect with exponential backoff"""
        if self.current_reconnect_attempt >= self.max_reconnect_attempts:
            logger.error("Maximum reconnection attempts exceeded")
            self.connection_state = ConnectionState.FAILED
            return
        
        self.current_reconnect_attempt += 1
        self.connection_state = ConnectionState.RECONNECTING
        
        # Calculate backoff delay (exponential with jitter)
        base_delay = self.reconnect_delay * (2 ** (self.current_reconnect_attempt - 1))
        jitter = base_delay * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)
        delay = min(base_delay + jitter, 300)  # Max 5 minutes
        
        logger.info("Attempting WebSocket reconnection", 
                   attempt=self.current_reconnect_attempt,
                   delay=f"{delay:.2f}s")
        
        await asyncio.sleep(delay)
        
        # Attempt reconnection
        if await self.connect():
            logger.info("WebSocket reconnection successful")
        else:
            logger.warning("WebSocket reconnection failed")
            # Will attempt again in the connection monitor loop
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection and processing statistics"""
        return {
            **self.stats,
            "connection_state": self.connection_state.value,
            "active_subscriptions": len(self.active_subscriptions),
            "reconnect_attempt": self.current_reconnect_attempt,
            "queue_size": self.message_queue.qsize()
        }
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected and healthy"""
        return (self.connection_state == ConnectionState.CONNECTED and 
                self.websocket is not None)