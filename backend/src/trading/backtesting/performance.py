"""
Performance Metrics Calculator for Backtesting

Comprehensive trading performance analysis including Sharpe ratio, maximum drawdown,
win rate, profit factor, and risk-adjusted returns for backtesting evaluation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """
    Production-grade performance metrics calculator for trading backtests

    Features:
    - Sharpe ratio with configurable risk-free rate
    - Maximum drawdown and drawdown duration
    - Win rate and profit factor
    - Risk-adjusted returns and volatility
    - Trade analysis and statistics
    - Benchmark comparison capabilities
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize performance calculator

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation (default: 2%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_comprehensive_metrics(self, portfolio_history: List,
                                      trade_history: List,
                                      initial_capital: float) -> Dict:
        """
        Calculate comprehensive performance metrics from backtest results

        Args:
            portfolio_history: List of Portfolio snapshots
            trade_history: List of Trade objects
            initial_capital: Starting capital amount

        Returns:
            Dictionary containing all performance metrics
        """
        if not portfolio_history:
            return {"error": "No portfolio history provided"}

        logger.info(f"Calculating metrics for {len(portfolio_history)} portfolio snapshots, {len(trade_history)} trades")

        # Convert portfolio history to DataFrame
        portfolio_df = self._portfolio_history_to_df(portfolio_history)

        # Basic return metrics
        basic_metrics = self._calculate_basic_metrics(portfolio_df, initial_capital)

        # Risk metrics
        risk_metrics = self._calculate_risk_metrics(portfolio_df)

        # Trade analysis
        trade_metrics = self._calculate_trade_metrics(trade_history)

        # Drawdown analysis
        drawdown_metrics = self._calculate_drawdown_metrics(portfolio_df)

        # Time-based analysis
        time_metrics = self._calculate_time_metrics(portfolio_df, trade_history)

        # Combine all metrics
        all_metrics = {
            **basic_metrics,
            **risk_metrics,
            **trade_metrics,
            **drawdown_metrics,
            **time_metrics
        }

        logger.info(f"Performance calculation complete: {all_metrics.get('total_return_pct', 0):.2f}% return")
        return all_metrics

    def _portfolio_history_to_df(self, portfolio_history: List) -> pd.DataFrame:
        """Convert portfolio history to DataFrame for analysis"""
        data = []
        for snapshot in portfolio_history:
            data.append({
                'timestamp': snapshot.timestamp,
                'total_value': float(snapshot.total_value),
                'cash_balance': float(snapshot.cash_balance),
                'positions_value': float(snapshot.positions_value),
                'unrealized_pnl': float(snapshot.unrealized_pnl),
                'realized_pnl': float(snapshot.realized_pnl)
            })

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Calculate returns
        df['returns'] = df['total_value'].pct_change().fillna(0)
        df['cumulative_returns'] = (1 + df['returns']).cumprod() - 1

        return df

    def _calculate_basic_metrics(self, portfolio_df: pd.DataFrame, initial_capital: float) -> Dict:
        """Calculate basic return metrics"""
        final_value = portfolio_df['total_value'].iloc[-1]
        total_return = final_value - initial_capital
        total_return_pct = (total_return / initial_capital) * 100

        # Annualized return
        days = (portfolio_df['timestamp'].iloc[-1] - portfolio_df['timestamp'].iloc[0]).days
        years = max(days / 365.25, 1/365.25)  # Minimum 1 day
        annualized_return = ((final_value / initial_capital) ** (1/years) - 1) * 100

        return {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': round(total_return_pct, 2),
            'annualized_return_pct': round(annualized_return, 2),
            'backtest_days': days
        }

    def _calculate_risk_metrics(self, portfolio_df: pd.DataFrame) -> Dict:
        """Calculate risk and volatility metrics"""
        returns = portfolio_df['returns'].dropna()

        if len(returns) < 2:
            return {
                'sharpe_ratio': 0,
                'volatility_pct': 0,
                'downside_deviation_pct': 0
            }

        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252) * 100  # Assuming daily data

        # Sharpe ratio
        excess_returns = returns - (self.risk_free_rate / 252)  # Daily risk-free rate
        sharpe_ratio = (excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if excess_returns.std() > 0 else 0

        # Downside deviation
        negative_returns = returns[returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) * 100 if len(negative_returns) > 0 else 0

        # Sortino ratio
        sortino_ratio = (excess_returns.mean() / negative_returns.std() * np.sqrt(252)) if len(negative_returns) > 0 and negative_returns.std() > 0 else 0

        return {
            'sharpe_ratio': round(sharpe_ratio, 3),
            'sortino_ratio': round(sortino_ratio, 3),
            'volatility_pct': round(volatility, 2),
            'downside_deviation_pct': round(downside_deviation, 2)
        }

    def _calculate_trade_metrics(self, trade_history: List) -> Dict:
        """Calculate trade-specific metrics"""
        if not trade_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate_pct': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0
            }

        # Convert trades to list of P&L values
        trade_pnls = [float(trade.realized_pnl) for trade in trade_history if hasattr(trade, 'realized_pnl')]

        if not trade_pnls:
            return {'total_trades': len(trade_history), 'win_rate_pct': 0}

        # Basic trade statistics
        total_trades = len(trade_pnls)
        winning_trades = len([pnl for pnl in trade_pnls if pnl > 0])
        losing_trades = len([pnl for pnl in trade_pnls if pnl < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Profit/Loss analysis
        wins = [pnl for pnl in trade_pnls if pnl > 0]
        losses = [pnl for pnl in trade_pnls if pnl < 0]

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0

        # Profit factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0

        # Risk-reward ratio
        risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss < 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_pct': round(win_rate, 1),
            'profit_factor': round(profit_factor, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'largest_win': round(largest_win, 2),
            'largest_loss': round(largest_loss, 2),
            'risk_reward_ratio': round(risk_reward_ratio, 2)
        }

    def _calculate_drawdown_metrics(self, portfolio_df: pd.DataFrame) -> Dict:
        """Calculate maximum drawdown and related metrics"""
        if len(portfolio_df) < 2:
            return {
                'max_drawdown_pct': 0,
                'max_drawdown_duration_days': 0,
                'current_drawdown_pct': 0
            }

        values = portfolio_df['total_value']
        peak = values.expanding().max()
        drawdown = (values - peak) / peak * 100

        max_drawdown = drawdown.min()
        current_drawdown = drawdown.iloc[-1]

        # Calculate drawdown duration
        is_drawdown = drawdown < -0.01  # Consider >0.01% as drawdown
        drawdown_periods = []
        current_period = 0

        for in_drawdown in is_drawdown:
            if in_drawdown:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0

        if current_period > 0:
            drawdown_periods.append(current_period)

        max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0

        # Convert periods to days (assuming daily snapshots)
        max_drawdown_duration_days = max_drawdown_duration

        return {
            'max_drawdown_pct': round(max_drawdown, 2),
            'max_drawdown_duration_days': max_drawdown_duration_days,
            'current_drawdown_pct': round(current_drawdown, 2)
        }

    def _calculate_time_metrics(self, portfolio_df: pd.DataFrame, trade_history: List) -> Dict:
        """Calculate time-based performance metrics"""
        if len(portfolio_df) < 2:
            return {}

        start_time = portfolio_df['timestamp'].iloc[0]
        end_time = portfolio_df['timestamp'].iloc[-1]
        total_duration = end_time - start_time

        # Trading frequency
        trades_per_day = len(trade_history) / max(total_duration.days, 1)

        # Calculate monthly returns
        portfolio_df_monthly = portfolio_df.set_index('timestamp').resample('M')['total_value'].last()
        monthly_returns = portfolio_df_monthly.pct_change().dropna()

        # Best/worst periods
        best_month = monthly_returns.max() * 100 if len(monthly_returns) > 0 else 0
        worst_month = monthly_returns.min() * 100 if len(monthly_returns) > 0 else 0

        return {
            'backtest_start': start_time.isoformat(),
            'backtest_end': end_time.isoformat(),
            'total_duration_days': total_duration.days,
            'trades_per_day': round(trades_per_day, 2),
            'best_month_pct': round(best_month, 2),
            'worst_month_pct': round(worst_month, 2)
        }

    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = None) -> float:
        """
        Calculate Sharpe ratio for a series of returns

        Args:
            returns: Series of period returns
            risk_free_rate: Annual risk-free rate (defaults to instance setting)

        Returns:
            Sharpe ratio (annualized)
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate

        if len(returns) < 2 or returns.std() == 0:
            return 0.0

        # Assume daily returns, convert risk-free rate to daily
        daily_rf_rate = risk_free_rate / 252
        excess_returns = returns - daily_rf_rate

        sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        return round(sharpe, 3)

    def calculate_max_drawdown(self, portfolio_values: pd.Series) -> Tuple[float, int]:
        """
        Calculate maximum drawdown and its duration

        Args:
            portfolio_values: Series of portfolio values

        Returns:
            Tuple of (max_drawdown_percentage, max_duration_periods)
        """
        if len(portfolio_values) < 2:
            return 0.0, 0

        peak = portfolio_values.expanding().max()
        drawdown = (portfolio_values - peak) / peak

        max_drawdown = drawdown.min() * 100  # Convert to percentage

        # Calculate duration
        is_drawdown = drawdown < -0.001  # 0.1% threshold
        max_duration = 0
        current_duration = 0

        for in_dd in is_drawdown:
            if in_dd:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return round(max_drawdown, 2), max_duration

    def calculate_win_rate(self, trades: List) -> float:
        """Calculate win rate from trade list"""
        if not trades:
            return 0.0

        winning_trades = sum(1 for trade in trades if hasattr(trade, 'realized_pnl') and float(trade.realized_pnl) > 0)
        return round(winning_trades / len(trades) * 100, 1)

    def calculate_profit_factor(self, trades: List) -> float:
        """Calculate profit factor from trade list"""
        if not trades:
            return 0.0

        wins = sum(float(trade.realized_pnl) for trade in trades
                  if hasattr(trade, 'realized_pnl') and float(trade.realized_pnl) > 0)

        losses = abs(sum(float(trade.realized_pnl) for trade in trades
                        if hasattr(trade, 'realized_pnl') and float(trade.realized_pnl) < 0))

        if losses == 0:
            return float('inf') if wins > 0 else 0.0

        return round(wins / losses, 2)

    def generate_performance_report(self, metrics: Dict) -> str:
        """Generate a formatted performance report"""
        report = f"""
BACKTEST PERFORMANCE REPORT
{'='*50}

RETURNS:
  Initial Capital:     ${metrics.get('initial_capital', 0):,.2f}
  Final Value:         ${metrics.get('final_value', 0):,.2f}
  Total Return:        {metrics.get('total_return_pct', 0):+.2f}%
  Annualized Return:   {metrics.get('annualized_return_pct', 0):+.2f}%

RISK METRICS:
  Sharpe Ratio:        {metrics.get('sharpe_ratio', 0):.3f}
  Sortino Ratio:       {metrics.get('sortino_ratio', 0):.3f}
  Volatility:          {metrics.get('volatility_pct', 0):.2f}%
  Max Drawdown:        {metrics.get('max_drawdown_pct', 0):.2f}%

TRADE ANALYSIS:
  Total Trades:        {metrics.get('total_trades', 0):,}
  Win Rate:            {metrics.get('win_rate_pct', 0):.1f}%
  Profit Factor:       {metrics.get('profit_factor', 0):.2f}
  Avg Win:             ${metrics.get('avg_win', 0):.2f}
  Avg Loss:            ${metrics.get('avg_loss', 0):.2f}

DURATION:
  Backtest Period:     {metrics.get('total_duration_days', 0):,} days
  Trades per Day:      {metrics.get('trades_per_day', 0):.2f}
"""
        return report

    def compare_to_benchmark(self, strategy_metrics: Dict, benchmark_return_pct: float) -> Dict:
        """Compare strategy performance to benchmark"""
        strategy_return = strategy_metrics.get('total_return_pct', 0)
        excess_return = strategy_return - benchmark_return_pct

        alpha = excess_return  # Simplified alpha calculation

        return {
            'benchmark_return_pct': benchmark_return_pct,
            'strategy_return_pct': strategy_return,
            'excess_return_pct': round(excess_return, 2),
            'alpha': round(alpha, 2),
            'outperformed_benchmark': strategy_return > benchmark_return_pct
        }