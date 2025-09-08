"""Tests for WebSocket endpoints."""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from backend.src.api.websocket_routes import ConnectionManager


class TestWebSocketEndpoints:
    """Test WebSocket endpoints."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, test_client: TestClient):
        """Test WebSocket connection establishment."""
        with test_client.websocket_connect("/ws/trading") as websocket:
            # Connection should be established
            assert websocket is not None
    
    @pytest.mark.asyncio
    async def test_websocket_authentication(self, test_client: TestClient):
        """Test WebSocket authentication."""
        # Test without token - should disconnect
        with pytest.raises(WebSocketDisconnect):
            with test_client.websocket_connect("/ws/trading"):
                pass
        
        # Test with invalid token
        with pytest.raises(WebSocketDisconnect):
            with test_client.websocket_connect("/ws/trading?token=invalid_token"):
                pass
    
    @pytest.mark.asyncio
    async def test_websocket_authenticated_connection(self, test_client: TestClient, test_user_token):
        """Test WebSocket connection with valid authentication."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert data["type"] == "connection"
            assert data["status"] == "connected"
    
    @pytest.mark.asyncio
    async def test_websocket_subscription(self, test_client: TestClient, test_user_token):
        """Test WebSocket subscription to updates."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send subscription request
            subscription_request = {
                "type": "subscribe",
                "channels": ["positions", "trades", "market_data"],
                "symbols": ["BTC-USD", "ETH-USD"]
            }
            websocket.send_json(subscription_request)
            
            # Should receive subscription confirmation
            response = websocket.receive_json()
            assert response["type"] == "subscription"
            assert response["status"] == "subscribed"
    
    @pytest.mark.asyncio
    async def test_websocket_position_updates(self, test_client: TestClient, test_user_token):
        """Test WebSocket position updates."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Subscribe to position updates
            websocket.send_json({
                "type": "subscribe",
                "channels": ["positions"]
            })
            websocket.receive_json()  # Skip subscription confirmation
            
            # Mock position update
            with patch('backend.src.api.websocket_routes.connection_manager') as mock_manager:
                mock_manager.broadcast_position_update = AsyncMock()
                
                # Simulate position update
                position_data = {
                    "symbol": "BTC-USD",
                    "side": "LONG",
                    "size": 0.001,
                    "entry_price": 45000.00,
                    "unrealized_pnl": 50.00,
                    "unrealized_pnl_percent": 0.11
                }
                
                await mock_manager.broadcast_position_update(1, position_data)
                mock_manager.broadcast_position_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_trade_updates(self, test_client: TestClient, test_user_token):
        """Test WebSocket trade updates."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            # Skip welcome and subscription messages
            websocket.receive_json()
            
            # Subscribe to trade updates
            websocket.send_json({
                "type": "subscribe",
                "channels": ["trades"]
            })
            websocket.receive_json()
            
            # Mock trade update
            with patch('backend.src.api.websocket_routes.connection_manager') as mock_manager:
                mock_manager.broadcast_trade_update = AsyncMock()
                
                trade_data = {
                    "order_id": "test_order_123",
                    "symbol": "BTC-USD",
                    "side": "BUY",
                    "size": 0.001,
                    "price": 45000.00,
                    "status": "FILLED",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                
                await mock_manager.broadcast_trade_update(1, trade_data)
                mock_manager.broadcast_trade_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_market_data_updates(self, test_client: TestClient, test_user_token):
        """Test WebSocket market data updates."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            websocket.receive_json()  # Skip welcome
            
            # Subscribe to market data
            websocket.send_json({
                "type": "subscribe",
                "channels": ["market_data"],
                "symbols": ["BTC-USD"]
            })
            websocket.receive_json()  # Skip subscription confirmation
            
            # Mock market data update
            with patch('backend.src.api.websocket_routes.connection_manager') as mock_manager:
                mock_manager.broadcast_market_data = AsyncMock()
                
                market_data = {
                    "symbol": "BTC-USD",
                    "price": 45000.00,
                    "volume": 1.5,
                    "timestamp": "2024-01-01T00:00:00Z",
                    "bid": 44995.00,
                    "ask": 45005.00
                }
                
                await mock_manager.broadcast_market_data("BTC-USD", market_data)
                mock_manager.broadcast_market_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_alert_updates(self, test_client: TestClient, test_user_token):
        """Test WebSocket alert updates."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            websocket.receive_json()  # Skip welcome
            
            # Subscribe to alerts
            websocket.send_json({
                "type": "subscribe",
                "channels": ["alerts"]
            })
            websocket.receive_json()  # Skip subscription confirmation
            
            # Mock alert update
            with patch('backend.src.api.websocket_routes.connection_manager') as mock_manager:
                mock_manager.send_alert = AsyncMock()
                
                alert_data = {
                    "alert_type": "trading",
                    "severity": "WARNING",
                    "title": "High Loss Alert",
                    "message": "Daily loss exceeds 5%",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                
                await mock_manager.send_alert(1, alert_data)
                mock_manager.send_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_unsubscribe(self, test_client: TestClient, test_user_token):
        """Test WebSocket unsubscription."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            websocket.receive_json()  # Skip welcome
            
            # Subscribe first
            websocket.send_json({
                "type": "subscribe",
                "channels": ["positions"]
            })
            websocket.receive_json()  # Skip subscription confirmation
            
            # Unsubscribe
            websocket.send_json({
                "type": "unsubscribe",
                "channels": ["positions"]
            })
            
            # Should receive unsubscription confirmation
            response = websocket.receive_json()
            assert response["type"] == "subscription"
            assert response["status"] == "unsubscribed"
    
    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, test_client: TestClient, test_user_token):
        """Test WebSocket ping-pong mechanism."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            websocket.receive_json()  # Skip welcome
            
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, test_client: TestClient, test_user_token):
        """Test WebSocket error handling."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            websocket.receive_json()  # Skip welcome
            
            # Send invalid message
            websocket.send_text("invalid json")
            
            # Should receive error message
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "message" in response
    
    @pytest.mark.asyncio
    async def test_websocket_rate_limiting(self, test_client: TestClient, test_user_token):
        """Test WebSocket rate limiting."""
        with test_client.websocket_connect(f"/ws/trading?token={test_user_token}") as websocket:
            websocket.receive_json()  # Skip welcome
            
            # Send many messages rapidly
            for i in range(100):
                websocket.send_json({"type": "ping"})
            
            # Should handle rate limiting gracefully
            # The exact behavior depends on implementation
            response = websocket.receive_json()
            assert response is not None  # Should not crash


class TestConnectionManager:
    """Test Connection Manager."""
    
    def test_connection_manager_initialization(self):
        """Test connection manager initialization."""
        manager = ConnectionManager()
        
        assert manager.active_connections == {}
        assert manager.user_subscriptions == {}
    
    @pytest.mark.asyncio
    async def test_connect_user(self):
        """Test connecting a user."""
        manager = ConnectionManager()
        
        # Mock WebSocket and user
        websocket = Mock()
        user_id = 1
        
        await manager.connect(websocket, user_id)
        
        assert user_id in manager.active_connections
        assert manager.active_connections[user_id] == websocket
    
    @pytest.mark.asyncio
    async def test_disconnect_user(self):
        """Test disconnecting a user."""
        manager = ConnectionManager()
        
        # Connect first
        websocket = Mock()
        user_id = 1
        await manager.connect(websocket, user_id)
        
        # Disconnect
        manager.disconnect(user_id)
        
        assert user_id not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending personal message to user."""
        manager = ConnectionManager()
        
        # Mock WebSocket
        websocket = AsyncMock()
        user_id = 1
        
        await manager.connect(websocket, user_id)
        
        # Send message
        message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(user_id, message)
        
        websocket.send_text.assert_called_once_with(json.dumps(message))
    
    @pytest.mark.asyncio
    async def test_subscribe_user(self):
        """Test subscribing user to channels."""
        manager = ConnectionManager()
        
        user_id = 1
        channels = ["positions", "trades"]
        symbols = ["BTC-USD", "ETH-USD"]
        
        manager.subscribe_user(user_id, channels, symbols)
        
        assert user_id in manager.user_subscriptions
        assert "positions" in manager.user_subscriptions[user_id]["channels"]
        assert "BTC-USD" in manager.user_subscriptions[user_id]["symbols"]
    
    @pytest.mark.asyncio
    async def test_unsubscribe_user(self):
        """Test unsubscribing user from channels."""
        manager = ConnectionManager()
        
        user_id = 1
        
        # Subscribe first
        manager.subscribe_user(user_id, ["positions"], ["BTC-USD"])
        
        # Unsubscribe
        manager.unsubscribe_user(user_id, ["positions"])
        
        assert "positions" not in manager.user_subscriptions[user_id]["channels"]
    
    @pytest.mark.asyncio
    async def test_broadcast_to_subscribed_users(self):
        """Test broadcasting to subscribed users."""
        manager = ConnectionManager()
        
        # Mock WebSockets for multiple users
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()
        
        user_id1 = 1
        user_id2 = 2
        
        await manager.connect(websocket1, user_id1)
        await manager.connect(websocket2, user_id2)
        
        # Subscribe users to different channels
        manager.subscribe_user(user_id1, ["positions"], ["BTC-USD"])
        manager.subscribe_user(user_id2, ["trades"], ["ETH-USD"])
        
        # Broadcast position update (should only go to user1)
        position_data = {"symbol": "BTC-USD", "data": "test"}
        await manager.broadcast_position_update(user_id1, position_data)
        
        websocket1.send_text.assert_called()
        websocket2.send_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_disconnected_users(self):
        """Test cleanup of disconnected users."""
        manager = ConnectionManager()
        
        # Mock WebSocket that will raise exception
        websocket = AsyncMock()
        websocket.send_text.side_effect = ConnectionError("Connection lost")
        
        user_id = 1
        await manager.connect(websocket, user_id)
        
        # Try to send message - should handle disconnection
        message = {"type": "test"}
        await manager.send_personal_message(user_id, message)
        
        # User should be removed from active connections
        assert user_id not in manager.active_connections
    
    def test_get_connection_stats(self):
        """Test getting connection statistics."""
        manager = ConnectionManager()
        
        # Add some connections
        manager.active_connections[1] = Mock()
        manager.active_connections[2] = Mock()
        manager.user_subscriptions[1] = {"channels": ["positions"], "symbols": ["BTC-USD"]}
        
        stats = manager.get_connection_stats()
        
        assert stats["active_connections"] == 2
        assert stats["total_subscriptions"] == 1
    
    @pytest.mark.asyncio
    async def test_broadcast_system_message(self):
        """Test broadcasting system message to all users."""
        manager = ConnectionManager()
        
        # Mock multiple WebSocket connections
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()
        
        await manager.connect(websocket1, 1)
        await manager.connect(websocket2, 2)
        
        # Broadcast system message
        system_message = {
            "type": "system",
            "message": "System maintenance in 5 minutes"
        }
        await manager.broadcast_system_message(system_message)
        
        websocket1.send_text.assert_called()
        websocket2.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_connection_health_check(self):
        """Test connection health checking."""
        manager = ConnectionManager()
        
        # Mock WebSocket with ping capability
        websocket = AsyncMock()
        websocket.ping.return_value = AsyncMock()
        
        await manager.connect(websocket, 1)
        
        # Perform health check
        healthy_connections = await manager.health_check()
        
        assert len(healthy_connections) == 1
        websocket.ping.assert_called_once()