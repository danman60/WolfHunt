"""
Daily Loss Monitor
Monitors daily losses and implements auto-disable functionality to protect capital.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import structlog

from src.config import get_config

logger = structlog.get_logger(__name__)


class TradingState(str, Enum):
    """Trading system states"""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    MAINTENANCE = "MAINTENANCE"


@dataclass
class DailyPnL:
    """Daily P&L tracking"""
    date: str  # YYYY-MM-DD format
    starting_equity: float
    current_equity: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    max_drawdown: float = 0.0
    max_equity_today: float = 0.0
    trades_count: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    last_updated: float = field(default_factory=time.time)
    
    def update(self, current_equity: float, realized_pnl: float, unrealized_pnl: float) -> None:
        """Update daily P&L metrics"""
        self.current_equity = current_equity
        self.realized_pnl = realized_pnl
        self.unrealized_pnl = unrealized_pnl
        self.total_pnl = realized_pnl + unrealized_pnl
        self.total_pnl_pct = (self.total_pnl / self.starting_equity) if self.starting_equity > 0 else 0
        
        # Update max equity and drawdown
        if current_equity > self.max_equity_today:
            self.max_equity_today = current_equity
        
        current_drawdown = (self.max_equity_today - current_equity) / self.max_equity_today if self.max_equity_today > 0 else 0
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        self.last_updated = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "date": self.date,
            "starting_equity": self.starting_equity,
            "current_equity": self.current_equity,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "total_pnl": self.total_pnl,
            "total_pnl_pct": self.total_pnl_pct,
            "max_drawdown": self.max_drawdown,
            "max_equity_today": self.max_equity_today,
            "trades_count": self.trades_count,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": (self.winning_trades / self.trades_count) * 100 if self.trades_count > 0 else 0,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "last_updated": self.last_updated
        }


class DailyLossMonitor:
    """
    Daily loss monitoring system with:
    - Real-time P&L tracking
    - Daily loss limit enforcement
    - Automatic trading suspension
    - Recovery procedures
    - Alert notifications
    - Historical tracking
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Configuration
        self.daily_loss_limit_pct = self.config.daily_loss_limit_pct
        self.enable_auto_suspend = True
        self.recovery_delay_hours = 24  # Hours before allowing re-enable
        
        # State tracking
        self.trading_state = TradingState.ACTIVE
        self.suspension_reason: Optional[str] = None
        self.suspension_time: Optional[float] = None
        self.last_recovery_attempt: Optional[float] = None
        
        # Daily tracking
        self.current_daily_pnl: Optional[DailyPnL] = None
        self.daily_history: Dict[str, DailyPnL] = {}  # date -> DailyPnL
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        self.suspension_callbacks: List[Callable] = []
        
        # Statistics
        self.stats = {
            "days_tracked": 0,
            "suspension_count": 0,
            "limit_breaches": 0,
            "max_daily_loss": 0.0,
            "max_daily_gain": 0.0,
            "average_daily_return": 0.0,
            "win_days": 0,
            "loss_days": 0,
            "break_even_days": 0
        }
        
        logger.info("Daily loss monitor initialized",
                   daily_loss_limit_pct=self.daily_loss_limit_pct * 100,
                   auto_suspend=self.enable_auto_suspend)
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add callback for alerts"""
        self.alert_callbacks.append(callback)
    
    def add_suspension_callback(self, callback: Callable) -> None:
        """Add callback for suspension events"""
        self.suspension_callbacks.append(callback)
    
    def get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    async def track_daily_pnl(self, current_equity: float, realized_pnl: float, unrealized_pnl: float) -> DailyPnL:
        """
        Track daily P&L and check limits
        
        Args:
            current_equity: Current account equity
            realized_pnl: Today's realized P&L
            unrealized_pnl: Current unrealized P&L
            
        Returns:
            Updated DailyPnL object
        """
        current_date = self.get_current_date()
        
        # Initialize new day if needed
        if (self.current_daily_pnl is None or 
            self.current_daily_pnl.date != current_date):
            await self._initialize_new_day(current_date, current_equity)
        
        # Update current day P&L
        self.current_daily_pnl.update(current_equity, realized_pnl, unrealized_pnl)
        
        # Store in history
        self.daily_history[current_date] = self.current_daily_pnl
        
        # Check loss limits
        await self._check_loss_limits()
        
        return self.current_daily_pnl
    
    async def _initialize_new_day(self, date: str, starting_equity: float) -> None:
        """Initialize tracking for a new day"""
        # Store previous day if it exists
        if self.current_daily_pnl:
            await self._finalize_day(self.current_daily_pnl)
        
        # Create new day tracking
        self.current_daily_pnl = DailyPnL(
            date=date,
            starting_equity=starting_equity,
            current_equity=starting_equity,
            max_equity_today=starting_equity
        )
        
        self.stats["days_tracked"] += 1
        
        logger.info("New trading day initialized",
                   date=date,
                   starting_equity=starting_equity)
    
    async def _finalize_day(self, daily_pnl: DailyPnL) -> None:
        """Finalize day and update statistics"""
        # Update win/loss statistics
        if daily_pnl.total_pnl > 0:
            self.stats["win_days"] += 1
            if daily_pnl.total_pnl_pct > self.stats["max_daily_gain"]:
                self.stats["max_daily_gain"] = daily_pnl.total_pnl_pct
        elif daily_pnl.total_pnl < 0:
            self.stats["loss_days"] += 1
            if daily_pnl.total_pnl_pct < self.stats["max_daily_loss"]:
                self.stats["max_daily_loss"] = daily_pnl.total_pnl_pct
        else:
            self.stats["break_even_days"] += 1
        
        # Update average daily return
        total_days = self.stats["win_days"] + self.stats["loss_days"] + self.stats["break_even_days"]
        if total_days > 0:
            total_return = sum(pnl.total_pnl_pct for pnl in self.daily_history.values())
            self.stats["average_daily_return"] = total_return / total_days
        
        logger.info("Trading day finalized",
                   date=daily_pnl.date,
                   total_pnl=daily_pnl.total_pnl,
                   total_pnl_pct=daily_pnl.total_pnl_pct * 100,
                   trades=daily_pnl.trades_count,
                   max_drawdown=daily_pnl.max_drawdown * 100)
    
    async def _check_loss_limits(self) -> None:
        """Check if daily loss limits have been breached"""
        if not self.current_daily_pnl:
            return
        
        # Check daily loss limit
        if self.current_daily_pnl.total_pnl_pct <= -self.daily_loss_limit_pct:
            self.stats["limit_breaches"] += 1
            
            await self._trigger_loss_limit_breach()
    
    async def _trigger_loss_limit_breach(self) -> None:
        """Handle daily loss limit breach"""
        if self.trading_state == TradingState.SUSPENDED:
            return  # Already suspended
        
        loss_pct = self.current_daily_pnl.total_pnl_pct * 100
        
        logger.critical("Daily loss limit breached",
                       current_loss_pct=loss_pct,
                       limit_pct=self.daily_loss_limit_pct * 100,
                       equity_remaining=self.current_daily_pnl.current_equity)
        
        # Send alerts
        await self._send_alerts(
            level="CRITICAL",
            message=f"Daily loss limit breached: {loss_pct:.2f}% (limit: {self.daily_loss_limit_pct * 100:.1f}%)",
            data=self.current_daily_pnl.to_dict()
        )
        
        # Auto-suspend trading if enabled
        if self.enable_auto_suspend:
            await self.suspend_trading(f"Daily loss limit breached: {loss_pct:.2f}%")
    
    async def suspend_trading(self, reason: str) -> None:
        """
        Suspend all trading activity
        
        Args:
            reason: Reason for suspension
        """
        if self.trading_state == TradingState.SUSPENDED:
            logger.warning("Trading already suspended")
            return
        
        self.trading_state = TradingState.SUSPENDED
        self.suspension_reason = reason
        self.suspension_time = time.time()
        self.stats["suspension_count"] += 1
        
        logger.critical("Trading suspended",
                       reason=reason,
                       suspension_time=datetime.fromtimestamp(self.suspension_time))
        
        # Notify suspension callbacks
        if self.suspension_callbacks:
            tasks = [callback(reason) for callback in self.suspension_callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Send critical alert
        await self._send_alerts(
            level="CRITICAL",
            message=f"Trading suspended: {reason}",
            data={
                "suspension_reason": reason,
                "suspension_time": self.suspension_time,
                "can_recover_at": self.suspension_time + (self.recovery_delay_hours * 3600)
            }
        )
    
    async def emergency_stop(self, reason: str) -> None:
        """
        Emergency stop all trading (manual intervention required)
        
        Args:
            reason: Reason for emergency stop
        """
        self.trading_state = TradingState.EMERGENCY_STOP
        self.suspension_reason = f"EMERGENCY: {reason}"
        self.suspension_time = time.time()
        
        logger.critical("EMERGENCY STOP ACTIVATED",
                       reason=reason,
                       intervention_required=True)
        
        await self._send_alerts(
            level="EMERGENCY",
            message=f"EMERGENCY STOP: {reason}",
            data={
                "requires_manual_intervention": True,
                "emergency_time": self.suspension_time
            }
        )
    
    def can_resume_trading(self) -> Tuple[bool, Optional[str]]:
        """
        Check if trading can be resumed
        
        Returns:
            Tuple of (can_resume, reason_if_not)
        """
        if self.trading_state == TradingState.ACTIVE:
            return True, None
        
        if self.trading_state == TradingState.EMERGENCY_STOP:
            return False, "Emergency stop requires manual intervention"
        
        if self.trading_state == TradingState.MAINTENANCE:
            return False, "System in maintenance mode"
        
        if self.trading_state == TradingState.SUSPENDED:
            if not self.suspension_time:
                return False, "Suspension time not recorded"
            
            # Check if enough time has passed
            time_since_suspension = time.time() - self.suspension_time
            required_delay = self.recovery_delay_hours * 3600
            
            if time_since_suspension < required_delay:
                remaining_hours = (required_delay - time_since_suspension) / 3600
                return False, f"Must wait {remaining_hours:.1f} more hours before recovery"
            
            # Check if we're in a new trading day
            current_date = self.get_current_date()
            if self.current_daily_pnl and self.current_daily_pnl.date == current_date:
                return False, "Cannot resume on same day as suspension"
            
            return True, None
        
        return False, "Unknown trading state"
    
    async def resume_trading(self, manual_override: bool = False) -> bool:
        """
        Resume trading if conditions are met
        
        Args:
            manual_override: Override safety checks (use with caution)
            
        Returns:
            True if trading was resumed
        """
        if not manual_override:
            can_resume, reason = self.can_resume_trading()
            if not can_resume:
                logger.warning("Cannot resume trading", reason=reason)
                return False
        
        # Emergency stops require manual override
        if self.trading_state == TradingState.EMERGENCY_STOP and not manual_override:
            logger.error("Emergency stop requires manual override to resume")
            return False
        
        old_state = self.trading_state
        self.trading_state = TradingState.ACTIVE
        self.suspension_reason = None
        self.last_recovery_attempt = time.time()
        
        logger.info("Trading resumed",
                   previous_state=old_state,
                   manual_override=manual_override)
        
        await self._send_alerts(
            level="INFO",
            message="Trading resumed",
            data={
                "previous_state": old_state,
                "resume_time": time.time(),
                "manual_override": manual_override
            }
        )
        
        return True
    
    def record_trade(self, pnl: float) -> None:
        """Record a completed trade"""
        if not self.current_daily_pnl:
            return
        
        self.current_daily_pnl.trades_count += 1
        
        if pnl > 0:
            self.current_daily_pnl.winning_trades += 1
            if pnl > self.current_daily_pnl.largest_win:
                self.current_daily_pnl.largest_win = pnl
        elif pnl < 0:
            self.current_daily_pnl.losing_trades += 1
            if pnl < self.current_daily_pnl.largest_loss:
                self.current_daily_pnl.largest_loss = pnl
    
    async def _send_alerts(self, level: str, message: str, data: Dict[str, Any]) -> None:
        """Send alerts to registered callbacks"""
        if self.alert_callbacks:
            alert_data = {
                "level": level,
                "message": message,
                "timestamp": time.time(),
                "data": data
            }
            
            tasks = [callback(alert_data) for callback in self.alert_callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_current_pnl(self) -> Optional[DailyPnL]:
        """Get current day P&L"""
        return self.current_daily_pnl
    
    def get_historical_pnl(self, days: int = 30) -> List[DailyPnL]:
        """Get historical daily P&L data"""
        sorted_dates = sorted(self.daily_history.keys(), reverse=True)
        return [self.daily_history[date] for date in sorted_dates[:days]]
    
    def get_trading_state(self) -> TradingState:
        """Get current trading state"""
        return self.trading_state
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed"""
        return self.trading_state == TradingState.ACTIVE
    
    def get_suspension_info(self) -> Optional[Dict[str, Any]]:
        """Get suspension information if suspended"""
        if self.trading_state != TradingState.SUSPENDED or not self.suspension_time:
            return None
        
        time_since_suspension = time.time() - self.suspension_time
        required_delay = self.recovery_delay_hours * 3600
        can_recover_at = self.suspension_time + required_delay
        
        return {
            "reason": self.suspension_reason,
            "suspended_at": self.suspension_time,
            "hours_since_suspension": time_since_suspension / 3600,
            "can_recover_at": can_recover_at,
            "hours_until_recovery": max(0, (can_recover_at - time.time()) / 3600)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        current_pnl = self.current_daily_pnl.to_dict() if self.current_daily_pnl else None
        suspension_info = self.get_suspension_info()
        
        return {
            "trading_state": self.trading_state.value,
            "daily_loss_limit_pct": self.daily_loss_limit_pct * 100,
            "current_daily_pnl": current_pnl,
            "suspension_info": suspension_info,
            "statistics": self.stats,
            "recovery_settings": {
                "recovery_delay_hours": self.recovery_delay_hours,
                "auto_suspend_enabled": self.enable_auto_suspend
            }
        }
    
    def reset_day(self) -> None:
        """Reset current day (use carefully - for testing)"""
        if self.current_daily_pnl:
            self.daily_history[self.current_daily_pnl.date] = self.current_daily_pnl
        self.current_daily_pnl = None
        logger.warning("Daily tracking reset")
    
    async def simulate_daily_loss(self, loss_pct: float) -> None:
        """Simulate daily loss for testing"""
        if not self.current_daily_pnl:
            current_date = self.get_current_date()
            await self._initialize_new_day(current_date, 10000.0)
        
        simulated_equity = self.current_daily_pnl.starting_equity * (1 + loss_pct)
        await self.track_daily_pnl(simulated_equity, loss_pct * self.current_daily_pnl.starting_equity, 0)
        
        logger.warning("Simulated daily loss",
                      loss_pct=loss_pct * 100,
                      simulated_equity=simulated_equity)