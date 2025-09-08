"""Test data factory utilities."""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

from backend.src.database.models import User, Trade, Position, StrategySignal, Alert, Configuration
from backend.src.security.auth import hash_password


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_test_user(**kwargs) -> User:
        """Create a test user with default or custom attributes."""
        defaults = {
            'email': f'test{random.randint(1000, 9999)}@example.com',
            'username': f'testuser{random.randint(1000, 9999)}',
            'hashed_password': hash_password('TestPassword123!'),
            'is_active': True,
            'trading_enabled': True,
            'paper_trading_mode': True,
            'account_balance': Decimal('10000.00'),
            'peak_balance': Decimal('10000.00'),
            'encrypted_api_key': 'encrypted_api_key_test',
            'encrypted_api_secret': 'encrypted_api_secret_test',
            'encrypted_api_passphrase': 'encrypted_passphrase_test'
        }
        defaults.update(kwargs)
        return User(**defaults)
    
    @staticmethod
    def create_test_trade(user_id: int, **kwargs) -> Trade:
        """Create a test trade with default or custom attributes."""
        order_id = f'order_{random.randint(100000, 999999)}'
        defaults = {
            'user_id': user_id,
            'order_id': order_id,
            'symbol': 'BTC-USD',
            'side': random.choice(['BUY', 'SELL']),
            'order_type': 'MARKET',
            'size': Decimal(str(round(random.uniform(0.001, 0.01), 3))),
            'price': Decimal(str(round(random.uniform(40000, 50000), 2))),
            'filled_size': None,  # Will be set to size if not specified
            'notional_value': None,  # Will be calculated
            'commission': None,  # Will be calculated
            'status': 'FILLED',
            'timestamp': datetime.utcnow(),
            'is_paper_trade': True
        }
        defaults.update(kwargs)
        
        # Calculate derived fields if not provided
        if defaults['filled_size'] is None:
            defaults['filled_size'] = defaults['size']
        
        if defaults['notional_value'] is None:
            defaults['notional_value'] = defaults['price'] * defaults['filled_size']
        
        if defaults['commission'] is None:
            defaults['commission'] = defaults['notional_value'] * Decimal('0.001')  # 0.1% commission
        
        return Trade(**defaults)
    
    @staticmethod
    def create_test_position(user_id: int, **kwargs) -> Position:
        """Create a test position with default or custom attributes."""
        defaults = {
            'user_id': user_id,
            'symbol': 'BTC-USD',
            'side': random.choice(['LONG', 'SHORT']),
            'size': Decimal(str(round(random.uniform(0.001, 0.01), 3))),
            'entry_price': Decimal(str(round(random.uniform(40000, 50000), 2))),
            'mark_price': None,  # Will be calculated
            'unrealized_pnl': None,  # Will be calculated
            'unrealized_pnl_percent': None,  # Will be calculated
            'notional_value': None,  # Will be calculated
            'margin_used': None,  # Will be calculated
            'leverage': Decimal('3.0'),
            'is_open': True,
            'opened_at': datetime.utcnow()
        }
        defaults.update(kwargs)
        
        # Calculate derived fields if not provided
        entry_price = defaults['entry_price']
        size = defaults['size']
        
        if defaults['mark_price'] is None:
            # Random mark price within 5% of entry price
            price_change = random.uniform(-0.05, 0.05)
            defaults['mark_price'] = entry_price * (1 + Decimal(str(price_change)))
        
        mark_price = defaults['mark_price']
        
        if defaults['notional_value'] is None:
            defaults['notional_value'] = mark_price * size
        
        if defaults['margin_used'] is None:
            defaults['margin_used'] = defaults['notional_value'] / defaults['leverage']
        
        if defaults['unrealized_pnl'] is None:
            if defaults['side'] == 'LONG':
                defaults['unrealized_pnl'] = (mark_price - entry_price) * size
            else:
                defaults['unrealized_pnl'] = (entry_price - mark_price) * size
        
        if defaults['unrealized_pnl_percent'] is None:
            defaults['unrealized_pnl_percent'] = (defaults['unrealized_pnl'] / (entry_price * size)) * 100
        
        return Position(**defaults)
    
    @staticmethod
    def create_test_strategy_signal(user_id: int, **kwargs) -> StrategySignal:
        """Create a test strategy signal with default or custom attributes."""
        defaults = {
            'user_id': user_id,
            'strategy_name': 'MovingAverageCrossover',
            'symbol': 'BTC-USD',
            'signal_type': random.choice(['BUY', 'SELL', 'HOLD']),
            'strength': Decimal(str(round(random.uniform(0.3, 1.0), 2))),
            'confidence': Decimal(str(round(random.uniform(0.5, 1.0), 2))),
            'price': Decimal(str(round(random.uniform(40000, 50000), 2))),
            'indicators': {
                'ema12': round(random.uniform(40000, 50000), 2),
                'ema26': round(random.uniform(40000, 50000), 2),
                'rsi': round(random.uniform(20, 80), 1)
            },
            'reasoning': 'Test signal generated by factory',
            'timestamp': datetime.utcnow()
        }
        defaults.update(kwargs)
        return StrategySignal(**defaults)
    
    @staticmethod
    def create_test_alert(user_id: int = None, **kwargs) -> Alert:
        """Create a test alert with default or custom attributes."""
        defaults = {
            'user_id': user_id,
            'alert_type': random.choice(['trading', 'system', 'risk']),
            'severity': random.choice(['INFO', 'WARNING', 'ERROR', 'CRITICAL']),
            'title': f'Test Alert {random.randint(1000, 9999)}',
            'message': 'This is a test alert message',
            'symbol': 'BTC-USD' if random.choice([True, False]) else None,
            'strategy_name': 'MovingAverageCrossover' if random.choice([True, False]) else None,
            'metadata': {'test': True, 'value': random.randint(1, 100)},
            'timestamp': datetime.utcnow(),
            'is_acknowledged': False
        }
        defaults.update(kwargs)
        return Alert(**defaults)
    
    @staticmethod
    def create_test_configuration(user_id: int = None, **kwargs) -> Configuration:
        """Create a test configuration with default or custom attributes."""
        defaults = {
            'user_id': user_id,
            'category': random.choice(['strategy', 'risk', 'trading', 'system']),
            'key': f'test_config_{random.randint(1000, 9999)}',
            'value': random.choice([12, 26, 0.02, 'test_value', True]),
            'value_type': 'str',
            'description': 'Test configuration parameter'
        }
        defaults.update(kwargs)
        
        # Set value_type based on value if not specified
        if kwargs.get('value_type') is None:
            value = defaults['value']
            if isinstance(value, int):
                defaults['value_type'] = 'int'
            elif isinstance(value, float):
                defaults['value_type'] = 'float'
            elif isinstance(value, bool):
                defaults['value_type'] = 'bool'
            else:
                defaults['value_type'] = 'str'
        
        return Configuration(**defaults)
    
    @staticmethod
    def create_mock_candle_data(
        symbol: str = 'BTC-USD',
        count: int = 100,
        start_price: float = 45000.0,
        volatility: float = 0.02
    ) -> List[Dict[str, Any]]:
        """Create mock candle data for testing strategies."""
        candles = []
        current_price = start_price
        current_time = datetime.utcnow() - timedelta(hours=count)
        
        for i in range(count):
            # Simulate price movement
            price_change = random.gauss(0, volatility)  # Normal distribution
            current_price *= (1 + price_change)
            current_price = max(current_price, 1.0)  # Ensure positive price
            
            # Generate OHLC data
            open_price = current_price
            high_price = open_price * (1 + abs(random.gauss(0, volatility/2)))
            low_price = open_price * (1 - abs(random.gauss(0, volatility/2)))
            close_price = random.uniform(low_price, high_price)
            
            candle = {
                'timestamp': (current_time + timedelta(hours=i)).isoformat(),
                'symbol': symbol,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(random.uniform(100, 10000), 2)
            }
            candles.append(candle)
            current_price = close_price
        
        return candles
    
    @staticmethod
    def create_trending_candle_data(
        symbol: str = 'BTC-USD',
        count: int = 50,
        start_price: float = 45000.0,
        trend: str = 'up',  # 'up', 'down', or 'sideways'
        volatility: float = 0.01
    ) -> List[Dict[str, Any]]:
        """Create candle data with a specific trend for testing strategies."""
        candles = []
        current_price = start_price
        current_time = datetime.utcnow() - timedelta(hours=count)
        
        # Define trend parameters
        trend_strength = 0.002  # 0.2% per candle
        if trend == 'down':
            trend_strength = -trend_strength
        elif trend == 'sideways':
            trend_strength = 0
        
        for i in range(count):
            # Apply trend
            current_price *= (1 + trend_strength)
            
            # Add random volatility
            price_change = random.gauss(0, volatility)
            current_price *= (1 + price_change)
            current_price = max(current_price, 1.0)
            
            # Generate OHLC
            open_price = current_price
            high_price = open_price * (1 + abs(random.gauss(0, volatility/3)))
            low_price = open_price * (1 - abs(random.gauss(0, volatility/3)))
            close_price = random.uniform(low_price, high_price)
            
            candle = {
                'timestamp': (current_time + timedelta(hours=i)).isoformat(),
                'symbol': symbol,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(random.uniform(500, 5000), 2)
            }
            candles.append(candle)
            current_price = close_price
        
        return candles
    
    @staticmethod
    def create_trade_sequence(
        user_id: int,
        count: int = 10,
        symbol: str = 'BTC-USD',
        profitable_ratio: float = 0.6
    ) -> List[Trade]:
        """Create a sequence of trades with specified profitable ratio."""
        trades = []
        current_time = datetime.utcnow() - timedelta(hours=count)
        
        profitable_count = int(count * profitable_ratio)
        trade_results = ['profit'] * profitable_count + ['loss'] * (count - profitable_count)
        random.shuffle(trade_results)
        
        for i, result in enumerate(trade_results):
            base_price = random.uniform(40000, 50000)
            
            if result == 'profit':
                # Profitable trade
                if random.choice([True, False]):  # BUY trade
                    entry_price = base_price
                    exit_price = base_price * random.uniform(1.005, 1.03)  # 0.5% to 3% profit
                    side = 'BUY'
                else:  # SELL trade
                    entry_price = base_price
                    exit_price = base_price * random.uniform(0.97, 0.995)  # 0.5% to 3% profit
                    side = 'SELL'
            else:
                # Losing trade
                if random.choice([True, False]):  # BUY trade
                    entry_price = base_price
                    exit_price = base_price * random.uniform(0.98, 0.995)  # 0.5% to 2% loss
                    side = 'BUY'
                else:  # SELL trade
                    entry_price = base_price
                    exit_price = base_price * random.uniform(1.005, 1.02)  # 0.5% to 2% loss
                    side = 'SELL'
            
            size = Decimal(str(round(random.uniform(0.001, 0.005), 3)))
            entry_price_decimal = Decimal(str(round(entry_price, 2)))
            
            trade = TestDataFactory.create_test_trade(
                user_id=user_id,
                symbol=symbol,
                side=side,
                size=size,
                price=entry_price_decimal,
                timestamp=current_time + timedelta(hours=i),
                order_id=f'sequence_order_{i}_{random.randint(1000, 9999)}'
            )
            
            trades.append(trade)
        
        return trades
    
    @staticmethod
    def create_portfolio_snapshot(user_id: int) -> Dict[str, Any]:
        """Create a realistic portfolio snapshot for testing."""
        # Create some positions
        positions = [
            TestDataFactory.create_test_position(user_id, symbol='BTC-USD', size=Decimal('0.002')),
            TestDataFactory.create_test_position(user_id, symbol='ETH-USD', size=Decimal('0.05')),
            TestDataFactory.create_test_position(user_id, symbol='SOL-USD', size=Decimal('2.0'))
        ]
        
        # Create recent trades
        recent_trades = TestDataFactory.create_trade_sequence(user_id, count=5)
        
        # Calculate portfolio metrics
        total_notional_value = sum(pos.notional_value for pos in positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        total_margin_used = sum(pos.margin_used for pos in positions)
        
        return {
            'positions': positions,
            'recent_trades': recent_trades,
            'total_notional_value': total_notional_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_margin_used': total_margin_used,
            'number_of_positions': len(positions),
            'account_balance': Decimal('10000.00')
        }