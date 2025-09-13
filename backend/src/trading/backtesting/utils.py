"""
Backtesting Utilities

Helper functions and configuration classes for the backtesting system including
time series processing, data validation, and configuration management.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BacktestStatus(Enum):
    """Backtest execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BacktestConfig:
    """Configuration for backtesting runs"""

    # Strategy configuration
    strategy_name: str
    strategy_params: Dict[str, Any]

    # Time period
    start_date: datetime
    end_date: datetime
    timeframe: str = '1h'

    # Trading parameters
    symbols: List[str]
    initial_capital: float = 10000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0001

    # Risk management
    max_position_size: float = 0.1  # 10% of portfolio
    max_total_exposure: float = 0.8  # 80% of portfolio
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None

    # Execution settings
    warmup_period: int = 50  # Periods needed for indicators
    rebalance_frequency: str = '1h'  # How often to check for signals

    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_config()

    def _validate_config(self):
        """Validate configuration parameters"""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")

        if self.initial_capital <= 0:
            raise ValueError("Initial capital must be positive")

        if not self.symbols:
            raise ValueError("At least one symbol must be specified")

        if not 0 < self.max_position_size <= 1:
            raise ValueError("Max position size must be between 0 and 1")

        if not 0 < self.max_total_exposure <= 1:
            raise ValueError("Max total exposure must be between 0 and 1")

        if self.warmup_period < 0:
            raise ValueError("Warmup period must be non-negative")


class TimeSeriesUtils:
    """Utilities for time series processing in backtesting"""

    @staticmethod
    def resample_ohlcv(data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample OHLCV data to different timeframe

        Args:
            data: DataFrame with columns [timestamp, open, high, low, close, volume]
            timeframe: Target timeframe ('1h', '4h', '1d', etc.)

        Returns:
            Resampled DataFrame
        """
        if data.empty:
            return data

        # Set timestamp as index
        df = data.set_index('timestamp')

        # Define resampling rules
        agg_rules = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }

        # Map timeframe to pandas frequency
        freq_map = {
            '1m': '1T',
            '5m': '5T',
            '15m': '15T',
            '30m': '30T',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D',
            '1w': '1W'
        }

        freq = freq_map.get(timeframe, '1H')

        # Resample data
        resampled = df.resample(freq).agg(agg_rules).dropna()

        # Reset index
        resampled = resampled.reset_index()

        return resampled

    @staticmethod
    def align_timeframes(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Align multiple symbol datasets to common timestamps

        Args:
            data_dict: Dictionary of symbol -> DataFrame mappings

        Returns:
            Dictionary with aligned DataFrames
        """
        if not data_dict:
            return data_dict

        # Find common time range
        all_timestamps = []
        for df in data_dict.values():
            if not df.empty:
                all_timestamps.extend(df['timestamp'].tolist())

        if not all_timestamps:
            return data_dict

        # Create common timestamp range
        min_time = min(all_timestamps)
        max_time = max(all_timestamps)

        # Align each dataset
        aligned_data = {}
        for symbol, df in data_dict.items():
            if df.empty:
                aligned_data[symbol] = df
                continue

            # Filter to common time range
            mask = (df['timestamp'] >= min_time) & (df['timestamp'] <= max_time)
            aligned_data[symbol] = df[mask].reset_index(drop=True)

        return aligned_data

    @staticmethod
    def fill_missing_data(data: pd.DataFrame, method: str = 'forward') -> pd.DataFrame:
        """
        Fill missing data in OHLCV DataFrame

        Args:
            data: OHLCV DataFrame
            method: Fill method ('forward', 'backward', 'interpolate')

        Returns:
            DataFrame with filled data
        """
        if data.empty:
            return data

        df = data.copy()

        if method == 'forward':
            # Forward fill OHLC, set volume to 0
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].fillna(method='ffill')
            df['volume'] = df['volume'].fillna(0)
        elif method == 'backward':
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].fillna(method='bfill')
            df['volume'] = df['volume'].fillna(0)
        elif method == 'interpolate':
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].interpolate()
            df['volume'] = df['volume'].fillna(0)

        return df

    @staticmethod
    def detect_market_hours(data: pd.DataFrame, symbol: str = 'BTC') -> Tuple[int, int]:
        """
        Detect active trading hours from historical data

        Args:
            data: OHLCV DataFrame
            symbol: Trading symbol

        Returns:
            Tuple of (start_hour, end_hour) in UTC
        """
        if data.empty:
            return (0, 23)  # Default to 24/7 for crypto

        # For crypto, typically 24/7 trading
        crypto_symbols = ['BTC', 'ETH', 'LINK', 'WBTC']
        if symbol in crypto_symbols:
            return (0, 23)

        # For traditional assets, analyze volume patterns
        df = data.copy()
        df['hour'] = df['timestamp'].dt.hour

        # Calculate average volume by hour
        hourly_volume = df.groupby('hour')['volume'].mean()

        # Find hours with significant volume (> 50% of max)
        volume_threshold = hourly_volume.max() * 0.5
        active_hours = hourly_volume[hourly_volume >= volume_threshold]

        if active_hours.empty:
            return (0, 23)

        start_hour = active_hours.index.min()
        end_hour = active_hours.index.max()

        return (start_hour, end_hour)


class DataValidator:
    """Data validation utilities for backtesting"""

    @staticmethod
    def validate_ohlcv_data(data: pd.DataFrame, symbol: str) -> Tuple[bool, List[str]]:
        """
        Validate OHLCV data quality

        Args:
            data: OHLCV DataFrame
            symbol: Symbol name for error messages

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if data.empty:
            errors.append(f"{symbol}: No data available")
            return False, errors

        # Check required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            errors.append(f"{symbol}: Missing columns: {missing_cols}")

        # Check for negative prices
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in data.columns and (data[col] <= 0).any():
                errors.append(f"{symbol}: Found non-positive prices in {col}")

        # Check OHLC relationships
        if all(col in data.columns for col in price_cols):
            invalid_ohlc = (
                (data['high'] < data['low']) |
                (data['high'] < data['open']) |
                (data['high'] < data['close']) |
                (data['low'] > data['open']) |
                (data['low'] > data['close'])
            )
            if invalid_ohlc.any():
                errors.append(f"{symbol}: Found {invalid_ohlc.sum()} invalid OHLC relationships")

        # Check for negative volume
        if 'volume' in data.columns and (data['volume'] < 0).any():
            errors.append(f"{symbol}: Found negative volume values")

        # Check timestamp ordering
        if 'timestamp' in data.columns:
            if not data['timestamp'].is_monotonic_increasing:
                errors.append(f"{symbol}: Timestamps not in chronological order")

        # Check for excessive price gaps (>50% change)
        if 'close' in data.columns and len(data) > 1:
            price_changes = data['close'].pct_change().abs()
            large_gaps = price_changes > 0.5
            if large_gaps.any():
                errors.append(f"{symbol}: Found {large_gaps.sum()} large price gaps (>50%)")

        # Check data completeness
        missing_data_pct = data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100
        if missing_data_pct > 5:
            errors.append(f"{symbol}: High missing data percentage: {missing_data_pct:.1f}%")

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def validate_backtest_config(config: BacktestConfig) -> Tuple[bool, List[str]]:
        """
        Validate backtest configuration

        Args:
            config: BacktestConfig object

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            # This will call the validation in __post_init__
            config._validate_config()
        except ValueError as e:
            errors.append(str(e))

        # Additional business logic validation
        duration = config.end_date - config.start_date
        if duration.days < 1:
            errors.append("Backtest period must be at least 1 day")

        if duration.days > 365 * 5:
            errors.append("Backtest period too long (max 5 years)")

        # Check symbol validity
        valid_symbols = ['BTC', 'ETH', 'LINK', 'WBTC']
        invalid_symbols = [s for s in config.symbols if s not in valid_symbols]
        if invalid_symbols:
            errors.append(f"Invalid symbols: {invalid_symbols}")

        is_valid = len(errors) == 0
        return is_valid, errors


class BacktestResultsFormatter:
    """Format backtest results for different output formats"""

    @staticmethod
    def to_json_summary(results: Dict) -> Dict:
        """Convert results to JSON-safe summary format"""
        summary = {
            'strategy_name': results.get('strategy_name', 'Unknown'),
            'symbols': results.get('symbols', []),
            'start_date': results.get('start_date'),
            'end_date': results.get('end_date'),
            'performance': {
                'initial_capital': results.get('initial_capital'),
                'final_value': results.get('final_value'),
                'total_return_pct': results.get('total_return_pct'),
                'annualized_return_pct': results.get('annualized_return_pct'),
                'sharpe_ratio': results.get('sharpe_ratio'),
                'max_drawdown_pct': results.get('max_drawdown_pct'),
                'win_rate_pct': results.get('win_rate_pct'),
                'total_trades': results.get('total_trades')
            },
            'metadata': {
                'backtest_duration_days': results.get('total_duration_days'),
                'created_at': datetime.utcnow().isoformat(),
                'version': '1.0.0'
            }
        }
        return summary

    @staticmethod
    def to_csv_trades(trade_history: List) -> str:
        """Convert trade history to CSV format"""
        if not trade_history:
            return "timestamp,symbol,side,size,price,commission,realized_pnl\n"

        lines = ["timestamp,symbol,side,size,price,commission,realized_pnl"]

        for trade in trade_history:
            line = f"{trade.timestamp.isoformat()},{trade.symbol},{trade.side},{trade.size},{trade.price},{trade.commission},{trade.realized_pnl}"
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def create_performance_chart_data(portfolio_history: List) -> List[Dict]:
        """Create data for performance charts"""
        if not portfolio_history:
            return []

        chart_data = []
        for snapshot in portfolio_history:
            chart_data.append({
                'timestamp': snapshot.timestamp.isoformat(),
                'portfolio_value': float(snapshot.total_value),
                'cash_balance': float(snapshot.cash_balance),
                'positions_value': float(snapshot.positions_value),
                'realized_pnl': float(snapshot.realized_pnl),
                'unrealized_pnl': float(snapshot.unrealized_pnl)
            })

        return chart_data


def calculate_technical_indicators(data: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """
    Calculate technical indicators for strategy backtesting

    Args:
        data: OHLCV DataFrame
        config: Indicator configuration

    Returns:
        DataFrame with added indicator columns
    """
    if data.empty:
        return data

    df = data.copy()

    # Moving averages
    if 'sma_periods' in config:
        for period in config['sma_periods']:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()

    if 'ema_periods' in config:
        for period in config['ema_periods']:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()

    # RSI
    if 'rsi_period' in config:
        period = config['rsi_period']
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    if 'macd_config' in config:
        macd_config = config['macd_config']
        exp1 = df['close'].ewm(span=macd_config.get('fast', 12)).mean()
        exp2 = df['close'].ewm(span=macd_config.get('slow', 26)).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=macd_config.get('signal', 9)).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

    # Bollinger Bands
    if 'bollinger_config' in config:
        bb_config = config['bollinger_config']
        period = bb_config.get('period', 20)
        std_dev = bb_config.get('std_dev', 2)

        df['bb_middle'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (bb_std * std_dev)

    return df