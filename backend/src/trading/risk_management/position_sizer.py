"""
Position Sizing for Trading Bot
Calculates optimal position sizes with account equity-based sizing, leverage limits,
correlation awareness, and available margin checks.
"""

import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog

from src.config import get_config
from src.trading.strategies.base import Signal

logger = structlog.get_logger(__name__)


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    side: str  # BUY or SELL
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    margin_used: float
    leverage: float
    timestamp: float
    
    def get_value(self) -> float:
        """Calculate position value"""
        return self.size * self.entry_price
    
    def get_pnl_pct(self) -> float:
        """Calculate P&L percentage"""
        if self.entry_price == 0:
            return 0.0
        
        if self.side == "BUY":
            return (self.current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - self.current_price) / self.entry_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "size": self.size,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "margin_used": self.margin_used,
            "leverage": self.leverage,
            "timestamp": self.timestamp,
            "position_value": self.get_value(),
            "pnl_pct": self.get_pnl_pct()
        }


@dataclass
class PositionSizeResult:
    """Result of position size calculation"""
    symbol: str
    recommended_size: float
    max_allowed_size: float
    risk_adjusted_size: float
    leverage: float
    margin_required: float
    risk_pct: float
    reasons: List[str]
    approved: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "symbol": self.symbol,
            "recommended_size": self.recommended_size,
            "max_allowed_size": self.max_allowed_size,
            "risk_adjusted_size": self.risk_adjusted_size,
            "leverage": self.leverage,
            "margin_required": self.margin_required,
            "risk_pct": self.risk_pct,
            "reasons": self.reasons,
            "approved": self.approved
        }


class CorrelationMatrix:
    """Manage correlation calculations between trading pairs"""
    
    def __init__(self, lookback_periods: int = 50):
        self.lookback_periods = lookback_periods
        self.price_history: Dict[str, List[float]] = {}
        self.correlations: Dict[Tuple[str, str], float] = {}
        self.last_update = 0.0
        
    def update_price(self, symbol: str, price: float) -> None:
        """Update price history for symbol"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(price)
        
        # Keep only lookback periods
        if len(self.price_history[symbol]) > self.lookback_periods:
            self.price_history[symbol] = self.price_history[symbol][-self.lookback_periods:]
    
    def calculate_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Calculate correlation between two symbols"""
        if (symbol1 not in self.price_history or 
            symbol2 not in self.price_history):
            return None
        
        prices1 = self.price_history[symbol1]
        prices2 = self.price_history[symbol2]
        
        if len(prices1) < 10 or len(prices2) < 10:
            return None
        
        # Use same length for both series
        min_length = min(len(prices1), len(prices2))
        prices1 = prices1[-min_length:]
        prices2 = prices2[-min_length:]
        
        # Calculate returns
        returns1 = [prices1[i] / prices1[i-1] - 1 for i in range(1, len(prices1))]
        returns2 = [prices2[i] / prices2[i-1] - 1 for i in range(1, len(prices2))]
        
        if not returns1 or not returns2:
            return None
        
        # Calculate correlation coefficient
        n = len(returns1)
        mean1 = sum(returns1) / n
        mean2 = sum(returns2) / n
        
        numerator = sum((returns1[i] - mean1) * (returns2[i] - mean2) for i in range(n))
        
        sum_sq1 = sum((returns1[i] - mean1) ** 2 for i in range(n))
        sum_sq2 = sum((returns2[i] - mean2) ** 2 for i in range(n))
        
        denominator = math.sqrt(sum_sq1 * sum_sq2)
        
        if denominator == 0:
            return None
        
        correlation = numerator / denominator
        
        # Cache the result
        self.correlations[(symbol1, symbol2)] = correlation
        self.correlations[(symbol2, symbol1)] = correlation
        
        return correlation
    
    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Get cached correlation or calculate if needed"""
        key = (symbol1, symbol2) if symbol1 < symbol2 else (symbol2, symbol1)
        return self.correlations.get(key)
    
    def get_portfolio_correlations(self, positions: List[Position]) -> Dict[str, Dict[str, float]]:
        """Get correlation matrix for current positions"""
        symbols = [pos.symbol for pos in positions]
        correlations = {}
        
        for symbol1 in symbols:
            correlations[symbol1] = {}
            for symbol2 in symbols:
                if symbol1 == symbol2:
                    correlations[symbol1][symbol2] = 1.0
                else:
                    corr = self.calculate_correlation(symbol1, symbol2)
                    correlations[symbol1][symbol2] = corr if corr is not None else 0.0
        
        return correlations


class PositionSizer:
    """
    Position sizing engine with:
    - Account equity-based sizing
    - Maximum leverage limits
    - Correlation-aware sizing
    - Available margin checks
    - Risk budget allocation
    - Dynamic risk adjustment
    """
    
    def __init__(self):
        self.config = get_config()
        self.correlation_matrix = CorrelationMatrix()
        
        # Risk parameters from config
        self.max_position_size_pct = self.config.max_position_size_pct
        self.max_leverage = self.config.max_leverage
        self.max_correlation = self.config.max_correlation
        
        # Internal settings
        self.min_position_size = 10.0  # Minimum position size in USD
        self.max_portfolio_risk = 0.1  # Maximum 10% of portfolio at risk
        
        logger.info("Position sizer initialized",
                   max_position_size_pct=self.max_position_size_pct,
                   max_leverage=self.max_leverage,
                   max_correlation=self.max_correlation)
    
    async def calculate_size(
        self, 
        symbol: str, 
        signal: Signal, 
        account_equity: float,
        current_price: float,
        existing_positions: List[Position],
        available_margin: float
    ) -> PositionSizeResult:
        """
        Calculate optimal position size with all risk checks
        
        Args:
            symbol: Trading symbol
            signal: Trading signal with strength and confidence
            account_equity: Current account equity
            current_price: Current market price
            existing_positions: List of existing positions
            available_margin: Available margin for new positions
            
        Returns:
            PositionSizeResult with sizing decision and reasoning
        """
        reasons = []
        
        try:
            # 1. Base position sizing
            base_size = self._calculate_base_size(
                account_equity, signal, current_price
            )
            reasons.append(f"Base size calculated: ${base_size:.2f}")
            
            # 2. Apply leverage constraints
            leveraged_size = self._apply_leverage_constraints(
                base_size, current_price, signal
            )
            reasons.append(f"After leverage constraints: ${leveraged_size:.2f}")
            
            # 3. Check margin requirements
            margin_adjusted_size = self._apply_margin_constraints(
                leveraged_size, current_price, available_margin
            )
            if margin_adjusted_size < leveraged_size:
                reasons.append(f"Reduced for margin: ${margin_adjusted_size:.2f}")
            
            # 4. Apply correlation-based adjustments
            correlation_adjusted_size = await self._apply_correlation_constraints(
                symbol, margin_adjusted_size, existing_positions
            )
            if correlation_adjusted_size < margin_adjusted_size:
                reasons.append(f"Reduced for correlation: ${correlation_adjusted_size:.2f}")
            
            # 5. Portfolio risk budget check
            risk_adjusted_size = self._apply_portfolio_risk_constraints(
                correlation_adjusted_size, account_equity, existing_positions
            )
            if risk_adjusted_size < correlation_adjusted_size:
                reasons.append(f"Reduced for portfolio risk: ${risk_adjusted_size:.2f}")
            
            # 6. Minimum size check
            final_size = max(risk_adjusted_size, 0)
            
            # Calculate metrics for the final size
            leverage_used = self._calculate_leverage(final_size, current_price)
            margin_required = self._calculate_margin_required(final_size, current_price)
            risk_pct = (final_size / account_equity) if account_equity > 0 else 0
            
            # Determine if position is approved
            approved = (
                final_size >= self.min_position_size and
                margin_required <= available_margin and
                leverage_used <= self.max_leverage
            )
            
            if not approved:
                if final_size < self.min_position_size:
                    reasons.append(f"Below minimum size (${self.min_position_size})")
                if margin_required > available_margin:
                    reasons.append(f"Insufficient margin (need ${margin_required:.2f}, have ${available_margin:.2f})")
                if leverage_used > self.max_leverage:
                    reasons.append(f"Leverage too high ({leverage_used:.1f}x > {self.max_leverage}x)")
            
            result = PositionSizeResult(
                symbol=symbol,
                recommended_size=final_size,
                max_allowed_size=base_size,
                risk_adjusted_size=final_size,
                leverage=leverage_used,
                margin_required=margin_required,
                risk_pct=risk_pct,
                reasons=reasons,
                approved=approved
            )
            
            logger.info("Position size calculated",
                       symbol=symbol,
                       size=final_size,
                       leverage=leverage_used,
                       risk_pct=risk_pct * 100,
                       approved=approved)
            
            return result
            
        except Exception as e:
            logger.error("Error calculating position size",
                        symbol=symbol,
                        error=str(e))
            
            return PositionSizeResult(
                symbol=symbol,
                recommended_size=0.0,
                max_allowed_size=0.0,
                risk_adjusted_size=0.0,
                leverage=0.0,
                margin_required=0.0,
                risk_pct=0.0,
                reasons=[f"Error in calculation: {str(e)}"],
                approved=False
            )
    
    def _calculate_base_size(self, account_equity: float, signal: Signal, current_price: float) -> float:
        """Calculate base position size from equity and signal strength"""
        # Base allocation as percentage of equity
        base_allocation = account_equity * self.max_position_size_pct
        
        # Adjust based on signal strength and confidence
        signal_factor = (signal.strength + signal.confidence) / 2.0
        
        # Scale the position size
        position_value = base_allocation * signal_factor
        
        return position_value
    
    def _apply_leverage_constraints(self, position_value: float, current_price: float, signal: Signal) -> float:
        """Apply maximum leverage constraints"""
        # Calculate position size at maximum leverage
        max_leveraged_value = position_value * self.max_leverage
        
        # For stronger signals, allow more leverage utilization
        leverage_utilization = 0.5 + (signal.strength * 0.5)  # 50% to 100% utilization
        
        leveraged_value = position_value * (1 + (self.max_leverage - 1) * leverage_utilization)
        
        return min(leveraged_value, max_leveraged_value)
    
    def _apply_margin_constraints(self, position_value: float, current_price: float, available_margin: float) -> float:
        """Ensure position doesn't exceed available margin"""
        margin_required = self._calculate_margin_required(position_value, current_price)
        
        if margin_required > available_margin:
            # Scale down position to fit available margin
            scaling_factor = available_margin / margin_required
            return position_value * scaling_factor * 0.95  # 5% buffer
        
        return position_value
    
    async def _apply_correlation_constraints(
        self, 
        symbol: str, 
        position_value: float, 
        existing_positions: List[Position]
    ) -> float:
        """Reduce position size based on correlation with existing positions"""
        if not existing_positions:
            return position_value
        
        # Update correlation matrix with latest prices
        for position in existing_positions:
            self.correlation_matrix.update_price(position.symbol, position.current_price)
        
        # Calculate maximum correlation with existing positions
        max_correlation = 0.0
        for position in existing_positions:
            correlation = self.correlation_matrix.calculate_correlation(symbol, position.symbol)
            if correlation and abs(correlation) > abs(max_correlation):
                max_correlation = correlation
        
        # If correlation exceeds threshold, reduce position size
        if abs(max_correlation) > self.max_correlation:
            reduction_factor = 1 - (abs(max_correlation) - self.max_correlation) / (1 - self.max_correlation)
            reduction_factor = max(0.1, reduction_factor)  # Don't reduce more than 90%
            return position_value * reduction_factor
        
        return position_value
    
    def _apply_portfolio_risk_constraints(
        self, 
        position_value: float, 
        account_equity: float, 
        existing_positions: List[Position]
    ) -> float:
        """Ensure total portfolio risk doesn't exceed limits"""
        # Calculate current portfolio risk
        current_risk = sum(abs(pos.get_value()) for pos in existing_positions)
        current_risk_pct = current_risk / account_equity if account_equity > 0 else 0
        
        # Check if adding this position would exceed portfolio risk limit
        new_total_risk = current_risk + position_value
        new_risk_pct = new_total_risk / account_equity if account_equity > 0 else 0
        
        if new_risk_pct > self.max_portfolio_risk:
            # Reduce position to stay within portfolio risk limit
            max_additional_risk = (self.max_portfolio_risk * account_equity) - current_risk
            return max(0, max_additional_risk * 0.95)  # 5% buffer
        
        return position_value
    
    def _calculate_leverage(self, position_value: float, current_price: float) -> float:
        """Calculate leverage for a position"""
        if position_value == 0:
            return 1.0
        
        # For simplicity, assuming 1:1 leverage for now
        # In real implementation, this would depend on the specific market and margin requirements
        return min(self.max_leverage, position_value / (position_value / self.max_leverage))
    
    def _calculate_margin_required(self, position_value: float, current_price: float) -> float:
        """Calculate margin required for position"""
        leverage = self._calculate_leverage(position_value, current_price)
        return position_value / leverage
    
    def check_risk_limits(self, position: Position, account_equity: float) -> Dict[str, bool]:
        """
        Validate position against all risk limits
        
        Args:
            position: Proposed position
            account_equity: Current account equity
            
        Returns:
            Dict of limit checks with boolean results
        """
        checks = {}
        
        # Position size limit
        position_pct = position.get_value() / account_equity if account_equity > 0 else 0
        checks["position_size_limit"] = position_pct <= self.max_position_size_pct
        
        # Leverage limit
        checks["leverage_limit"] = position.leverage <= self.max_leverage
        
        # Minimum size
        checks["minimum_size"] = position.get_value() >= self.min_position_size
        
        # Margin requirement (simplified)
        margin_ratio = position.margin_used / account_equity if account_equity > 0 else 1
        checks["margin_limit"] = margin_ratio <= 0.8  # Max 80% margin utilization
        
        return checks
    
    def update_price_for_correlation(self, symbol: str, price: float) -> None:
        """Update price in correlation matrix"""
        self.correlation_matrix.update_price(symbol, price)
    
    def get_correlation_matrix(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """Get correlation matrix for given symbols"""
        correlations = {}
        
        for symbol1 in symbols:
            correlations[symbol1] = {}
            for symbol2 in symbols:
                if symbol1 == symbol2:
                    correlations[symbol1][symbol2] = 1.0
                else:
                    corr = self.correlation_matrix.calculate_correlation(symbol1, symbol2)
                    correlations[symbol1][symbol2] = corr if corr is not None else 0.0
        
        return correlations
    
    def get_position_limits(self, account_equity: float) -> Dict[str, float]:
        """Get current position limits based on account equity"""
        return {
            "max_position_value": account_equity * self.max_position_size_pct,
            "max_portfolio_risk": account_equity * self.max_portfolio_risk,
            "min_position_value": self.min_position_size,
            "max_leverage": self.max_leverage,
            "max_correlation": self.max_correlation
        }
    
    def get_sizing_statistics(self) -> Dict[str, Any]:
        """Get position sizing statistics"""
        return {
            "config": {
                "max_position_size_pct": self.max_position_size_pct,
                "max_leverage": self.max_leverage,
                "max_correlation": self.max_correlation,
                "max_portfolio_risk": self.max_portfolio_risk,
                "min_position_size": self.min_position_size
            },
            "correlation_symbols": len(self.correlation_matrix.price_history),
            "cached_correlations": len(self.correlation_matrix.correlations)
        }