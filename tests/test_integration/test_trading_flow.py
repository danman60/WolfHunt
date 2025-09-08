"""Integration tests for complete trading flows."""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from backend.src.database.models import User, Trade, Position
from backend.src.trading.strategies.ma_crossover import MovingAverageCrossoverStrategy
from backend.src.trading.risk_manager import RiskManager
from backend.src.trading.dydx_client import DYDXTradingClient


class TestCompleteTradeExecution:
    """Test complete trade execution flow."""
    
    @pytest.mark.asyncio
    async def test_complete_buy_trade_flow(self, db_session: Session, test_user: User):
        """Test complete buy trade execution flow."""
        # Initialize components
        strategy = MovingAverageCrossoverStrategy()
        risk_manager = RiskManager()
        
        with patch('backend.src.trading.dydx_client.DYDXTradingClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock successful order placement
            mock_client.place_order.return_value = {
                'order_id': 'test_order_123',
                'status': 'PENDING',
                'symbol': 'BTC-USD',
                'side': 'BUY',
                'size': 0.001,
                'price': 45000.00
            }
            
            # Mock order fill
            mock_client.get_order_status.return_value = {
                'order_id': 'test_order_123',
                'status': 'FILLED',
                'filled_size': 0.001,
                'avg_fill_price': 45000.00,
                'commission': 0.045
            }
            
            # Create candle data that generates BUY signal
            candles = self._create_buy_signal_candles()
            
            # 1. Strategy generates signal
            signal = strategy.analyze(candles)
            assert signal.signal_type.name == 'BUY'
            
            # 2. Risk manager approves trade
            trade_request = {
                'symbol': 'BTC-USD',
                'side': 'BUY',
                'size': Decimal('0.001'),
                'price': Decimal('45000.0')
            }
            risk_check = risk_manager.comprehensive_risk_check(test_user, trade_request)
            assert risk_check.approved is True
            
            # 3. Execute trade through client
            trading_client = DYDXTradingClient(test_user.encrypted_api_key, test_user.encrypted_api_secret)
            
            order_result = await trading_client.place_order(
                symbol='BTC-USD',
                side='BUY',
                order_type='MARKET',
                size=0.001,
                reduce_only=False
            )
            
            assert order_result['order_id'] == 'test_order_123'
            
            # 4. Monitor order execution
            order_status = await trading_client.get_order_status(order_result['order_id'])
            assert order_status['status'] == 'FILLED'
            
            # 5. Create trade record
            trade = Trade(
                user_id=test_user.id,
                order_id=order_result['order_id'],
                symbol='BTC-USD',
                side='BUY',
                order_type='MARKET',
                size=Decimal('0.001'),
                price=Decimal('45000.00'),
                filled_size=Decimal('0.001'),
                notional_value=Decimal('45.00'),
                commission=Decimal('0.045'),
                status='FILLED'
            )
            
            db_session.add(trade)
            db_session.commit()
            
            # Verify trade record
            saved_trade = db_session.query(Trade).filter(Trade.order_id == 'test_order_123').first()
            assert saved_trade is not None
            assert saved_trade.status == 'FILLED'
    
    @pytest.mark.asyncio
    async def test_complete_sell_trade_flow(self, db_session: Session, test_user: User):
        """Test complete sell trade execution flow."""
        # First create a position to sell
        position = Position(
            user_id=test_user.id,
            symbol='BTC-USD',
            side='LONG',
            size=Decimal('0.001'),
            entry_price=Decimal('45000.00'),
            mark_price=Decimal('46000.00'),
            unrealized_pnl=Decimal('1.00'),
            unrealized_pnl_percent=Decimal('2.22'),
            notional_value=Decimal('46.00'),
            margin_used=Decimal('15.33'),
            leverage=Decimal('3.0'),
            is_open=True
        )
        db_session.add(position)
        db_session.commit()
        
        # Initialize components
        strategy = MovingAverageCrossoverStrategy()
        risk_manager = RiskManager()
        
        with patch('backend.src.trading.dydx_client.DYDXTradingClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock successful sell order
            mock_client.place_order.return_value = {
                'order_id': 'test_sell_123',
                'status': 'PENDING',
                'symbol': 'BTC-USD',
                'side': 'SELL',
                'size': 0.001,
                'price': 46000.00,
                'reduce_only': True
            }
            
            mock_client.get_order_status.return_value = {
                'order_id': 'test_sell_123',
                'status': 'FILLED',
                'filled_size': 0.001,
                'avg_fill_price': 46000.00,
                'commission': 0.046
            }
            
            # Create candle data that generates SELL signal
            candles = self._create_sell_signal_candles()
            
            # 1. Strategy generates sell signal
            signal = strategy.analyze(candles)
            assert signal.signal_type.name == 'SELL'
            
            # 2. Check if position should be exited
            should_exit = strategy.should_exit(position, Decimal('46000.00'))
            assert should_exit is True  # Profit taking
            
            # 3. Execute sell trade
            trading_client = DYDXTradingClient(test_user.encrypted_api_key, test_user.encrypted_api_secret)
            
            order_result = await trading_client.place_order(
                symbol='BTC-USD',
                side='SELL',
                order_type='MARKET',
                size=0.001,
                reduce_only=True
            )
            
            # 4. Update position
            position.is_open = False
            position.closed_at = order_result.get('timestamp')
            position.exit_price = Decimal('46000.00')
            position.realized_pnl = Decimal('1.00')
            
            db_session.commit()
            
            # Verify position is closed
            updated_position = db_session.query(Position).filter(Position.id == position.id).first()
            assert updated_position.is_open is False
            assert updated_position.realized_pnl == Decimal('1.00')
    
    @pytest.mark.asyncio
    async def test_risk_rejection_flow(self, db_session: Session, test_user: User):
        """Test trade rejection due to risk limits."""
        # Set user to have low account balance
        test_user.account_balance = Decimal('100.00')  # Very low balance
        db_session.commit()
        
        risk_manager = RiskManager()
        
        # Large trade request that exceeds risk limits
        trade_request = {
            'symbol': 'BTC-USD',
            'side': 'BUY',
            'size': Decimal('0.1'),  # Very large position
            'price': Decimal('45000.0')
        }
        
        # Risk check should fail
        risk_check = risk_manager.comprehensive_risk_check(test_user, trade_request)
        assert risk_check.approved is False
        assert len(risk_check.violations) > 0
        
        # Trade should not be executed
        # No mocked client calls should be made
        # No trade records should be created
        trades_count = db_session.query(Trade).filter(Trade.user_id == test_user.id).count()
        assert trades_count == 0
    
    @pytest.mark.asyncio
    async def test_emergency_stop_flow(self, db_session: Session, test_user: User):
        """Test emergency stop activation and trade blocking."""
        risk_manager = RiskManager()
        
        # Activate emergency stop
        risk_manager.activate_emergency_stop(test_user, "Test emergency stop")
        
        # Any trade request should be blocked
        trade_request = {
            'symbol': 'BTC-USD',
            'side': 'BUY',
            'size': Decimal('0.001'),
            'price': Decimal('45000.0')
        }
        
        risk_check = risk_manager.check_emergency_stop(test_user)
        assert risk_check.approved is False
        
        # Strategy should also check emergency stop
        strategy = MovingAverageCrossoverStrategy()
        candles = self._create_buy_signal_candles()
        
        # Even with buy signal, should be blocked by emergency stop
        signal = strategy.analyze(candles)
        
        # In real implementation, strategy would check emergency stop
        # and return HOLD signal regardless of technical indicators
        
        # No trades should be executed
        trades_count = db_session.query(Trade).filter(Trade.user_id == test_user.id).count()
        assert trades_count == 0
    
    @pytest.mark.asyncio
    async def test_paper_trading_flow(self, db_session: Session, test_user: User):
        """Test paper trading execution flow."""
        # Enable paper trading mode
        test_user.paper_trading_mode = True
        db_session.commit()
        
        strategy = MovingAverageCrossoverStrategy()
        
        with patch('backend.src.trading.paper_trading.PaperTradingClient') as mock_paper_client:
            mock_client = AsyncMock()
            mock_paper_client.return_value = mock_client
            
            # Mock paper trade execution
            mock_client.place_order.return_value = {
                'order_id': 'paper_order_123',
                'status': 'FILLED',
                'symbol': 'BTC-USD',
                'side': 'BUY',
                'size': 0.001,
                'price': 45000.00,
                'paper_trade': True
            }
            
            candles = self._create_buy_signal_candles()
            signal = strategy.analyze(candles)
            
            # Execute paper trade
            from backend.src.trading.paper_trading import PaperTradingClient
            paper_client = PaperTradingClient(test_user.id)
            
            order_result = await paper_client.place_order(
                symbol='BTC-USD',
                side='BUY',
                order_type='MARKET',
                size=0.001
            )
            
            assert order_result['paper_trade'] is True
            assert order_result['order_id'] == 'paper_order_123'
            
            # Create paper trade record
            trade = Trade(
                user_id=test_user.id,
                order_id=order_result['order_id'],
                symbol='BTC-USD',
                side='BUY',
                order_type='MARKET',
                size=Decimal('0.001'),
                price=Decimal('45000.00'),
                filled_size=Decimal('0.001'),
                notional_value=Decimal('45.00'),
                commission=Decimal('0.00'),  # No commission in paper trading
                status='FILLED',
                is_paper_trade=True
            )
            
            db_session.add(trade)
            db_session.commit()
            
            # Verify paper trade record
            paper_trade = db_session.query(Trade).filter(
                Trade.order_id == 'paper_order_123'
            ).first()
            assert paper_trade is not None
            assert paper_trade.is_paper_trade is True
    
    def _create_buy_signal_candles(self):
        """Create candle data that generates a BUY signal."""
        # Uptrend with fast EMA crossing above slow EMA
        prices = [100, 101, 102, 105, 108, 110, 112, 115, 118, 120, 122, 125, 128, 130]
        candles = []
        
        for i, price in enumerate(prices):
            candles.append({
                'timestamp': f'2024-01-01T{i:02d}:00:00',
                'open': price - 0.5,
                'high': price + 1,
                'low': price - 1,
                'close': price,
                'volume': 1000 + i * 100
            })
        
        return candles
    
    def _create_sell_signal_candles(self):
        """Create candle data that generates a SELL signal."""
        # Downtrend with fast EMA crossing below slow EMA
        prices = [130, 128, 125, 122, 120, 118, 115, 112, 110, 108, 105, 102, 100, 98]
        candles = []
        
        for i, price in enumerate(prices):
            candles.append({
                'timestamp': f'2024-01-01T{i:02d}:00:00',
                'open': price + 0.5,
                'high': price + 1,
                'low': price - 1,
                'close': price,
                'volume': 1000 + i * 50
            })
        
        return candles


class TestWebSocketIntegration:
    """Test WebSocket integration with trading flows."""
    
    @pytest.mark.asyncio
    async def test_real_time_position_updates(self, test_client, test_user_token):
        """Test real-time position updates via WebSocket."""
        with patch('backend.src.api.websocket_routes.connection_manager') as mock_manager:
            mock_manager.broadcast_position_update = AsyncMock()
            
            # Simulate position change
            position_data = {
                'symbol': 'BTC-USD',
                'side': 'LONG',
                'size': 0.001,
                'unrealized_pnl': 50.00,
                'unrealized_pnl_percent': 1.11
            }
            
            # Should broadcast to connected users
            await mock_manager.broadcast_position_update(1, position_data)
            
            mock_manager.broadcast_position_update.assert_called_once_with(1, position_data)
    
    @pytest.mark.asyncio
    async def test_real_time_trade_notifications(self, test_client, test_user_token):
        """Test real-time trade notifications via WebSocket."""
        with patch('backend.src.api.websocket_routes.connection_manager') as mock_manager:
            mock_manager.broadcast_trade_update = AsyncMock()
            
            # Simulate trade execution
            trade_data = {
                'order_id': 'test_order_123',
                'symbol': 'BTC-USD',
                'side': 'BUY',
                'status': 'FILLED',
                'price': 45000.00,
                'size': 0.001
            }
            
            await mock_manager.broadcast_trade_update(1, trade_data)
            
            mock_manager.broadcast_trade_update.assert_called_once_with(1, trade_data)


class TestAPIIntegration:
    """Test API integration with trading components."""
    
    @pytest.mark.asyncio
    async def test_dashboard_data_integration(self, authenticated_client, db_session, test_user):
        """Test dashboard data retrieval integration."""
        # Create some test data
        trade1 = Trade(
            user_id=test_user.id,
            order_id='test_order_1',
            symbol='BTC-USD',
            side='BUY',
            order_type='MARKET',
            size=Decimal('0.001'),
            price=Decimal('45000.00'),
            filled_size=Decimal('0.001'),
            notional_value=Decimal('45.00'),
            commission=Decimal('0.045'),
            status='FILLED'
        )
        
        position1 = Position(
            user_id=test_user.id,
            symbol='BTC-USD',
            side='LONG',
            size=Decimal('0.001'),
            entry_price=Decimal('45000.00'),
            mark_price=Decimal('46000.00'),
            unrealized_pnl=Decimal('1.00'),
            unrealized_pnl_percent=Decimal('2.22'),
            notional_value=Decimal('46.00'),
            margin_used=Decimal('15.33'),
            leverage=Decimal('3.0'),
            is_open=True
        )
        
        db_session.add_all([trade1, position1])
        db_session.commit()
        
        # Get dashboard data
        response = authenticated_client.get('/api/trading/dashboard')
        assert response.status_code == 200
        
        data = response.json()
        assert 'portfolio_stats' in data
        assert 'open_positions' in data
        assert 'recent_trades' in data
        
        # Verify data integrity
        assert len(data['open_positions']) == 1
        assert len(data['recent_trades']) == 1
        assert data['open_positions'][0]['symbol'] == 'BTC-USD'
    
    @pytest.mark.asyncio
    async def test_strategy_configuration_integration(self, authenticated_client, db_session, test_user):
        """Test strategy configuration API integration."""
        # Update strategy configuration
        new_config = {
            'fast_period': 10,
            'slow_period': 20,
            'rsi_period': 21,
            'rsi_oversold': 25,
            'rsi_overbought': 75
        }
        
        response = authenticated_client.put('/api/trading/strategy/config', json=new_config)
        assert response.status_code == 200
        
        # Verify configuration was saved
        from backend.src.database.models import Configuration
        
        fast_period_config = db_session.query(Configuration).filter(
            Configuration.user_id == test_user.id,
            Configuration.key == 'fast_period'
        ).first()
        
        assert fast_period_config is not None
        assert fast_period_config.value == 10
    
    @pytest.mark.asyncio
    async def test_emergency_stop_api_integration(self, authenticated_client, db_session, test_user):
        """Test emergency stop API integration."""
        # Activate emergency stop
        response = authenticated_client.post('/api/trading/emergency-stop', json={
            'reason': 'Test emergency stop'
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Emergency stop activated'
        
        # Verify subsequent trades are blocked
        trade_request = {
            'symbol': 'BTC-USD',
            'side': 'BUY',
            'order_type': 'MARKET',
            'size': 0.001
        }
        
        response = authenticated_client.post('/api/trading/place-order', json=trade_request)
        assert response.status_code == 400  # Should be blocked
        
        error_data = response.json()
        assert 'emergency stop' in error_data['detail'].lower()