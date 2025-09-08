"""
Stop Loss Manager for Trading Bot
Manages stop-loss and take-profit orders with automatic placement, trailing stops,
and emergency liquidation logic.
"""

import time
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import structlog

from src.config import get_config
from src.trading.risk_management.position_sizer import Position

logger = structlog.get_logger(__name__)


@dataclass
class StopLossOrder:
    """Represents a stop-loss order"""
    position_symbol: str
    stop_price: float
    stop_type: str  # "STOP_LOSS", "TRAILING_STOP", "TAKE_PROFIT"
    order_id: Optional[str] = None
    is_trailing: bool = False
    trail_amount: float = 0.0
    highest_price: float = 0.0  # For trailing stops
    lowest_price: float = float('inf')  # For trailing stops
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    triggered: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stop loss order to dictionary"""
        return {
            "position_symbol": self.position_symbol,
            "stop_price": self.stop_price,
            "stop_type": self.stop_type,
            "order_id": self.order_id,
            "is_trailing": self.is_trailing,
            "trail_amount": self.trail_amount,
            "highest_price": self.highest_price,
            "lowest_price": self.lowest_price,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "triggered": self.triggered
        }


@dataclass
class RiskReward:
    """Risk/reward calculation"""
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_amount": self.risk_amount,
            "reward_amount": self.reward_amount,
            "risk_reward_ratio": self.risk_reward_ratio
        }


class StopLossManager:
    """
    Comprehensive stop-loss management with:
    - Automatic stop placement
    - Trailing stop functionality
    - Risk/reward ratio enforcement
    - Emergency liquidation logic
    - Multiple stop types
    - Dynamic adjustment based on volatility
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Risk parameters from config
        self.default_stop_loss_pct = self.config.stop_loss_pct
        self.take_profit_ratio = self.config.take_profit_ratio
        self.enable_trailing_stops = self.config.enable_trailing_stops
        self.trailing_stop_trigger_pct = self.config.trailing_stop_trigger_pct
        
        # Internal tracking
        self.stop_orders: Dict[str, StopLossOrder] = {}  # symbol -> stop order
        self.position_states: Dict[str, Dict[str, Any]] = {}  # symbol -> state
        
        # Statistics
        self.stats = {
            "stops_created": 0,
            "stops_triggered": 0,
            "trailing_stops_activated": 0,
            "emergency_stops": 0,
            "profit_targets_hit": 0,
            "total_risk_saved": 0.0,
            "total_profit_captured": 0.0
        }
        
        logger.info("Stop loss manager initialized",
                   stop_loss_pct=self.default_stop_loss_pct * 100,
                   take_profit_ratio=self.take_profit_ratio,
                   trailing_stops=self.enable_trailing_stops)
    
    def calculate_stop_loss(self, entry_price: float, side: str, volatility_multiplier: float = 1.0) -> float:
        """
        Calculate stop-loss level based on entry price and position side
        
        Args:
            entry_price: Position entry price
            side: Position side ("BUY" or "SELL")
            volatility_multiplier: Multiplier to adjust for volatility (default 1.0)
            
        Returns:
            Stop-loss price
        """
        # Base stop loss percentage adjusted for volatility
        stop_pct = self.default_stop_loss_pct * volatility_multiplier
        
        if side.upper() == "BUY":
            # Long position: stop below entry
            stop_price = entry_price * (1 - stop_pct)
        else:
            # Short position: stop above entry
            stop_price = entry_price * (1 + stop_pct)
        
        return stop_price
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float, side: str) -> float:
        """
        Calculate take-profit level based on risk/reward ratio
        
        Args:
            entry_price: Position entry price
            stop_loss: Stop-loss price
            side: Position side ("BUY" or "SELL")
            
        Returns:
            Take-profit price
        """
        # Calculate risk amount
        risk_amount = abs(entry_price - stop_loss)
        
        # Calculate reward amount based on risk/reward ratio
        reward_amount = risk_amount * self.take_profit_ratio
        
        if side.upper() == "BUY":
            # Long position: take profit above entry
            take_profit = entry_price + reward_amount
        else:
            # Short position: take profit below entry  
            take_profit = entry_price - reward_amount
        
        return take_profit
    
    def calculate_risk_reward(self, entry_price: float, stop_loss: float, take_profit: float) -> RiskReward:
        """Calculate complete risk/reward metrics"""
        risk_amount = abs(entry_price - stop_loss)
        reward_amount = abs(take_profit - entry_price)
        
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        
        return RiskReward(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_reward_ratio=risk_reward_ratio
        )
    
    async def create_stop_loss_order(
        self, 
        position: Position, 
        volatility_multiplier: float = 1.0,
        custom_stop_price: Optional[float] = None
    ) -> StopLossOrder:
        """
        Create stop-loss order for position
        
        Args:
            position: Position to protect
            volatility_multiplier: Adjustment for market volatility
            custom_stop_price: Custom stop price (overrides calculation)
            
        Returns:
            Created stop-loss order
        """
        # Calculate or use custom stop price
        if custom_stop_price:
            stop_price = custom_stop_price
        else:
            stop_price = self.calculate_stop_loss(
                position.entry_price, 
                position.side, 
                volatility_multiplier
            )
        
        # Create stop order
        stop_order = StopLossOrder(
            position_symbol=position.symbol,
            stop_price=stop_price,
            stop_type="STOP_LOSS",
            is_trailing=False,
            highest_price=position.current_price if position.side == "BUY" else 0.0,
            lowest_price=position.current_price if position.side == "SELL" else float('inf')
        )
        
        # Store the order
        self.stop_orders[position.symbol] = stop_order
        self.stats["stops_created"] += 1
        
        logger.info("Stop-loss order created",
                   symbol=position.symbol,
                   side=position.side,
                   entry_price=position.entry_price,
                   stop_price=stop_price,
                   risk_pct=(abs(position.entry_price - stop_price) / position.entry_price) * 100)
        
        return stop_order
    
    async def update_trailing_stops(self, positions: List[Position], current_prices: Dict[str, float]) -> List[str]:
        """
        Update trailing stops for profitable positions
        
        Args:
            positions: List of current positions
            current_prices: Current market prices by symbol
            
        Returns:
            List of symbols with updated trailing stops
        """
        updated_symbols = []
        
        for position in positions:
            symbol = position.symbol
            current_price = current_prices.get(symbol, position.current_price)
            
            # Check if position is profitable enough to activate trailing stop
            if not self._should_activate_trailing_stop(position, current_price):
                continue
            
            stop_order = self.stop_orders.get(symbol)
            if not stop_order:
                continue
            
            # Activate trailing stop if not already active
            if not stop_order.is_trailing:
                await self._activate_trailing_stop(position, stop_order, current_price)
                updated_symbols.append(symbol)
                continue
            
            # Update existing trailing stop
            if await self._update_trailing_stop(position, stop_order, current_price):
                updated_symbols.append(symbol)
        
        return updated_symbols
    
    def _should_activate_trailing_stop(self, position: Position, current_price: float) -> bool:
        """Check if position is profitable enough to activate trailing stop"""
        if not self.enable_trailing_stops:
            return False
        
        profit_pct = abs(current_price - position.entry_price) / position.entry_price
        
        if position.side == "BUY":
            # Long position: price should be higher than entry
            return current_price > position.entry_price and profit_pct >= self.trailing_stop_trigger_pct
        else:
            # Short position: price should be lower than entry
            return current_price < position.entry_price and profit_pct >= self.trailing_stop_trigger_pct
    
    async def _activate_trailing_stop(self, position: Position, stop_order: StopLossOrder, current_price: float) -> None:
        """Activate trailing stop for position"""
        stop_order.is_trailing = True
        stop_order.trail_amount = abs(current_price - stop_order.stop_price)
        
        if position.side == "BUY":
            stop_order.highest_price = current_price
            # Update stop to trail behind current price
            stop_order.stop_price = current_price - stop_order.trail_amount
        else:
            stop_order.lowest_price = current_price
            # Update stop to trail behind current price
            stop_order.stop_price = current_price + stop_order.trail_amount
        
        stop_order.last_updated = time.time()
        self.stats["trailing_stops_activated"] += 1
        
        logger.info("Trailing stop activated",
                   symbol=position.symbol,
                   side=position.side,
                   new_stop_price=stop_order.stop_price,
                   trail_amount=stop_order.trail_amount)
    
    async def _update_trailing_stop(self, position: Position, stop_order: StopLossOrder, current_price: float) -> bool:
        """Update trailing stop position"""
        updated = False
        
        if position.side == "BUY":
            # Long position: trail stop up if price moves higher
            if current_price > stop_order.highest_price:
                stop_order.highest_price = current_price
                new_stop_price = current_price - stop_order.trail_amount
                
                if new_stop_price > stop_order.stop_price:
                    stop_order.stop_price = new_stop_price
                    stop_order.last_updated = time.time()
                    updated = True
                    
                    logger.info("Trailing stop updated (long)",
                               symbol=position.symbol,
                               new_stop_price=stop_order.stop_price,
                               current_price=current_price)
        
        else:
            # Short position: trail stop down if price moves lower
            if current_price < stop_order.lowest_price:
                stop_order.lowest_price = current_price
                new_stop_price = current_price + stop_order.trail_amount
                
                if new_stop_price < stop_order.stop_price:
                    stop_order.stop_price = new_stop_price
                    stop_order.last_updated = time.time()
                    updated = True
                    
                    logger.info("Trailing stop updated (short)",
                               symbol=position.symbol,
                               new_stop_price=stop_order.stop_price,
                               current_price=current_price)
        
        return updated
    
    def check_stop_triggers(self, positions: List[Position], current_prices: Dict[str, float]) -> List[Tuple[Position, StopLossOrder]]:
        """
        Check if any stop-loss orders should be triggered
        
        Args:
            positions: List of current positions
            current_prices: Current market prices
            
        Returns:
            List of (position, stop_order) tuples that should be closed
        """
        triggered_stops = []
        
        for position in positions:
            symbol = position.symbol
            current_price = current_prices.get(symbol, position.current_price)
            
            stop_order = self.stop_orders.get(symbol)
            if not stop_order or stop_order.triggered:
                continue
            
            should_trigger = False
            
            if position.side == "BUY":
                # Long position: trigger if price drops below stop
                should_trigger = current_price <= stop_order.stop_price
            else:
                # Short position: trigger if price rises above stop
                should_trigger = current_price >= stop_order.stop_price
            
            if should_trigger:
                stop_order.triggered = True
                stop_order.last_updated = time.time()
                triggered_stops.append((position, stop_order))
                
                # Update statistics
                self.stats["stops_triggered"] += 1
                if stop_order.stop_type == "TAKE_PROFIT":
                    self.stats["profit_targets_hit"] += 1
                
                logger.warning("Stop-loss triggered",
                              symbol=symbol,
                              side=position.side,
                              entry_price=position.entry_price,
                              stop_price=stop_order.stop_price,
                              current_price=current_price,
                              stop_type=stop_order.stop_type)
        
        return triggered_stops
    
    async def create_take_profit_order(self, position: Position) -> Optional[StopLossOrder]:
        """
        Create take-profit order for position
        
        Args:
            position: Position to create take-profit for
            
        Returns:
            Created take-profit order or None
        """
        # Get existing stop-loss to calculate take-profit
        stop_order = self.stop_orders.get(position.symbol)
        if not stop_order:
            logger.warning("Cannot create take-profit without stop-loss",
                          symbol=position.symbol)
            return None
        
        # Calculate take-profit price
        take_profit_price = self.calculate_take_profit(
            position.entry_price,
            stop_order.stop_price,
            position.side
        )
        
        # Create take-profit order (stored separately)
        tp_key = f"{position.symbol}_TP"
        tp_order = StopLossOrder(
            position_symbol=position.symbol,
            stop_price=take_profit_price,
            stop_type="TAKE_PROFIT",
            is_trailing=False
        )
        
        self.stop_orders[tp_key] = tp_order
        
        logger.info("Take-profit order created",
                   symbol=position.symbol,
                   side=position.side,
                   entry_price=position.entry_price,
                   take_profit_price=take_profit_price)
        
        return tp_order
    
    async def emergency_liquidation_check(self, positions: List[Position], account_equity: float) -> List[Position]:
        """
        Check for positions that need emergency liquidation
        
        Args:
            positions: Current positions
            account_equity: Current account equity
            
        Returns:
            List of positions that need immediate liquidation
        """
        emergency_positions = []
        
        for position in positions:
            # Check for extreme losses
            loss_pct = abs(position.get_pnl_pct())
            
            # Emergency liquidation triggers:
            # 1. Single position loss > 5% of account
            # 2. Position loss > 50% of position value
            # 3. Margin call risk
            
            position_loss_vs_account = (abs(position.unrealized_pnl) / account_equity) if account_equity > 0 else 0
            
            if (position_loss_vs_account > 0.05 or  # 5% account loss
                loss_pct > 0.5 or  # 50% position loss  
                position.margin_used / account_equity > 0.9):  # 90% margin used
                
                emergency_positions.append(position)
                self.stats["emergency_stops"] += 1
                
                logger.critical("Emergency liquidation triggered",
                               symbol=position.symbol,
                               loss_pct=loss_pct * 100,
                               account_loss_pct=position_loss_vs_account * 100,
                               margin_ratio=(position.margin_used / account_equity) * 100)
        
        return emergency_positions
    
    def remove_stop_order(self, symbol: str) -> bool:
        """Remove stop order for symbol"""
        if symbol in self.stop_orders:
            del self.stop_orders[symbol]
            return True
        
        # Also check for take-profit order
        tp_key = f"{symbol}_TP"
        if tp_key in self.stop_orders:
            del self.stop_orders[tp_key]
        
        return False
    
    def get_stop_order(self, symbol: str) -> Optional[StopLossOrder]:
        """Get stop order for symbol"""
        return self.stop_orders.get(symbol)
    
    def get_take_profit_order(self, symbol: str) -> Optional[StopLossOrder]:
        """Get take-profit order for symbol"""
        tp_key = f"{symbol}_TP"
        return self.stop_orders.get(tp_key)
    
    def update_stop_price(self, symbol: str, new_stop_price: float) -> bool:
        """Manually update stop price"""
        stop_order = self.stop_orders.get(symbol)
        if not stop_order:
            return False
        
        old_price = stop_order.stop_price
        stop_order.stop_price = new_stop_price
        stop_order.last_updated = time.time()
        
        logger.info("Stop price updated",
                   symbol=symbol,
                   old_price=old_price,
                   new_price=new_stop_price)
        
        return True
    
    def get_all_stops(self) -> Dict[str, StopLossOrder]:
        """Get all active stop orders"""
        return self.stop_orders.copy()
    
    def get_risk_metrics(self, positions: List[Position]) -> Dict[str, Any]:
        """Get risk metrics for current positions"""
        total_risk = 0.0
        total_reward_potential = 0.0
        stops_in_place = 0
        
        for position in positions:
            stop_order = self.stop_orders.get(position.symbol)
            if stop_order:
                stops_in_place += 1
                risk_amount = abs(position.entry_price - stop_order.stop_price) * position.size
                total_risk += risk_amount
                
                # Calculate potential reward if take-profit exists
                tp_order = self.get_take_profit_order(position.symbol)
                if tp_order:
                    reward_amount = abs(tp_order.stop_price - position.entry_price) * position.size
                    total_reward_potential += reward_amount
        
        return {
            "total_positions": len(positions),
            "stops_in_place": stops_in_place,
            "stop_coverage_pct": (stops_in_place / len(positions)) * 100 if positions else 0,
            "total_risk_amount": total_risk,
            "total_reward_potential": total_reward_potential,
            "risk_reward_ratio": total_reward_potential / total_risk if total_risk > 0 else 0,
            "statistics": self.stats
        }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters"""
        self.stats = {
            "stops_created": 0,
            "stops_triggered": 0,
            "trailing_stops_activated": 0,
            "emergency_stops": 0,
            "profit_targets_hit": 0,
            "total_risk_saved": 0.0,
            "total_profit_captured": 0.0
        }
        
        logger.info("Stop-loss manager statistics reset")