"""
Base Strategy Interface
Defines the common interface and functionality for all trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import structlog

from src.trading.market_data.candles import Candle

logger = structlog.get_logger(__name__)


class SignalType(str, Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class StrategyState(str, Enum):
    """Strategy execution states"""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


@dataclass
class Signal:
    """Trading signal with metadata"""
    symbol: str
    signal_type: SignalType
    strength: float  # Signal strength from 0.0 to 1.0
    timestamp: float
    price: float
    strategy_name: str
    
    # Additional signal metadata
    confidence: float = 0.0  # Confidence level 0.0 to 1.0
    reasons: List[str] = None  # Reasons for the signal
    indicators: Dict[str, float] = None  # Indicator values at signal time
    
    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []
        if self.indicators is None:
            self.indicators = {}
        
        # Validate strength and confidence
        self.strength = max(0.0, min(1.0, self.strength))
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    def is_buy_signal(self) -> bool:
        """Check if signal is a buy signal"""
        return self.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]
    
    def is_sell_signal(self) -> bool:
        """Check if signal is a sell signal"""
        return self.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]
    
    def is_strong_signal(self) -> bool:
        """Check if signal is strong (strong buy or strong sell)"""
        return self.signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary"""
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "strength": self.strength,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "price": self.price,
            "strategy_name": self.strategy_name,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "indicators": self.indicators
        }


@dataclass
class StrategyMetrics:
    """Strategy performance metrics"""
    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    strong_signals: int = 0
    
    # Performance tracking
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    
    # Signal accuracy
    correct_signals: int = 0
    false_signals: int = 0
    
    # Timing metrics
    average_signal_strength: float = 0.0
    average_confidence: float = 0.0
    last_signal_time: Optional[float] = None
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100.0
    
    def get_signal_accuracy(self) -> float:
        """Calculate signal accuracy percentage"""
        total_evaluated = self.correct_signals + self.false_signals
        if total_evaluated == 0:
            return 0.0
        return (self.correct_signals / total_evaluated) * 100.0
    
    def get_profit_factor(self) -> float:
        """Calculate profit factor (gross profits / gross losses)"""
        # This would need actual trade P&L data to implement properly
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_signals": self.total_signals,
            "buy_signals": self.buy_signals,
            "sell_signals": self.sell_signals,
            "strong_signals": self.strong_signals,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_pnl": self.total_pnl,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.get_win_rate(),
            "signal_accuracy": self.get_signal_accuracy(),
            "average_signal_strength": self.average_signal_strength,
            "average_confidence": self.average_confidence,
            "last_signal_time": self.last_signal_time
        }


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    
    All strategies must implement the analyze method and can optionally
    override other lifecycle methods.
    """
    
    def __init__(self, name: str, symbols: List[str], config: Dict[str, Any] = None):
        self.name = name
        self.symbols = symbols
        self.config = config or {}
        
        # Strategy state
        self.state = StrategyState.ACTIVE
        self.metrics = StrategyMetrics()
        
        # Data storage
        self.historical_data: Dict[str, List[Candle]] = {symbol: [] for symbol in symbols}
        self.latest_signals: Dict[str, Signal] = {}
        
        # Configuration validation
        self._validate_config()
        
        logger.info("Strategy initialized", 
                   name=self.name, 
                   symbols=self.symbols,
                   config=self.config)
    
    @abstractmethod
    async def analyze(self, symbol: str, candles: List[Candle]) -> Optional[Signal]:
        """
        Analyze market data and generate trading signal
        
        Args:
            symbol: Trading symbol to analyze
            candles: Historical candle data (most recent first)
            
        Returns:
            Signal if conditions are met, None otherwise
        """
        pass
    
    def _validate_config(self) -> None:
        """Validate strategy configuration - override in subclasses"""
        pass
    
    async def update_data(self, symbol: str, candles: List[Candle]) -> None:
        """
        Update historical data for symbol
        
        Args:
            symbol: Symbol to update
            candles: New candle data
        """
        if symbol not in self.symbols:
            logger.warning("Received data for untracked symbol", 
                         strategy=self.name, symbol=symbol)
            return
        
        # Store historical data (keep limited history for performance)
        max_history = self.config.get("max_history_candles", 200)
        self.historical_data[symbol] = candles[-max_history:]
    
    async def generate_signal(self, symbol: str, candles: List[Candle]) -> Optional[Signal]:
        """
        Generate trading signal with full processing pipeline
        
        Args:
            symbol: Symbol to analyze
            candles: Candle data for analysis
            
        Returns:
            Generated signal or None
        """
        if self.state != StrategyState.ACTIVE:
            return None
        
        try:
            # Update historical data
            await self.update_data(symbol, candles)
            
            # Run strategy analysis
            signal = await self.analyze(symbol, candles)
            
            if signal:
                # Update metrics
                self._update_signal_metrics(signal)
                
                # Store latest signal
                self.latest_signals[symbol] = signal
                
                logger.info("Signal generated",
                           strategy=self.name,
                           symbol=symbol,
                           signal_type=signal.signal_type,
                           strength=signal.strength,
                           confidence=signal.confidence)
            
            return signal
            
        except Exception as e:
            logger.error("Error generating signal",
                        strategy=self.name,
                        symbol=symbol,
                        error=str(e))
            self.state = StrategyState.ERROR
            return None
    
    def _update_signal_metrics(self, signal: Signal) -> None:
        """Update strategy metrics with new signal"""
        self.metrics.total_signals += 1
        self.metrics.last_signal_time = signal.timestamp
        
        if signal.is_buy_signal():
            self.metrics.buy_signals += 1
        elif signal.is_sell_signal():
            self.metrics.sell_signals += 1
        
        if signal.is_strong_signal():
            self.metrics.strong_signals += 1
        
        # Update rolling averages
        total = self.metrics.total_signals
        self.metrics.average_signal_strength = (
            (self.metrics.average_signal_strength * (total - 1) + signal.strength) / total
        )
        self.metrics.average_confidence = (
            (self.metrics.average_confidence * (total - 1) + signal.confidence) / total
        )
    
    async def should_exit_position(self, symbol: str, current_price: float, entry_price: float, side: str) -> bool:
        """
        Determine if current position should be exited
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            entry_price: Position entry price
            side: Position side (BUY/SELL)
            
        Returns:
            True if position should be exited
        """
        # Default implementation - override in subclasses for custom logic
        return False
    
    def calculate_position_size(self, signal: Signal, account_equity: float, max_position_pct: float = 0.02) -> float:
        """
        Calculate position size based on signal strength and risk parameters
        
        Args:
            signal: Trading signal
            account_equity: Current account equity
            max_position_pct: Maximum position size as percentage of equity
            
        Returns:
            Calculated position size
        """
        # Base position size
        base_size = account_equity * max_position_pct
        
        # Scale by signal strength and confidence
        strength_factor = signal.strength
        confidence_factor = signal.confidence
        
        # Combined scaling factor
        scaling_factor = (strength_factor + confidence_factor) / 2.0
        
        # Apply scaling
        position_size = base_size * scaling_factor
        
        # Minimum position size check
        min_size = self.config.get("min_position_size", account_equity * 0.001)
        position_size = max(position_size, min_size)
        
        return position_size
    
    def get_latest_signal(self, symbol: str) -> Optional[Signal]:
        """Get the latest signal for symbol"""
        return self.latest_signals.get(symbol)
    
    def get_metrics(self) -> StrategyMetrics:
        """Get strategy performance metrics"""
        return self.metrics
    
    def get_state(self) -> StrategyState:
        """Get current strategy state"""
        return self.state
    
    def pause(self) -> None:
        """Pause strategy execution"""
        self.state = StrategyState.PAUSED
        logger.info("Strategy paused", name=self.name)
    
    def resume(self) -> None:
        """Resume strategy execution"""
        self.state = StrategyState.ACTIVE
        logger.info("Strategy resumed", name=self.name)
    
    def stop(self) -> None:
        """Stop strategy execution"""
        self.state = StrategyState.STOPPED
        logger.info("Strategy stopped", name=self.name)
    
    def reset_metrics(self) -> None:
        """Reset strategy metrics"""
        self.metrics = StrategyMetrics()
        logger.info("Strategy metrics reset", name=self.name)
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update strategy configuration
        
        Args:
            new_config: New configuration parameters
            
        Returns:
            True if update was successful
        """
        try:
            old_config = self.config.copy()
            self.config.update(new_config)
            
            # Validate new configuration
            self._validate_config()
            
            logger.info("Strategy configuration updated",
                       name=self.name,
                       old_config=old_config,
                       new_config=self.config)
            return True
            
        except Exception as e:
            # Revert to old configuration on validation failure
            self.config = old_config
            logger.error("Failed to update strategy configuration",
                        name=self.name,
                        error=str(e))
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current strategy configuration"""
        return self.config.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy to dictionary representation"""
        return {
            "name": self.name,
            "symbols": self.symbols,
            "state": self.state.value,
            "config": self.config,
            "metrics": self.metrics.to_dict(),
            "latest_signals": {
                symbol: signal.to_dict() 
                for symbol, signal in self.latest_signals.items()
            }
        }