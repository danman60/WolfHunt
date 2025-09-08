"""Data Access Objects for database operations."""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging
from decimal import Decimal

from .models import User, Trade, Position, StrategySignal, Configuration, Alert

logger = logging.getLogger(__name__)


class TradingDAO:
    """Data Access Object for trading operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def save_trade(self, trade_data: Dict[str, Any], user_id: int) -> Trade:
        """Save a trade execution record."""
        trade = Trade(
            user_id=user_id,
            order_id=trade_data["order_id"],
            client_order_id=trade_data.get("client_order_id"),
            symbol=trade_data["symbol"],
            side=trade_data["side"],
            order_type=trade_data["order_type"],
            size=trade_data["size"],
            price=trade_data["price"],
            filled_size=trade_data.get("filled_size", trade_data["size"]),
            remaining_size=trade_data.get("remaining_size", 0.0),
            notional_value=trade_data["notional_value"],
            commission=trade_data.get("commission", 0.0),
            realized_pnl=trade_data.get("realized_pnl"),
            status=trade_data["status"],
            strategy_name=trade_data.get("strategy_name"),
            signal_strength=trade_data.get("signal_strength"),
            entry_reason=trade_data.get("entry_reason"),
            stop_loss_price=trade_data.get("stop_loss_price"),
            take_profit_price=trade_data.get("take_profit_price"),
            timestamp=trade_data.get("timestamp", datetime.utcnow())
        )
        
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return trade
    
    def get_trade_history(
        self, 
        user_id: int,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Trade]:
        """Retrieve trade history with filters."""
        query = self.db.query(Trade).filter(Trade.user_id == user_id)
        
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        
        if start_date:
            query = query.filter(Trade.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Trade.timestamp <= end_date)
        
        if strategy_name:
            query = query.filter(Trade.strategy_name == strategy_name)
        
        return query.order_by(desc(Trade.timestamp)).offset(offset).limit(limit).all()
    
    async def save_position(self, position_data: Dict[str, Any], user_id: int) -> Position:
        """Save or update a position."""
        # Check if position already exists
        existing_position = self.db.query(Position).filter(
            and_(
                Position.user_id == user_id,
                Position.symbol == position_data["symbol"],
                Position.is_open == True
            )
        ).first()
        
        if existing_position:
            # Update existing position
            for key, value in position_data.items():
                if hasattr(existing_position, key):
                    setattr(existing_position, key, value)
            existing_position.updated_at = datetime.utcnow()
            position = existing_position
        else:
            # Create new position
            position = Position(
                user_id=user_id,
                symbol=position_data["symbol"],
                side=position_data["side"],
                size=position_data["size"],
                entry_price=position_data["entry_price"],
                mark_price=position_data.get("mark_price"),
                unrealized_pnl=position_data.get("unrealized_pnl"),
                unrealized_pnl_percent=position_data.get("unrealized_pnl_percent"),
                notional_value=position_data["notional_value"],
                margin_used=position_data["margin_used"],
                leverage=position_data["leverage"],
                stop_loss_price=position_data.get("stop_loss_price"),
                take_profit_price=position_data.get("take_profit_price"),
                liquidation_price=position_data.get("liquidation_price"),
                strategy_name=position_data.get("strategy_name"),
                entry_reason=position_data.get("entry_reason"),
                opened_at=position_data.get("opened_at", datetime.utcnow())
            )
            self.db.add(position)
        
        self.db.commit()
        self.db.refresh(position)
        return position
    
    def get_current_positions(self, user_id: int, symbol: Optional[str] = None) -> List[Position]:
        """Get all current open positions."""
        query = self.db.query(Position).filter(
            and_(Position.user_id == user_id, Position.is_open == True)
        )
        
        if symbol:
            query = query.filter(Position.symbol == symbol)
        
        return query.order_by(desc(Position.opened_at)).all()
    
    async def close_position(self, position_id: int, close_price: float, realized_pnl: float) -> bool:
        """Close a position."""
        position = self.db.query(Position).filter(Position.id == position_id).first()
        if not position:
            return False
        
        position.is_open = False
        position.closed_at = datetime.utcnow()
        position.mark_price = close_price
        
        # Calculate final unrealized P&L (which becomes realized)
        if position.side == "LONG":
            position.unrealized_pnl = (close_price - position.entry_price) * position.size
        else:
            position.unrealized_pnl = (position.entry_price - close_price) * position.size
        
        self.db.commit()
        return True
    
    def calculate_daily_pnl(self, user_id: int, date: datetime) -> Dict[str, float]:
        """Calculate P&L for a specific date."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Realized P&L from trades
        realized_pnl = self.db.query(func.sum(Trade.realized_pnl)).filter(
            and_(
                Trade.user_id == user_id,
                Trade.timestamp >= start_of_day,
                Trade.timestamp < end_of_day,
                Trade.realized_pnl.isnot(None)
            )
        ).scalar() or 0.0
        
        # Unrealized P&L from current positions (snapshot at end of day)
        unrealized_pnl = self.db.query(func.sum(Position.unrealized_pnl)).filter(
            and_(
                Position.user_id == user_id,
                Position.is_open == True,
                Position.updated_at < end_of_day
            )
        ).scalar() or 0.0
        
        return {
            "realized_pnl": float(realized_pnl),
            "unrealized_pnl": float(unrealized_pnl),
            "total_pnl": float(realized_pnl) + float(unrealized_pnl)
        }
    
    def get_performance_metrics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get trades in the period
        trades = self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.timestamp >= start_date,
                Trade.status == "FILLED"
            )
        ).all()
        
        if not trades:
            return {"error": "No trades in the specified period"}
        
        # Calculate basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if (t.realized_pnl or 0) > 0])
        losing_trades = len([t for t in trades if (t.realized_pnl or 0) < 0])
        
        total_pnl = sum(t.realized_pnl or 0 for t in trades)
        total_volume = sum(t.notional_value for t in trades)
        total_commission = sum(t.commission for t in trades)
        
        # Calculate ratios
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Average win/loss
        wins = [t.realized_pnl for t in trades if (t.realized_pnl or 0) > 0]
        losses = [t.realized_pnl for t in trades if (t.realized_pnl or 0) < 0]
        
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        # Risk/reward ratio
        risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Calculate daily returns for Sharpe ratio
        daily_pnls = {}
        for trade in trades:
            date = trade.timestamp.date()
            if date not in daily_pnls:
                daily_pnls[date] = 0
            daily_pnls[date] += trade.realized_pnl or 0
        
        daily_returns = list(daily_pnls.values())
        
        # Sharpe ratio (assuming risk-free rate of 0)
        if len(daily_returns) > 1:
            avg_daily_return = sum(daily_returns) / len(daily_returns)
            volatility = (sum((r - avg_daily_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
            sharpe_ratio = avg_daily_return / volatility if volatility != 0 else 0
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in sorted(trades, key=lambda x: x.timestamp):
            cumulative_pnl += trade.realized_pnl or 0
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            drawdown = (peak - cumulative_pnl) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            "period_days": days,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "total_volume": total_volume,
            "total_commission": total_commission,
            "net_pnl": total_pnl - total_commission,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "risk_reward_ratio": risk_reward_ratio,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown
        }
    
    async def save_strategy_signal(self, signal_data: Dict[str, Any], user_id: int) -> StrategySignal:
        """Save a strategy signal."""
        signal = StrategySignal(
            user_id=user_id,
            strategy_name=signal_data["strategy_name"],
            symbol=signal_data["symbol"],
            signal_type=signal_data["signal_type"],
            strength=signal_data.get("strength"),
            confidence=signal_data.get("confidence"),
            price=signal_data["price"],
            volume=signal_data.get("volume"),
            indicators=signal_data.get("indicators"),
            reasoning=signal_data.get("reasoning"),
            risk_score=signal_data.get("risk_score"),
            timestamp=signal_data.get("timestamp", datetime.utcnow())
        )
        
        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)
        return signal
    
    def get_recent_signals(
        self, 
        user_id: int,
        strategy_name: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[StrategySignal]:
        """Get recent strategy signals."""
        query = self.db.query(StrategySignal).filter(StrategySignal.user_id == user_id)
        
        if strategy_name:
            query = query.filter(StrategySignal.strategy_name == strategy_name)
        
        if symbol:
            query = query.filter(StrategySignal.symbol == symbol)
        
        return query.order_by(desc(StrategySignal.timestamp)).limit(limit).all()


class UserDAO:
    """Data Access Object for user operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def update_user(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        return self.update_user(user_id, {"last_login": datetime.utcnow()})


class ConfigurationDAO:
    """Data Access Object for configuration management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_config(
        self, 
        category: str, 
        key: str, 
        user_id: Optional[int] = None
    ) -> Optional[Configuration]:
        """Get a configuration value."""
        query = self.db.query(Configuration).filter(
            and_(
                Configuration.category == category,
                Configuration.key == key,
                Configuration.is_active == True
            )
        )
        
        if user_id is not None:
            query = query.filter(Configuration.user_id == user_id)
        else:
            query = query.filter(Configuration.user_id.is_(None))
        
        return query.first()
    
    async def save_config(
        self, 
        category: str, 
        key: str, 
        value: Any, 
        value_type: str,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        updated_by: Optional[int] = None
    ) -> Configuration:
        """Save or update a configuration."""
        existing = self.get_config(category, key, user_id)
        
        if existing:
            # Update existing configuration
            existing.previous_value = existing.value
            existing.value = value
            existing.version += 1
            existing.updated_at = datetime.utcnow()
            existing.updated_by = updated_by
            config = existing
        else:
            # Create new configuration
            config = Configuration(
                user_id=user_id,
                category=category,
                key=key,
                value=value,
                value_type=value_type,
                description=description,
                updated_by=updated_by
            )
            self.db.add(config)
        
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def get_category_configs(
        self, 
        category: str, 
        user_id: Optional[int] = None
    ) -> List[Configuration]:
        """Get all configurations for a category."""
        query = self.db.query(Configuration).filter(
            and_(
                Configuration.category == category,
                Configuration.is_active == True
            )
        )
        
        if user_id is not None:
            query = query.filter(Configuration.user_id == user_id)
        else:
            query = query.filter(Configuration.user_id.is_(None))
        
        return query.all()


class AlertDAO:
    """Data Access Object for alert management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> Alert:
        """Create a new alert."""
        alert = Alert(
            user_id=alert_data.get("user_id"),
            alert_type=alert_data["alert_type"],
            severity=alert_data["severity"],
            title=alert_data["title"],
            message=alert_data["message"],
            symbol=alert_data.get("symbol"),
            strategy_name=alert_data.get("strategy_name"),
            related_trade_id=alert_data.get("related_trade_id"),
            related_position_id=alert_data.get("related_position_id"),
            metadata=alert_data.get("metadata"),
            timestamp=alert_data.get("timestamp", datetime.utcnow())
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert
    
    def get_user_alerts(
        self, 
        user_id: int, 
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Alert]:
        """Get alerts for a user."""
        query = self.db.query(Alert).filter(Alert.user_id == user_id)
        
        if unread_only:
            query = query.filter(Alert.is_read == False)
        
        return query.order_by(desc(Alert.timestamp)).limit(limit).all()
    
    def mark_alert_read(self, alert_id: int, user_id: int) -> bool:
        """Mark an alert as read."""
        alert = self.db.query(Alert).filter(
            and_(Alert.id == alert_id, Alert.user_id == user_id)
        ).first()
        
        if not alert:
            return False
        
        alert.is_read = True
        alert.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def get_system_alerts(self, severity: Optional[str] = None, limit: int = 100) -> List[Alert]:
        """Get system-wide alerts."""
        query = self.db.query(Alert).filter(Alert.user_id.is_(None))
        
        if severity:
            query = query.filter(Alert.severity == severity)
        
        return query.order_by(desc(Alert.timestamp)).limit(limit).all()