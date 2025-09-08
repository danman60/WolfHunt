"""
Candle Aggregator for dYdX v4
Aggregates trade data into OHLCV candles with multiple timeframes and technical indicators.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
import math
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Trade:
    """Individual trade data"""
    symbol: str
    price: float
    size: float
    side: str  # BUY or SELL
    timestamp: float
    trade_id: Optional[str] = None


@dataclass
class Candle:
    """OHLCV candle data with technical indicators"""
    symbol: str
    timeframe: str
    timestamp: float  # Start time of the candle
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: int = 0
    vwap: float = 0.0  # Volume Weighted Average Price
    
    # Technical indicators (calculated separately)
    ema12: Optional[float] = None
    ema26: Optional[float] = None
    rsi: Optional[float] = None
    
    def __post_init__(self):
        """Validate and normalize candle data"""
        self.open = float(self.open)
        self.high = float(self.high) 
        self.low = float(self.low)
        self.close = float(self.close)
        self.volume = float(self.volume)
        
        # Ensure OHLC consistency
        if self.high < max(self.open, self.close):
            self.high = max(self.open, self.close)
        if self.low > min(self.open, self.close):
            self.low = min(self.open, self.close)
    
    def update_with_trade(self, trade: Trade) -> None:
        """Update candle with new trade data"""
        self.high = max(self.high, trade.price)
        self.low = min(self.low, trade.price)
        self.close = trade.price
        self.volume += trade.size
        self.trade_count += 1
        
        # Update VWAP
        if self.volume > 0:
            total_value = (self.vwap * (self.volume - trade.size)) + (trade.price * trade.size)
            self.vwap = total_value / self.volume
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert candle to dictionary"""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp, timezone.utc).isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "trade_count": self.trade_count,
            "vwap": self.vwap,
            "ema12": self.ema12,
            "ema26": self.ema26,
            "rsi": self.rsi
        }


class TechnicalIndicators:
    """Technical indicator calculations"""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
        """
        Calculate Exponential Moving Average
        
        Args:
            prices: List of prices (usually close prices)
            period: EMA period
            
        Returns:
            List of EMA values (None for insufficient data)
        """
        if len(prices) < period:
            return [None] * len(prices)
        
        alpha = 2.0 / (period + 1)
        ema_values = [None] * len(prices)
        
        # Initialize with Simple Moving Average
        sma = sum(prices[:period]) / period
        ema_values[period - 1] = sma
        
        # Calculate EMA for remaining values
        for i in range(period, len(prices)):
            ema_values[i] = alpha * prices[i] + (1 - alpha) * ema_values[i - 1]
        
        return ema_values
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """
        Calculate Relative Strength Index
        
        Args:
            prices: List of prices (usually close prices)
            period: RSI period (default 14)
            
        Returns:
            List of RSI values (0-100)
        """
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [max(delta, 0) for delta in deltas]
        losses = [max(-delta, 0) for delta in deltas]
        
        rsi_values = [None] * len(prices)
        
        if len(gains) < period:
            return rsi_values
        
        # Calculate initial average gain and loss
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Calculate RSI for each period
        for i in range(period, len(deltas)):
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100.0 - (100.0 / (1.0 + rs))
            
            rsi_values[i + 1] = rsi
            
            # Update averages using Wilder's smoothing
            alpha = 1.0 / period
            avg_gain = alpha * gains[i] + (1 - alpha) * avg_gain
            avg_loss = alpha * losses[i] + (1 - alpha) * avg_loss
        
        return rsi_values
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """
        Calculate Bollinger Bands
        
        Args:
            prices: List of prices
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band) lists
        """
        if len(prices) < period:
            return ([None] * len(prices),) * 3
        
        upper_band = [None] * len(prices)
        middle_band = [None] * len(prices)
        lower_band = [None] * len(prices)
        
        for i in range(period - 1, len(prices)):
            # Calculate SMA and standard deviation
            window = prices[i - period + 1:i + 1]
            sma = sum(window) / period
            variance = sum((x - sma) ** 2 for x in window) / period
            std = math.sqrt(variance)
            
            middle_band[i] = sma
            upper_band[i] = sma + (std_dev * std)
            lower_band[i] = sma - (std_dev * std)
        
        return upper_band, middle_band, lower_band


class TimeframeManager:
    """Manages different timeframe configurations"""
    
    TIMEFRAME_SECONDS = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "1h": 3600,
        "4h": 14400,
        "1d": 86400
    }
    
    @classmethod
    def get_candle_start_time(cls, timestamp: float, timeframe: str) -> float:
        """Get the start time of the candle for given timestamp and timeframe"""
        interval_seconds = cls.TIMEFRAME_SECONDS.get(timeframe, 60)
        return (int(timestamp) // interval_seconds) * interval_seconds
    
    @classmethod
    def is_valid_timeframe(cls, timeframe: str) -> bool:
        """Check if timeframe is valid"""
        return timeframe in cls.TIMEFRAME_SECONDS
    
    @classmethod
    def get_next_candle_time(cls, current_time: float, timeframe: str) -> float:
        """Get the start time of the next candle"""
        interval_seconds = cls.TIMEFRAME_SECONDS.get(timeframe, 60)
        current_start = cls.get_candle_start_time(current_time, timeframe)
        return current_start + interval_seconds


class CandleStore:
    """In-memory storage for candle data with size limits"""
    
    def __init__(self, max_candles_per_timeframe: int = 1000):
        self.max_candles = max_candles_per_timeframe
        self.candles: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=max_candles_per_timeframe))
        )
        self.last_updated: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    def add_candle(self, candle: Candle) -> None:
        """Add candle to store"""
        self.candles[candle.symbol][candle.timeframe].append(candle)
        self.last_updated[candle.symbol][candle.timeframe] = time.time()
    
    def get_candles(self, symbol: str, timeframe: str, count: int = None) -> List[Candle]:
        """Get candles for symbol and timeframe"""
        candle_deque = self.candles[symbol][timeframe]
        if count is None:
            return list(candle_deque)
        else:
            return list(candle_deque)[-count:] if count <= len(candle_deque) else list(candle_deque)
    
    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Candle]:
        """Get the most recent candle"""
        candle_deque = self.candles[symbol][timeframe]
        return candle_deque[-1] if candle_deque else None
    
    def update_latest_candle(self, symbol: str, timeframe: str, trade: Trade) -> Optional[Candle]:
        """Update the latest candle with trade data"""
        candle_deque = self.candles[symbol][timeframe]
        if candle_deque:
            candle_deque[-1].update_with_trade(trade)
            return candle_deque[-1]
        return None


class CandleAggregator:
    """
    Real-time candle aggregation from trade data with:
    - Multiple timeframe support
    - Technical indicator calculation
    - Efficient storage and retrieval
    - Event callbacks for real-time updates
    """
    
    def __init__(self, symbols: List[str], timeframes: List[str] = None, ema_periods: List[int] = None):
        self.symbols = symbols
        self.timeframes = timeframes or ["1m", "5m", "15m", "1h", "4h", "1d"]
        self.ema_periods = ema_periods or [12, 26]
        
        # Validate timeframes
        for tf in self.timeframes:
            if not TimeframeManager.is_valid_timeframe(tf):
                raise ValueError(f"Invalid timeframe: {tf}")
        
        # Storage
        self.candle_store = CandleStore()
        
        # Current incomplete candles
        self.current_candles: Dict[str, Dict[str, Candle]] = defaultdict(dict)
        
        # Technical indicator calculators
        self.indicators = TechnicalIndicators()
        
        # Event callbacks
        self.candle_complete_callbacks: List[callable] = []
        self.candle_update_callbacks: List[callable] = []
        
        # Statistics
        self.stats = {
            "trades_processed": 0,
            "candles_created": 0,
            "last_trade_time": None,
            "symbols_active": 0
        }
        
        logger.info("Candle aggregator initialized", 
                   symbols=symbols, timeframes=self.timeframes)
    
    def add_candle_complete_callback(self, callback: callable) -> None:
        """Add callback for when candles are completed"""
        self.candle_complete_callbacks.append(callback)
    
    def add_candle_update_callback(self, callback: callable) -> None:
        """Add callback for candle updates"""
        self.candle_update_callbacks.append(callback)
    
    async def handle_trade_message(self, message: Dict[str, Any]) -> None:
        """
        Handle incoming trade WebSocket message
        
        Args:
            message: WebSocket message containing trade data
        """
        try:
            symbol = message.get("id", "")
            if symbol not in self.symbols:
                logger.debug("Received trade for untracked symbol", symbol=symbol)
                return
            
            contents = message.get("contents", {})
            if not contents:
                logger.warning("Empty trade message", symbol=symbol)
                return
            
            # Extract trade data
            trades_data = contents.get("trades", [])
            if not trades_data:
                logger.debug("No trades in message", symbol=symbol)
                return
            
            # Process each trade
            for trade_data in trades_data:
                trade = Trade(
                    symbol=symbol,
                    price=float(trade_data.get("price", 0)),
                    size=float(trade_data.get("size", 0)),
                    side=trade_data.get("side", ""),
                    timestamp=float(trade_data.get("createdAt", time.time())),
                    trade_id=trade_data.get("id")
                )
                
                await self.process_trade(trade)
            
            self.stats["trades_processed"] += len(trades_data)
            self.stats["last_trade_time"] = datetime.utcnow()
            
        except Exception as e:
            logger.error("Error handling trade message", error=str(e))
    
    async def process_trade(self, trade: Trade) -> None:
        """
        Process individual trade and update candles
        
        Args:
            trade: Trade data to process
        """
        try:
            # Process trade for each timeframe
            for timeframe in self.timeframes:
                await self._update_candle_for_timeframe(trade, timeframe)
            
        except Exception as e:
            logger.error("Error processing trade", 
                        symbol=trade.symbol, 
                        trade_id=trade.trade_id,
                        error=str(e))
    
    async def _update_candle_for_timeframe(self, trade: Trade, timeframe: str) -> None:
        """Update or create candle for specific timeframe"""
        candle_start_time = TimeframeManager.get_candle_start_time(trade.timestamp, timeframe)
        candle_key = f"{trade.symbol}_{timeframe}_{int(candle_start_time)}"
        
        # Get or create current candle
        current_candle = self.current_candles[trade.symbol].get(timeframe)
        
        if current_candle is None or current_candle.timestamp != candle_start_time:
            # Need to create new candle
            if current_candle is not None:
                # Complete the previous candle
                await self._complete_candle(current_candle)
            
            # Create new candle
            current_candle = Candle(
                symbol=trade.symbol,
                timeframe=timeframe,
                timestamp=candle_start_time,
                open=trade.price,
                high=trade.price,
                low=trade.price,
                close=trade.price,
                volume=0.0,
                trade_count=0,
                vwap=trade.price
            )
            
            self.current_candles[trade.symbol][timeframe] = current_candle
            self.stats["candles_created"] += 1
        
        # Update candle with trade
        current_candle.update_with_trade(trade)
        
        # Notify update callbacks
        if self.candle_update_callbacks:
            tasks = [callback(current_candle) for callback in self.candle_update_callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _complete_candle(self, candle: Candle) -> None:
        """Complete candle and calculate technical indicators"""
        try:
            # Calculate technical indicators
            await self._calculate_indicators(candle)
            
            # Store completed candle
            self.candle_store.add_candle(candle)
            
            # Notify completion callbacks
            if self.candle_complete_callbacks:
                tasks = [callback(candle) for callback in self.candle_complete_callbacks]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.debug("Candle completed",
                        symbol=candle.symbol,
                        timeframe=candle.timeframe,
                        timestamp=candle.timestamp,
                        ohlcv=f"O:{candle.open:.2f} H:{candle.high:.2f} L:{candle.low:.2f} C:{candle.close:.2f} V:{candle.volume:.2f}")
            
        except Exception as e:
            logger.error("Error completing candle", 
                        symbol=candle.symbol,
                        timeframe=candle.timeframe,
                        error=str(e))
    
    async def _calculate_indicators(self, candle: Candle) -> None:
        """Calculate technical indicators for candle"""
        try:
            # Get historical candles for calculation
            historical_candles = self.candle_store.get_candles(candle.symbol, candle.timeframe, 100)
            
            if len(historical_candles) < 2:
                return  # Not enough data
            
            # Add current candle to historical data for calculation
            all_candles = historical_candles + [candle]
            close_prices = [c.close for c in all_candles]
            
            # Calculate EMAs
            for period in self.ema_periods:
                ema_values = self.indicators.calculate_ema(close_prices, period)
                if ema_values[-1] is not None:
                    if period == 12:
                        candle.ema12 = ema_values[-1]
                    elif period == 26:
                        candle.ema26 = ema_values[-1]
            
            # Calculate RSI
            rsi_values = self.indicators.calculate_rsi(close_prices, 14)
            if rsi_values[-1] is not None:
                candle.rsi = rsi_values[-1]
            
        except Exception as e:
            logger.error("Error calculating indicators", 
                        symbol=candle.symbol,
                        error=str(e))
    
    def get_candles(self, symbol: str, timeframe: str, count: int = 100) -> List[Candle]:
        """
        Get historical candles for symbol and timeframe
        
        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            count: Number of candles to retrieve
            
        Returns:
            List of candles (most recent first)
        """
        if timeframe not in self.timeframes:
            logger.warning("Invalid timeframe requested", timeframe=timeframe)
            return []
        
        historical = self.candle_store.get_candles(symbol, timeframe, count)
        
        # Include current incomplete candle if it exists
        current = self.current_candles[symbol].get(timeframe)
        if current:
            historical.append(current)
        
        return historical[-count:] if count else historical
    
    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Candle]:
        """Get the most recent candle (may be incomplete)"""
        # Try current candle first
        current = self.current_candles[symbol].get(timeframe)
        if current:
            return current
        
        # Fall back to completed candles
        return self.candle_store.get_latest_candle(symbol, timeframe)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from most recent 1m candle"""
        latest_candle = self.get_latest_candle(symbol, "1m")
        return latest_candle.close if latest_candle else None
    
    async def force_complete_candles(self, symbol: Optional[str] = None) -> None:
        """Force completion of current candles (useful for shutdown)"""
        if symbol:
            symbols = [symbol] if symbol in self.symbols else []
        else:
            symbols = self.symbols
        
        for sym in symbols:
            for timeframe in self.timeframes:
                current_candle = self.current_candles[sym].get(timeframe)
                if current_candle:
                    await self._complete_candle(current_candle)
                    del self.current_candles[sym][timeframe]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        active_symbols = len([
            symbol for symbol in self.symbols
            if any(self.current_candles[symbol].values())
        ])
        
        self.stats["symbols_active"] = active_symbols
        
        return {
            **self.stats,
            "timeframes": self.timeframes,
            "total_stored_candles": sum(
                len(timeframes) for timeframes in self.candle_store.candles.values()
            )
        }