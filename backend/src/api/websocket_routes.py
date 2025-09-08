"""WebSocket API routes for real-time updates."""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.base import get_db
from ..database.dao import TradingDAO, UserDAO
from ..security.auth import verify_token
from ..monitoring.metrics import get_metrics_collector
from .schemas import WebSocketMessage, SubscriptionRequest, MarketDataUpdate, PositionUpdate, TradeExecution

router = APIRouter()
logger = logging.getLogger(__name__)

# Connection manager for WebSocket clients
class ConnectionManager:
    """Manages WebSocket connections and message distribution."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> set of connection_ids
        self.connection_subscriptions: Dict[str, Set[str]] = {}  # connection_id -> set of channels
        self.channel_subscribers: Dict[str, Set[str]] = {}  # channel -> set of connection_ids
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: int):
        """Accept a WebSocket connection and register it."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        self.connection_subscriptions[connection_id] = set()
        
        logger.info(f"WebSocket connection established: {connection_id} for user {user_id}")
    
    def disconnect(self, connection_id: str, user_id: int):
        """Remove a WebSocket connection."""
        # Remove from active connections
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove all subscriptions for this connection
        if connection_id in self.connection_subscriptions:
            for channel in self.connection_subscriptions[connection_id]:
                if channel in self.channel_subscribers:
                    self.channel_subscribers[channel].discard(connection_id)
                    if not self.channel_subscribers[channel]:
                        del self.channel_subscribers[channel]
            del self.connection_subscriptions[connection_id]
        
        logger.info(f"WebSocket connection closed: {connection_id} for user {user_id}")
    
    async def subscribe(self, connection_id: str, channels: List[str]) -> bool:
        """Subscribe a connection to channels."""
        if connection_id not in self.active_connections:
            return False
        
        for channel in channels:
            # Add to connection subscriptions
            self.connection_subscriptions[connection_id].add(channel)
            
            # Add to channel subscribers
            if channel not in self.channel_subscribers:
                self.channel_subscribers[channel] = set()
            self.channel_subscribers[channel].add(connection_id)
        
        logger.info(f"Connection {connection_id} subscribed to channels: {channels}")
        return True
    
    async def unsubscribe(self, connection_id: str, channels: List[str]) -> bool:
        """Unsubscribe a connection from channels."""
        if connection_id not in self.active_connections:
            return False
        
        for channel in channels:
            # Remove from connection subscriptions
            self.connection_subscriptions[connection_id].discard(channel)
            
            # Remove from channel subscribers
            if channel in self.channel_subscribers:
                self.channel_subscribers[channel].discard(connection_id)
                if not self.channel_subscribers[channel]:
                    del self.channel_subscribers[channel]
        
        logger.info(f"Connection {connection_id} unsubscribed from channels: {channels}")
        return True
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to connection {connection_id}: {e}")
                # Connection might be dead, remove it
                await self._cleanup_dead_connection(connection_id)
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send a message to all connections of a user."""
        if user_id in self.user_connections:
            dead_connections = []
            for connection_id in self.user_connections[user_id]:
                try:
                    await self.send_to_connection(connection_id, message)
                except Exception as e:
                    logger.error(f"Failed to send to connection {connection_id}: {e}")
                    dead_connections.append(connection_id)
            
            # Clean up dead connections
            for connection_id in dead_connections:
                await self._cleanup_dead_connection(connection_id)
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast a message to all subscribers of a channel."""
        if channel in self.channel_subscribers:
            dead_connections = []
            for connection_id in self.channel_subscribers[channel].copy():
                try:
                    await self.send_to_connection(connection_id, message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to connection {connection_id}: {e}")
                    dead_connections.append(connection_id)
            
            # Clean up dead connections
            for connection_id in dead_connections:
                await self._cleanup_dead_connection(connection_id)
    
    async def _cleanup_dead_connection(self, connection_id: str):
        """Clean up a dead connection."""
        if connection_id in self.active_connections:
            # Try to find the user_id for this connection
            user_id = None
            for uid, conn_ids in self.user_connections.items():
                if connection_id in conn_ids:
                    user_id = uid
                    break
            
            if user_id:
                self.disconnect(connection_id, user_id)
    
    def get_connection_stats(self) -> dict:
        """Get statistics about active connections."""
        total_connections = len(self.active_connections)
        total_users = len(self.user_connections)
        total_channels = len(self.channel_subscribers)
        
        channel_stats = {
            channel: len(subscribers) 
            for channel, subscribers in self.channel_subscribers.items()
        }
        
        return {
            "total_connections": total_connections,
            "total_users": total_users,
            "total_channels": total_channels,
            "channel_subscribers": channel_stats
        }


# Global connection manager
manager = ConnectionManager()


async def get_current_user_from_token(token: str, db: Session) -> Optional[int]:
    """Authenticate user from WebSocket token."""
    try:
        payload = verify_token(token)
        if not payload:
            return None
        
        email = payload.get("sub")
        if not email:
            return None
        
        user_dao = UserDAO(db)
        user = user_dao.get_user_by_email(email)
        
        return user.id if user and user.is_active else None
        
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None


@router.websocket("/api/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Main WebSocket endpoint for real-time updates."""
    connection_id = f"conn_{datetime.utcnow().timestamp()}"
    user_id = None
    
    try:
        # Authenticate user
        if token:
            user_id = await get_current_user_from_token(token, db)
            if not user_id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
                return
        else:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
            return
        
        # Accept connection
        await manager.connect(websocket, connection_id, user_id)
        
        # Send connection confirmation
        await manager.send_to_connection(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await handle_websocket_message(connection_id, user_id, message, db)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_to_connection(connection_id, {
                    "type": "error", 
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        if user_id:
            manager.disconnect(connection_id, user_id)


async def handle_websocket_message(
    connection_id: str, 
    user_id: int, 
    message: dict, 
    db: Session
):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        await handle_subscription(connection_id, message)
    elif message_type == "unsubscribe":
        await handle_unsubscription(connection_id, message)
    elif message_type == "ping":
        await handle_ping(connection_id)
    elif message_type == "get_dashboard_data":
        await handle_dashboard_request(connection_id, user_id, db)
    elif message_type == "get_positions":
        await handle_positions_request(connection_id, user_id, db)
    else:
        await manager.send_to_connection(connection_id, {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat()
        })


async def handle_subscription(connection_id: str, message: dict):
    """Handle channel subscription requests."""
    channels = message.get("channels", [])
    
    if not channels:
        await manager.send_to_connection(connection_id, {
            "type": "error",
            "message": "No channels specified",
            "timestamp": datetime.utcnow().isoformat()
        })
        return
    
    success = await manager.subscribe(connection_id, channels)
    
    if success:
        await manager.send_to_connection(connection_id, {
            "type": "subscription_success",
            "channels": channels,
            "timestamp": datetime.utcnow().isoformat()
        })
    else:
        await manager.send_to_connection(connection_id, {
            "type": "subscription_error",
            "message": "Failed to subscribe to channels",
            "timestamp": datetime.utcnow().isoformat()
        })


async def handle_unsubscription(connection_id: str, message: dict):
    """Handle channel unsubscription requests."""
    channels = message.get("channels", [])
    
    success = await manager.unsubscribe(connection_id, channels)
    
    if success:
        await manager.send_to_connection(connection_id, {
            "type": "unsubscription_success",
            "channels": channels,
            "timestamp": datetime.utcnow().isoformat()
        })


async def handle_ping(connection_id: str):
    """Handle ping messages."""
    await manager.send_to_connection(connection_id, {
        "type": "pong",
        "timestamp": datetime.utcnow().isoformat()
    })


async def handle_dashboard_request(connection_id: str, user_id: int, db: Session):
    """Handle dashboard data requests."""
    try:
        trading_dao = TradingDAO(db)
        
        # Get current positions
        positions = trading_dao.get_current_positions(user_id)
        
        # Calculate basic metrics
        total_unrealized_pnl = sum(pos.unrealized_pnl or 0 for pos in positions)
        
        # Get recent trades
        recent_trades = trading_dao.get_trade_history(user_id, limit=5)
        
        dashboard_data = {
            "type": "dashboard_data",
            "data": {
                "total_equity": 10000 + total_unrealized_pnl,  # Mock account balance
                "daily_pnl": sum(t.realized_pnl or 0 for t in recent_trades),
                "unrealized_pnl": total_unrealized_pnl,
                "open_positions": len(positions),
                "recent_trades_count": len(recent_trades)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_to_connection(connection_id, dashboard_data)
        
    except Exception as e:
        logger.error(f"Error handling dashboard request: {e}")
        await manager.send_to_connection(connection_id, {
            "type": "error",
            "message": "Failed to fetch dashboard data",
            "timestamp": datetime.utcnow().isoformat()
        })


async def handle_positions_request(connection_id: str, user_id: int, db: Session):
    """Handle positions data requests."""
    try:
        trading_dao = TradingDAO(db)
        positions = trading_dao.get_current_positions(user_id)
        
        positions_data = {
            "type": "positions_data",
            "data": [
                {
                    "id": pos.id,
                    "symbol": pos.symbol,
                    "side": pos.side,
                    "size": pos.size,
                    "entry_price": pos.entry_price,
                    "mark_price": pos.mark_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_percent": pos.unrealized_pnl_percent,
                    "leverage": pos.leverage
                }
                for pos in positions
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_to_connection(connection_id, positions_data)
        
    except Exception as e:
        logger.error(f"Error handling positions request: {e}")
        await manager.send_to_connection(connection_id, {
            "type": "error",
            "message": "Failed to fetch positions data",
            "timestamp": datetime.utcnow().isoformat()
        })


# WebSocket broadcasting functions for external use

async def broadcast_market_data(symbol: str, price: float, volume: float = None):
    """Broadcast market data update to subscribers."""
    message = {
        "type": "market_data",
        "data": {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    await manager.broadcast_to_channel(f"market_data_{symbol}", message)
    await manager.broadcast_to_channel("market_data_all", message)


async def broadcast_position_update(user_id: int, position_data: dict):
    """Broadcast position update to user."""
    message = {
        "type": "position_update",
        "data": position_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.send_to_user(user_id, message)
    
    # Also broadcast to position-specific channel
    symbol = position_data.get("symbol")
    if symbol:
        await manager.broadcast_to_channel(f"positions_{symbol}", message)


async def broadcast_trade_execution(user_id: int, trade_data: dict):
    """Broadcast trade execution to user."""
    message = {
        "type": "trade_execution",
        "data": trade_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.send_to_user(user_id, message)
    
    # Also broadcast to trade-specific channel
    symbol = trade_data.get("symbol")
    if symbol:
        await manager.broadcast_to_channel(f"trades_{symbol}", message)


async def broadcast_alert(user_id: int, alert_data: dict):
    """Broadcast alert to user."""
    message = {
        "type": "alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.send_to_user(user_id, message)


async def broadcast_system_status(status_data: dict):
    """Broadcast system status to all connected users."""
    message = {
        "type": "system_status",
        "data": status_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast_to_channel("system_status", message)


# Health check for WebSocket connections
@router.get("/api/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return manager.get_connection_stats()


# Background task to send periodic updates
async def periodic_updates_task():
    """Background task to send periodic updates to connected clients."""
    while True:
        try:
            # Send heartbeat to all connections
            heartbeat_message = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "server_time": datetime.utcnow().isoformat()
            }
            
            # Send to all users subscribed to heartbeat
            await manager.broadcast_to_channel("heartbeat", heartbeat_message)
            
            # Record WebSocket metrics
            metrics = get_metrics_collector()
            stats = manager.get_connection_stats()
            metrics.set_gauge("websocket_connections", stats["total_connections"])
            metrics.set_gauge("websocket_users", stats["total_users"])
            
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in periodic updates task: {e}")
            await asyncio.sleep(60)  # Wait longer on error


# Export the manager for use in other modules
__all__ = [
    "manager",
    "broadcast_market_data",
    "broadcast_position_update", 
    "broadcast_trade_execution",
    "broadcast_alert",
    "broadcast_system_status",
    "periodic_updates_task"
]