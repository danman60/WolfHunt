"""Tests for market data processing."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from backend.src.market_data.price_feed import PriceFeed
from backend.src.market_data.orderbook import OrderbookManager
from backend.src.market_data.websocket_client import MarketDataWebSocketClient


class TestPriceFeed:
    """Test Price Feed."""
    
    def test_price_feed_initialization(self):
        """Test price feed initialization."""
        price_feed = PriceFeed()
        
        assert price_feed.symbols == []
        assert price_feed._prices == {}
        assert price_feed._subscribers == {}
    
    def test_add_symbol(self):
        """Test adding a symbol to price feed."""
        price_feed = PriceFeed()
        
        price_feed.add_symbol('BTC-USD')
        
        assert 'BTC-USD' in price_feed.symbols
        assert 'BTC-USD' in price_feed._prices
    
    def test_remove_symbol(self):
        """Test removing a symbol from price feed."""
        price_feed = PriceFeed()
        
        price_feed.add_symbol('BTC-USD')
        price_feed.remove_symbol('BTC-USD')
        
        assert 'BTC-USD' not in price_feed.symbols
        assert 'BTC-USD' not in price_feed._prices
    
    def test_update_price(self):
        """Test price update."""
        price_feed = PriceFeed()
        price_feed.add_symbol('BTC-USD')
        
        # Mock price data
        price_data = {
            'symbol': 'BTC-USD',
            'price': 45000.00,
            'timestamp': datetime.utcnow(),
            'volume': 1.5,
            'bid': 44995.00,
            'ask': 45005.00
        }
        
        price_feed.update_price('BTC-USD', price_data)
        
        stored_price = price_feed.get_latest_price('BTC-USD')
        assert stored_price['price'] == 45000.00
        assert stored_price['symbol'] == 'BTC-USD'
    
    def test_get_latest_price(self):
        """Test getting latest price."""
        price_feed = PriceFeed()
        price_feed.add_symbol('BTC-USD')
        
        # No price yet
        price = price_feed.get_latest_price('BTC-USD')
        assert price is None
        
        # Add price
        price_data = {
            'symbol': 'BTC-USD',
            'price': 45000.00,
            'timestamp': datetime.utcnow()
        }
        price_feed.update_price('BTC-USD', price_data)
        
        # Get price
        price = price_feed.get_latest_price('BTC-USD')
        assert price['price'] == 45000.00
    
    def test_get_price_history(self):
        """Test getting price history."""
        price_feed = PriceFeed()
        price_feed.add_symbol('BTC-USD')
        
        # Add multiple prices
        for i in range(5):
            price_data = {
                'symbol': 'BTC-USD',
                'price': 45000.00 + i * 100,
                'timestamp': datetime.utcnow() - timedelta(minutes=i)
            }
            price_feed.update_price('BTC-USD', price_data)
        
        history = price_feed.get_price_history('BTC-USD', limit=3)
        assert len(history) == 3
        assert history[0]['price'] == 45400.00  # Latest price
    
    def test_subscribe_to_price_updates(self):
        """Test subscribing to price updates."""
        price_feed = PriceFeed()
        price_feed.add_symbol('BTC-USD')
        
        callback_called = False
        received_data = None
        
        def price_callback(symbol, price_data):
            nonlocal callback_called, received_data
            callback_called = True
            received_data = price_data
        
        price_feed.subscribe('BTC-USD', price_callback)
        
        # Update price - should trigger callback
        price_data = {
            'symbol': 'BTC-USD',
            'price': 45000.00,
            'timestamp': datetime.utcnow()
        }
        price_feed.update_price('BTC-USD', price_data)
        
        assert callback_called is True
        assert received_data['price'] == 45000.00


class TestOrderbookManager:
    """Test Orderbook Manager."""
    
    def test_orderbook_initialization(self):
        """Test orderbook initialization."""
        orderbook = OrderbookManager()
        
        assert orderbook._orderbooks == {}
    
    def test_create_orderbook(self):
        """Test creating orderbook for symbol."""
        orderbook = OrderbookManager()
        
        orderbook.create_orderbook('BTC-USD')
        
        assert 'BTC-USD' in orderbook._orderbooks
        assert 'bids' in orderbook._orderbooks['BTC-USD']
        assert 'asks' in orderbook._orderbooks['BTC-USD']
    
    def test_update_orderbook(self):
        """Test updating orderbook."""
        orderbook = OrderbookManager()
        orderbook.create_orderbook('BTC-USD')
        
        # Mock orderbook data
        orderbook_data = {
            'symbol': 'BTC-USD',
            'bids': [
                {'price': 44995.00, 'size': 1.5},
                {'price': 44990.00, 'size': 2.0}
            ],
            'asks': [
                {'price': 45005.00, 'size': 1.2},
                {'price': 45010.00, 'size': 1.8}
            ],
            'timestamp': datetime.utcnow()
        }
        
        orderbook.update_orderbook('BTC-USD', orderbook_data)
        
        book = orderbook.get_orderbook('BTC-USD')
        assert len(book['bids']) == 2
        assert len(book['asks']) == 2
        assert book['bids'][0]['price'] == 44995.00
    
    def test_get_best_bid_ask(self):
        """Test getting best bid and ask."""
        orderbook = OrderbookManager()
        orderbook.create_orderbook('BTC-USD')
        
        # Update with sample data
        orderbook_data = {
            'symbol': 'BTC-USD',
            'bids': [
                {'price': 44995.00, 'size': 1.5},
                {'price': 44990.00, 'size': 2.0}
            ],
            'asks': [
                {'price': 45005.00, 'size': 1.2},
                {'price': 45010.00, 'size': 1.8}
            ],
            'timestamp': datetime.utcnow()
        }
        
        orderbook.update_orderbook('BTC-USD', orderbook_data)
        
        best_bid = orderbook.get_best_bid('BTC-USD')
        best_ask = orderbook.get_best_ask('BTC-USD')
        
        assert best_bid == 44995.00
        assert best_ask == 45005.00
    
    def test_get_spread(self):
        """Test getting bid-ask spread."""
        orderbook = OrderbookManager()
        orderbook.create_orderbook('BTC-USD')
        
        # Update with sample data
        orderbook_data = {
            'symbol': 'BTC-USD',
            'bids': [{'price': 44995.00, 'size': 1.5}],
            'asks': [{'price': 45005.00, 'size': 1.2}],
            'timestamp': datetime.utcnow()
        }
        
        orderbook.update_orderbook('BTC-USD', orderbook_data)
        
        spread = orderbook.get_spread('BTC-USD')
        assert spread == 10.00  # 45005 - 44995
    
    def test_get_market_depth(self):
        """Test getting market depth."""
        orderbook = OrderbookManager()
        orderbook.create_orderbook('BTC-USD')
        
        # Update with multiple levels
        orderbook_data = {
            'symbol': 'BTC-USD',
            'bids': [
                {'price': 44995.00, 'size': 1.5},
                {'price': 44990.00, 'size': 2.0},
                {'price': 44985.00, 'size': 1.8}
            ],
            'asks': [
                {'price': 45005.00, 'size': 1.2},
                {'price': 45010.00, 'size': 1.8},
                {'price': 45015.00, 'size': 2.2}
            ],
            'timestamp': datetime.utcnow()
        }
        
        orderbook.update_orderbook('BTC-USD', orderbook_data)
        
        depth = orderbook.get_market_depth('BTC-USD', levels=2)
        
        assert len(depth['bids']) == 2
        assert len(depth['asks']) == 2
        assert depth['bids'][0]['price'] == 44995.00


class TestMarketDataWebSocketClient:
    """Test Market Data WebSocket Client."""
    
    @pytest.fixture
    def ws_client(self):
        """Create WebSocket client fixture."""
        return MarketDataWebSocketClient()
    
    def test_websocket_client_initialization(self, ws_client):
        """Test WebSocket client initialization."""
        assert ws_client._ws is None
        assert ws_client._subscriptions == set()
        assert ws_client._reconnect_attempts == 0
    
    @pytest.mark.asyncio
    async def test_connect(self, ws_client):
        """Test WebSocket connection."""
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws
            
            await ws_client.connect()
            
            assert ws_client._ws is not None
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe_to_ticker(self, ws_client):
        """Test subscribing to ticker updates."""
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws
            
            await ws_client.connect()
            await ws_client.subscribe_ticker('BTC-USD')
            
            assert 'ticker:BTC-USD' in ws_client._subscriptions
            mock_ws.send.assert_called()
    
    @pytest.mark.asyncio
    async def test_subscribe_to_orderbook(self, ws_client):
        """Test subscribing to orderbook updates."""
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws
            
            await ws_client.connect()
            await ws_client.subscribe_orderbook('BTC-USD')
            
            assert 'orderbook:BTC-USD' in ws_client._subscriptions
            mock_ws.send.assert_called()
    
    @pytest.mark.asyncio
    async def test_message_handling(self, ws_client):
        """Test WebSocket message handling."""
        callback_called = False
        received_message = None
        
        def message_callback(message):
            nonlocal callback_called, received_message
            callback_called = True
            received_message = message
        
        ws_client.add_message_handler(message_callback)
        
        # Mock incoming message
        test_message = {
            'type': 'ticker',
            'symbol': 'BTC-USD',
            'price': 45000.00,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await ws_client._handle_message(test_message)
        
        assert callback_called is True
        assert received_message['price'] == 45000.00
    
    @pytest.mark.asyncio
    async def test_reconnection_logic(self, ws_client):
        """Test automatic reconnection logic."""
        with patch('websockets.connect') as mock_connect:
            # First connection fails, second succeeds
            mock_connect.side_effect = [ConnectionError("Connection failed"), AsyncMock()]
            
            with patch('asyncio.sleep'):  # Speed up test
                await ws_client._reconnect()
            
            assert ws_client._reconnect_attempts > 0
    
    @pytest.mark.asyncio
    async def test_disconnect(self, ws_client):
        """Test WebSocket disconnection."""
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws
            
            await ws_client.connect()
            await ws_client.disconnect()
            
            mock_ws.close.assert_called_once()
            assert ws_client._ws is None
    
    def test_subscription_management(self, ws_client):
        """Test subscription management."""
        # Add subscription
        ws_client._add_subscription('ticker:BTC-USD')
        assert 'ticker:BTC-USD' in ws_client._subscriptions
        
        # Remove subscription
        ws_client._remove_subscription('ticker:BTC-USD')
        assert 'ticker:BTC-USD' not in ws_client._subscriptions
    
    @pytest.mark.asyncio
    async def test_error_handling(self, ws_client):
        """Test error handling in message processing."""
        with patch('backend.src.market_data.websocket_client.logger') as mock_logger:
            # Send invalid message
            invalid_message = "invalid json"
            
            await ws_client._handle_message(invalid_message)
            
            # Should log error but not crash
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_health_check(self, ws_client):
        """Test WebSocket health check."""
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_ws.ping.return_value = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws
            
            await ws_client.connect()
            is_healthy = await ws_client.health_check()
            
            assert is_healthy is True
            mock_ws.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, ws_client):
        """Test rate limiting on subscriptions."""
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws
            
            await ws_client.connect()
            
            # Subscribe to many symbols rapidly
            symbols = [f'SYMBOL-{i}' for i in range(100)]
            
            for symbol in symbols:
                await ws_client.subscribe_ticker(symbol)
            
            # Should handle rate limiting gracefully
            assert len(ws_client._subscriptions) <= 50  # Assuming 50 is the limit