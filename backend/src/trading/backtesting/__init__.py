"""
WolfHunt Backtesting Module

Production-ready backtesting system with mock wallet, historical data,
and comprehensive performance metrics for dYdX trading strategies.
"""

from .engine import BacktestEngine
from .mock_wallet import MockWallet, Portfolio
from .historical_data import HistoricalDataService
from .performance import PerformanceCalculator
from .utils import TimeSeriesUtils, BacktestConfig

__all__ = [
    'BacktestEngine',
    'MockWallet',
    'Portfolio',
    'HistoricalDataService',
    'PerformanceCalculator',
    'TimeSeriesUtils',
    'BacktestConfig'
]

__version__ = "1.0.0"