"""
Moving Average Crossover Strategy
Implements EMA crossover strategy with RSI confirmation and dynamic position sizing.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import structlog

from src.config import get_config
from src.trading.market_data.candles import Candle
from src.trading.strategies.base import BaseStrategy, Signal, SignalType

logger = structlog.get_logger(__name__)


@dataclass
class CrossoverState:
    """Track crossover state for a symbol"""
    last_ema_fast: Optional[float] = None
    last_ema_slow: Optional[float] = None
    last_crossover_time: float = 0.0
    last_crossover_direction: Optional[str] = None  # "bullish" or "bearish"
    consecutive_confirmations: int = 0
    in_position: bool = False


class MovingAverageCrossoverStrategy(BaseStrategy):
    """
    EMA Crossover Strategy with RSI confirmation:
    
    Entry Signals:
    - BUY: Fast EMA crosses above Slow EMA + RSI > oversold threshold
    - SELL: Fast EMA crosses below Slow EMA + RSI < overbought threshold
    
    Signal Strength Factors:
    - Magnitude of EMA separation
    - RSI position relative to extremes
    - Volume confirmation
    - Recent price momentum
    
    Configuration Parameters:
    - fast_period: Fast EMA period (default: 12)
    - slow_period: Slow EMA period (default: 26)
    - rsi_period: RSI period (default: 14)
    - rsi_oversold: RSI oversold threshold (default: 30)
    - rsi_overbought: RSI overbought threshold (default: 70)
    - min_crossover_separation: Minimum EMA separation for signal (default: 0.001)
    - confirmation_candles: Number of confirmation candles required (default: 1)
    - volume_confirmation: Require volume > average (default: True)
    """
    
    def __init__(self, symbols: List[str], config: Dict[str, Any] = None):
        # Default configuration
        default_config = {
            "fast_period": 12,
            "slow_period": 26,
            "rsi_period": 14,
            "rsi_oversold": 30.0,
            "rsi_overbought": 70.0,
            "min_crossover_separation": 0.001,  # 0.1%
            "confirmation_candles": 1,
            "volume_confirmation": True,
            "max_history_candles": 200,
            "min_signal_strength": 0.3,
            "cooldown_period": 300  # 5 minutes between signals
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("EMA_Crossover", symbols, default_config)
        
        # State tracking for each symbol
        self.crossover_states: Dict[str, CrossoverState] = {
            symbol: CrossoverState() for symbol in symbols
        }
        
        logger.info("EMA Crossover strategy initialized",
                   fast_period=self.config["fast_period"],
                   slow_period=self.config["slow_period"],
                   rsi_oversold=self.config["rsi_oversold"],
                   rsi_overbought=self.config["rsi_overbought"])
    
    def _validate_config(self) -> None:
        """Validate strategy configuration"""
        fast_period = self.config.get("fast_period", 12)
        slow_period = self.config.get("slow_period", 26)
        
        if fast_period >= slow_period:
            raise ValueError("Fast EMA period must be less than slow EMA period")
        
        if fast_period < 5 or slow_period < 10:
            raise ValueError("EMA periods too short (min: fast=5, slow=10)")
        
        rsi_oversold = self.config.get("rsi_oversold", 30)
        rsi_overbought = self.config.get("rsi_overbought", 70)
        
        if rsi_oversold >= rsi_overbought:
            raise ValueError("RSI oversold must be less than overbought")
        
        if rsi_oversold < 10 or rsi_overbought > 90:
            raise ValueError("RSI thresholds out of reasonable range (10-90)")
    
    async def analyze(self, symbol: str, candles: List[Candle]) -> Optional[Signal]:
        """
        Analyze EMA crossover and RSI for trading signal
        
        Args:
            symbol: Trading symbol
            candles: Historical candle data (most recent last)
            
        Returns:
            Trading signal or None
        """
        if len(candles) < self.config["slow_period"] + 10:
            logger.debug("Insufficient candle data for analysis",
                        symbol=symbol,
                        required=self.config["slow_period"] + 10,
                        available=len(candles))
            return None
        
        try:
            # Get latest candle
            latest_candle = candles[-1]
            
            # Check for required indicators
            if (latest_candle.ema12 is None or 
                latest_candle.ema26 is None or 
                latest_candle.rsi is None):
                logger.debug("Missing required indicators",
                           symbol=symbol,
                           ema12=latest_candle.ema12,
                           ema26=latest_candle.ema26,
                           rsi=latest_candle.rsi)
                return None
            
            # Map EMA values based on configuration
            if self.config["fast_period"] == 12:
                ema_fast = latest_candle.ema12
            else:
                # For non-standard periods, we'd need to calculate separately
                # For now, default to ema12
                ema_fast = latest_candle.ema12
            
            if self.config["slow_period"] == 26:
                ema_slow = latest_candle.ema26
            else:
                # For non-standard periods, we'd need to calculate separately  
                # For now, default to ema26
                ema_slow = latest_candle.ema26
            
            rsi = latest_candle.rsi
            current_price = latest_candle.close
            
            # Get crossover state
            state = self.crossover_states[symbol]
            
            # Check for crossover
            crossover_signal = self._detect_crossover(
                symbol, ema_fast, ema_slow, current_price
            )
            
            if not crossover_signal:
                return None
            
            # Validate signal with RSI and other filters
            signal = await self._validate_and_build_signal(
                symbol, crossover_signal, ema_fast, ema_slow, rsi, 
                current_price, latest_candle, candles
            )
            
            return signal
            
        except Exception as e:
            logger.error("Error analyzing EMA crossover",
                        symbol=symbol,
                        error=str(e))
            return None
    
    def _detect_crossover(self, symbol: str, ema_fast: float, ema_slow: float, price: float) -> Optional[str]:
        """
        Detect EMA crossover events
        
        Args:
            symbol: Trading symbol
            ema_fast: Fast EMA value
            ema_slow: Slow EMA value
            price: Current price
            
        Returns:
            "bullish" for bullish crossover, "bearish" for bearish crossover, None for no crossover
        """
        state = self.crossover_states[symbol]
        
        # Need previous values for crossover detection
        if state.last_ema_fast is None or state.last_ema_slow is None:
            # Initialize state
            state.last_ema_fast = ema_fast
            state.last_ema_slow = ema_slow
            return None
        
        # Check for bullish crossover (fast crosses above slow)
        if (state.last_ema_fast <= state.last_ema_slow and 
            ema_fast > ema_slow):
            
            # Ensure minimum separation
            separation = abs(ema_fast - ema_slow) / price
            if separation >= self.config["min_crossover_separation"]:
                logger.info("Bullish EMA crossover detected",
                           symbol=symbol,
                           ema_fast=ema_fast,
                           ema_slow=ema_slow,
                           separation_pct=separation * 100)
                
                state.last_crossover_time = time.time()
                state.last_crossover_direction = "bullish"
                state.consecutive_confirmations = 1
                
                # Update state
                state.last_ema_fast = ema_fast
                state.last_ema_slow = ema_slow
                
                return "bullish"
        
        # Check for bearish crossover (fast crosses below slow)
        elif (state.last_ema_fast >= state.last_ema_slow and 
              ema_fast < ema_slow):
            
            # Ensure minimum separation
            separation = abs(ema_slow - ema_fast) / price
            if separation >= self.config["min_crossover_separation"]:
                logger.info("Bearish EMA crossover detected",
                           symbol=symbol,
                           ema_fast=ema_fast,
                           ema_slow=ema_slow,
                           separation_pct=separation * 100)
                
                state.last_crossover_time = time.time()
                state.last_crossover_direction = "bearish"
                state.consecutive_confirmations = 1
                
                # Update state
                state.last_ema_fast = ema_fast
                state.last_ema_slow = ema_slow
                
                return "bearish"
        
        # Check for confirmation candles
        elif (state.last_crossover_direction and 
              state.consecutive_confirmations < self.config["confirmation_candles"]):
            
            # Bullish confirmation
            if (state.last_crossover_direction == "bullish" and ema_fast > ema_slow):
                state.consecutive_confirmations += 1
                if state.consecutive_confirmations >= self.config["confirmation_candles"]:
                    # Update state
                    state.last_ema_fast = ema_fast
                    state.last_ema_slow = ema_slow
                    return "bullish"
            
            # Bearish confirmation
            elif (state.last_crossover_direction == "bearish" and ema_fast < ema_slow):
                state.consecutive_confirmations += 1
                if state.consecutive_confirmations >= self.config["confirmation_candles"]:
                    # Update state
                    state.last_ema_fast = ema_fast
                    state.last_ema_slow = ema_slow
                    return "bearish"
            
            # Confirmation failed
            else:
                state.last_crossover_direction = None
                state.consecutive_confirmations = 0
        
        # Update state
        state.last_ema_fast = ema_fast
        state.last_ema_slow = ema_slow
        
        return None
    
    async def _validate_and_build_signal(
        self, 
        symbol: str, 
        crossover_direction: str, 
        ema_fast: float, 
        ema_slow: float, 
        rsi: float, 
        current_price: float,
        latest_candle: Candle,
        candles: List[Candle]
    ) -> Optional[Signal]:
        """
        Validate crossover signal and build complete signal with strength calculation
        """
        # Check cooldown period
        state = self.crossover_states[symbol]
        if time.time() - state.last_crossover_time < self.config["cooldown_period"]:
            logger.debug("Signal in cooldown period",
                        symbol=symbol,
                        cooldown_remaining=self.config["cooldown_period"] - (time.time() - state.last_crossover_time))
            return None
        
        signal_type = None
        reasons = []
        
        if crossover_direction == "bullish":
            # Bullish crossover - check RSI confirmation
            if rsi > self.config["rsi_oversold"]:
                signal_type = SignalType.BUY
                reasons.append(f"Bullish EMA crossover (Fast: {ema_fast:.4f}, Slow: {ema_slow:.4f})")
                reasons.append(f"RSI above oversold ({rsi:.2f} > {self.config['rsi_oversold']})")
            else:
                logger.debug("Bullish crossover rejected - RSI too low",
                           symbol=symbol,
                           rsi=rsi,
                           threshold=self.config["rsi_oversold"])
                return None
        
        elif crossover_direction == "bearish":
            # Bearish crossover - check RSI confirmation
            if rsi < self.config["rsi_overbought"]:
                signal_type = SignalType.SELL
                reasons.append(f"Bearish EMA crossover (Fast: {ema_fast:.4f}, Slow: {ema_slow:.4f})")
                reasons.append(f"RSI below overbought ({rsi:.2f} < {self.config['rsi_overbought']})")
            else:
                logger.debug("Bearish crossover rejected - RSI too high",
                           symbol=symbol,
                           rsi=rsi,
                           threshold=self.config["rsi_overbought"])
                return None
        
        if signal_type is None:
            return None
        
        # Volume confirmation
        if self.config["volume_confirmation"]:
            volume_confirmed = self._check_volume_confirmation(candles, latest_candle)
            if not volume_confirmed:
                logger.debug("Signal rejected - insufficient volume",
                           symbol=symbol,
                           current_volume=latest_candle.volume)
                return None
            reasons.append("Volume confirmation passed")
        
        # Calculate signal strength
        strength = self._calculate_signal_strength(
            ema_fast, ema_slow, rsi, current_price, crossover_direction
        )
        
        # Check minimum signal strength
        if strength < self.config["min_signal_strength"]:
            logger.debug("Signal rejected - insufficient strength",
                        symbol=symbol,
                        strength=strength,
                        min_required=self.config["min_signal_strength"])
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            ema_fast, ema_slow, rsi, candles, crossover_direction
        )
        
        # Determine if this is a strong signal
        if strength > 0.7 and confidence > 0.6:
            if signal_type == SignalType.BUY:
                signal_type = SignalType.STRONG_BUY
            elif signal_type == SignalType.SELL:
                signal_type = SignalType.STRONG_SELL
            reasons.append("Strong signal conditions met")
        
        # Build indicators dict
        indicators = {
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "rsi": rsi,
            "ema_separation": abs(ema_fast - ema_slow) / current_price,
            "volume": latest_candle.volume,
            "crossover_direction": crossover_direction
        }
        
        # Create signal
        signal = Signal(
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            timestamp=time.time(),
            price=current_price,
            strategy_name=self.name,
            confidence=confidence,
            reasons=reasons,
            indicators=indicators
        )
        
        return signal
    
    def _calculate_signal_strength(
        self, 
        ema_fast: float, 
        ema_slow: float, 
        rsi: float, 
        price: float,
        direction: str
    ) -> float:
        """Calculate signal strength from 0.0 to 1.0"""
        # Base strength from EMA separation
        separation = abs(ema_fast - ema_slow) / price
        separation_strength = min(separation / 0.01, 1.0)  # Max strength at 1% separation
        
        # RSI strength component
        if direction == "bullish":
            # Stronger signal if RSI is higher but not overbought
            rsi_strength = min((rsi - self.config["rsi_oversold"]) / 
                              (self.config["rsi_overbought"] - self.config["rsi_oversold"]), 1.0)
        else:
            # Stronger signal if RSI is lower but not oversold
            rsi_strength = min((self.config["rsi_overbought"] - rsi) / 
                              (self.config["rsi_overbought"] - self.config["rsi_oversold"]), 1.0)
        
        # Combined strength (weighted average)
        strength = (separation_strength * 0.6 + rsi_strength * 0.4)
        
        return max(0.0, min(1.0, strength))
    
    def _calculate_confidence(
        self, 
        ema_fast: float, 
        ema_slow: float, 
        rsi: float, 
        candles: List[Candle],
        direction: str
    ) -> float:
        """Calculate signal confidence from 0.0 to 1.0"""
        confidence_factors = []
        
        # Trend consistency (check last few candles)
        trend_candles = min(5, len(candles))
        if trend_candles >= 3:
            if direction == "bullish":
                bullish_candles = sum(1 for i in range(-trend_candles, -1) 
                                    if candles[i].close > candles[i].open)
                trend_confidence = bullish_candles / (trend_candles - 1)
            else:
                bearish_candles = sum(1 for i in range(-trend_candles, -1) 
                                    if candles[i].close < candles[i].open)
                trend_confidence = bearish_candles / (trend_candles - 1)
            
            confidence_factors.append(trend_confidence)
        
        # RSI position confidence
        if direction == "bullish":
            rsi_confidence = 1.0 - (rsi - 30) / 40  # Higher confidence closer to oversold
        else:
            rsi_confidence = (rsi - 30) / 40  # Higher confidence closer to overbought
        
        confidence_factors.append(max(0.0, min(1.0, rsi_confidence)))
        
        # Volume consistency
        if len(candles) >= 10:
            recent_volumes = [c.volume for c in candles[-10:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes)
            latest_volume = candles[-1].volume
            
            if avg_volume > 0:
                volume_confidence = min(latest_volume / avg_volume, 2.0) / 2.0
                confidence_factors.append(volume_confidence)
        
        # Average confidence
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5  # Default moderate confidence
    
    def _check_volume_confirmation(self, candles: List[Candle], latest_candle: Candle) -> bool:
        """Check if current volume supports the signal"""
        if len(candles) < 20:
            return True  # Skip volume check if insufficient history
        
        # Calculate average volume over last 20 periods
        recent_volumes = [c.volume for c in candles[-20:-1]]  # Exclude current candle
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        # Current volume should be at least 80% of average
        return latest_candle.volume >= (avg_volume * 0.8)
    
    async def should_exit_position(self, symbol: str, current_price: float, entry_price: float, side: str) -> bool:
        """
        Determine if current position should be exited based on EMA crossover reversal
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            entry_price: Position entry price
            side: Position side ("BUY" or "SELL")
            
        Returns:
            True if position should be exited
        """
        # Get latest candle data
        if symbol not in self.historical_data or len(self.historical_data[symbol]) == 0:
            return False
        
        latest_candle = self.historical_data[symbol][-1]
        
        if (latest_candle.ema12 is None or latest_candle.ema26 is None):
            return False
        
        ema_fast = latest_candle.ema12
        ema_slow = latest_candle.ema26
        
        # Exit long position if EMAs cross bearish
        if side.upper() == "BUY" and ema_fast < ema_slow:
            logger.info("Exit signal for long position - bearish EMA crossover",
                       symbol=symbol,
                       current_price=current_price,
                       entry_price=entry_price)
            return True
        
        # Exit short position if EMAs cross bullish  
        elif side.upper() == "SELL" and ema_fast > ema_slow:
            logger.info("Exit signal for short position - bullish EMA crossover",
                       symbol=symbol,
                       current_price=current_price,
                       entry_price=entry_price)
            return True
        
        return False
    
    def get_current_market_bias(self, symbol: str) -> Optional[str]:
        """
        Get current market bias based on EMA relationship
        
        Returns:
            "bullish", "bearish", or None
        """
        if symbol not in self.historical_data or len(self.historical_data[symbol]) == 0:
            return None
        
        latest_candle = self.historical_data[symbol][-1]
        
        if latest_candle.ema12 is None or latest_candle.ema26 is None:
            return None
        
        if latest_candle.ema12 > latest_candle.ema26:
            return "bullish"
        elif latest_candle.ema12 < latest_candle.ema26:
            return "bearish"
        else:
            return "neutral"
    
    def get_strategy_status(self, symbol: str) -> Dict[str, Any]:
        """Get detailed strategy status for symbol"""
        state = self.crossover_states.get(symbol, CrossoverState())
        
        bias = self.get_current_market_bias(symbol)
        latest_signal = self.get_latest_signal(symbol)
        
        return {
            "symbol": symbol,
            "market_bias": bias,
            "last_crossover_direction": state.last_crossover_direction,
            "last_crossover_time": state.last_crossover_time,
            "consecutive_confirmations": state.consecutive_confirmations,
            "latest_signal": latest_signal.to_dict() if latest_signal else None,
            "in_position": state.in_position
        }