"""
Mock Wallet Implementation for Backtesting

Provides realistic portfolio simulation with position management,
balance tracking, and trading execution for backtesting scenarios.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a trading position in the mock wallet"""
    symbol: str
    size: Decimal  # Positive for long, negative for short
    entry_price: Decimal
    entry_timestamp: datetime
    unrealized_pnl: Decimal = Decimal('0')

    def calculate_pnl(self, current_price: Decimal) -> Decimal:
        """Calculate unrealized P&L for this position"""
        if self.size == 0:
            return Decimal('0')

        price_diff = current_price - self.entry_price
        pnl = self.size * price_diff
        self.unrealized_pnl = pnl.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return self.unrealized_pnl


@dataclass
class Trade:
    """Represents a completed trade in the mock wallet"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ''
    side: str = ''  # 'BUY' or 'SELL'
    size: Decimal = Decimal('0')
    price: Decimal = Decimal('0')
    commission: Decimal = Decimal('0')
    timestamp: datetime = field(default_factory=datetime.utcnow)
    realized_pnl: Decimal = Decimal('0')


@dataclass
class Portfolio:
    """Portfolio state snapshot for performance tracking"""
    timestamp: datetime
    total_value: Decimal
    cash_balance: Decimal
    positions_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal


class MockWallet:
    """
    Production-grade mock wallet for backtesting with realistic trading simulation

    Features:
    - Position management (long/short)
    - Realistic commission and slippage
    - Portfolio value tracking
    - Trade history with P&L calculation
    - Performance metrics calculation
    """

    def __init__(self, initial_capital: float = 10000.0, commission_rate: float = 0.001):
        self.initial_capital = Decimal(str(initial_capital))
        self.cash_balance = Decimal(str(initial_capital))
        self.commission_rate = Decimal(str(commission_rate))

        # Position and trade tracking
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.portfolio_history: List[Portfolio] = []

        # Performance metrics
        self.total_realized_pnl = Decimal('0')
        self.total_commission_paid = Decimal('0')
        self.peak_portfolio_value = self.initial_capital
        self.max_drawdown = Decimal('0')

        logger.info(f"MockWallet initialized with ${initial_capital:,.2f} capital")

    def execute_trade(self, symbol: str, side: str, size: float, price: float,
                     timestamp: datetime, slippage_rate: float = 0.0001) -> Optional[Trade]:
        """
        Execute a trade with realistic slippage and commission

        Args:
            symbol: Trading symbol (e.g., 'BTC', 'ETH')
            side: 'BUY' or 'SELL'
            size: Position size in base units
            price: Execution price
            timestamp: Trade timestamp
            slippage_rate: Slippage as percentage (0.0001 = 0.01%)

        Returns:
            Trade object if successful, None if insufficient funds
        """
        size_decimal = Decimal(str(size))
        price_decimal = Decimal(str(price))

        # Apply slippage
        if side.upper() == 'BUY':
            execution_price = price_decimal * (Decimal('1') + Decimal(str(slippage_rate)))
        else:
            execution_price = price_decimal * (Decimal('1') - Decimal(str(slippage_rate)))

        # Calculate trade value and commission
        trade_value = size_decimal * execution_price
        commission = trade_value * self.commission_rate
        total_cost = trade_value + commission if side.upper() == 'BUY' else commission

        # Check sufficient funds for buying
        if side.upper() == 'BUY' and self.cash_balance < total_cost:
            logger.warning(f"Insufficient funds for {side} {size} {symbol} @ ${execution_price}")
            return None

        # Check sufficient position for selling
        if side.upper() == 'SELL':
            current_position = self.positions.get(symbol)
            if not current_position or current_position.size < size_decimal:
                logger.warning(f"Insufficient position for {side} {size} {symbol}")
                return None

        # Execute the trade
        realized_pnl = self._update_positions(symbol, side, size_decimal, execution_price)

        # Update cash balance
        if side.upper() == 'BUY':
            self.cash_balance -= total_cost
        else:
            self.cash_balance += (trade_value - commission)

        # Track commission
        self.total_commission_paid += commission

        # Create trade record
        trade = Trade(
            symbol=symbol,
            side=side.upper(),
            size=size_decimal,
            price=execution_price,
            commission=commission,
            timestamp=timestamp,
            realized_pnl=realized_pnl
        )

        self.trade_history.append(trade)
        self.total_realized_pnl += realized_pnl

        logger.info(f"Trade executed: {trade.side} {trade.size} {trade.symbol} @ ${trade.price:.2f}")
        return trade

    def _update_positions(self, symbol: str, side: str, size: Decimal, price: Decimal) -> Decimal:
        """Update position and calculate realized P&L"""
        realized_pnl = Decimal('0')

        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol, Decimal('0'), Decimal('0'), datetime.utcnow())

        position = self.positions[symbol]

        if side.upper() == 'BUY':
            if position.size >= 0:
                # Adding to long position or opening new long
                if position.size == 0:
                    position.entry_price = price
                    position.entry_timestamp = datetime.utcnow()
                else:
                    # Average entry price for additional buys
                    total_value = (position.size * position.entry_price) + (size * price)
                    position.entry_price = total_value / (position.size + size)

                position.size += size
            else:
                # Covering short position
                if size >= abs(position.size):
                    # Fully closing short and potentially opening long
                    realized_pnl = abs(position.size) * (position.entry_price - price)
                    remaining_size = size - abs(position.size)
                    position.size = remaining_size
                    position.entry_price = price if remaining_size > 0 else Decimal('0')
                else:
                    # Partially closing short
                    realized_pnl = size * (position.entry_price - price)
                    position.size += size  # Adding to negative (reducing short)

        else:  # SELL
            if position.size <= 0:
                # Adding to short position or opening new short
                if position.size == 0:
                    position.entry_price = price
                    position.entry_timestamp = datetime.utcnow()
                    position.size = -size
                else:
                    # Average entry price for additional shorts
                    total_value = (abs(position.size) * position.entry_price) + (size * price)
                    position.entry_price = total_value / (abs(position.size) + size)
                    position.size -= size
            else:
                # Closing long position
                if size >= position.size:
                    # Fully closing long and potentially opening short
                    realized_pnl = position.size * (price - position.entry_price)
                    remaining_size = size - position.size
                    position.size = -remaining_size
                    position.entry_price = price if remaining_size > 0 else Decimal('0')
                else:
                    # Partially closing long
                    realized_pnl = size * (price - position.entry_price)
                    position.size -= size

        return realized_pnl

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> Decimal:
        """Calculate total portfolio value including positions"""
        positions_value = Decimal('0')
        unrealized_pnl = Decimal('0')

        for symbol, position in self.positions.items():
            if position.size != 0 and symbol in current_prices:
                current_price = Decimal(str(current_prices[symbol]))
                position_value = abs(position.size) * current_price
                positions_value += position_value
                unrealized_pnl += position.calculate_pnl(current_price)

        total_value = self.cash_balance + positions_value

        # Update drawdown tracking
        if total_value > self.peak_portfolio_value:
            self.peak_portfolio_value = total_value
        else:
            current_drawdown = (self.peak_portfolio_value - total_value) / self.peak_portfolio_value
            if current_drawdown > self.max_drawdown:
                self.max_drawdown = current_drawdown

        return total_value

    def record_portfolio_snapshot(self, current_prices: Dict[str, float], timestamp: datetime):
        """Record portfolio state for performance tracking"""
        total_value = self.get_portfolio_value(current_prices)

        positions_value = Decimal('0')
        unrealized_pnl = Decimal('0')

        for symbol, position in self.positions.items():
            if position.size != 0 and symbol in current_prices:
                current_price = Decimal(str(current_prices[symbol]))
                positions_value += abs(position.size) * current_price
                unrealized_pnl += position.calculate_pnl(current_price)

        snapshot = Portfolio(
            timestamp=timestamp,
            total_value=total_value,
            cash_balance=self.cash_balance,
            positions_value=positions_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=self.total_realized_pnl
        )

        self.portfolio_history.append(snapshot)

    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance metrics"""
        if not self.portfolio_history:
            return {"error": "No portfolio history available"}

        final_value = self.portfolio_history[-1].total_value
        total_return = final_value - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100

        # Calculate additional metrics
        winning_trades = len([t for t in self.trade_history if t.realized_pnl > 0])
        total_trades = len(self.trade_history)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            'initial_capital': float(self.initial_capital),
            'final_value': float(final_value),
            'total_return': float(total_return),
            'total_return_pct': float(total_return_pct),
            'max_drawdown_pct': float(self.max_drawdown * 100),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'total_commission_paid': float(self.total_commission_paid),
            'realized_pnl': float(self.total_realized_pnl),
            'current_positions': len([p for p in self.positions.values() if p.size != 0])
        }

    def reset(self, initial_capital: float = None):
        """Reset wallet for new backtest"""
        if initial_capital:
            self.initial_capital = Decimal(str(initial_capital))

        self.cash_balance = self.initial_capital
        self.positions.clear()
        self.trade_history.clear()
        self.portfolio_history.clear()
        self.total_realized_pnl = Decimal('0')
        self.total_commission_paid = Decimal('0')
        self.peak_portfolio_value = self.initial_capital
        self.max_drawdown = Decimal('0')

        logger.info(f"MockWallet reset with ${float(self.initial_capital):,.2f} capital")