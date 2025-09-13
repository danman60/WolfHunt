"""
Backtesting Engine Core

Production-grade backtesting orchestration system that leverages existing
trading infrastructure with historical data replay and comprehensive
performance analysis.
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import uuid
from decimal import Decimal

from .mock_wallet import MockWallet, Portfolio, Trade
from .historical_data import HistoricalDataService
from .performance import PerformanceCalculator
from .utils import BacktestConfig, BacktestStatus, TimeSeriesUtils, DataValidator, calculate_technical_indicators

# Import existing strategy classes
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Production-grade backtesting engine with comprehensive strategy testing

    Features:
    - Historical data replay with realistic timing
    - Integration with existing trading strategies
    - Mock wallet with realistic execution
    - Comprehensive performance metrics
    - Real-time progress tracking
    - Error handling and recovery
    """

    def __init__(self):
        self.historical_data_service = None
        self.performance_calculator = PerformanceCalculator()
        self.active_backtests: Dict[str, Dict] = {}

    async def run_backtest(self, config: BacktestConfig, progress_callback=None) -> Dict:
        """
        Execute a complete backtesting run

        Args:
            config: Backtest configuration
            progress_callback: Optional callback for progress updates

        Returns:
            Comprehensive backtest results dictionary
        """
        backtest_id = str(uuid.uuid4())
        logger.info(f"Starting backtest {backtest_id}: {config.strategy_name} on {config.symbols}")

        # Initialize backtest tracking
        self.active_backtests[backtest_id] = {
            'status': BacktestStatus.RUNNING,
            'config': config,
            'start_time': datetime.utcnow(),
            'progress': 0.0
        }

        try:
            # Validate configuration
            is_valid, errors = DataValidator.validate_backtest_config(config)
            if not is_valid:
                raise ValueError(f"Invalid configuration: {errors}")

            # Initialize components
            mock_wallet = MockWallet(
                initial_capital=config.initial_capital,
                commission_rate=config.commission_rate
            )

            # Fetch historical data
            await self._update_progress(backtest_id, 10, "Fetching historical data", progress_callback)
            historical_data = await self._fetch_historical_data(config)

            # Validate data quality
            await self._update_progress(backtest_id, 20, "Validating data quality", progress_callback)
            await self._validate_historical_data(historical_data, config.symbols)

            # Initialize strategy
            await self._update_progress(backtest_id, 30, "Initializing strategy", progress_callback)
            strategy = await self._initialize_strategy(config)

            # Execute backtesting simulation
            await self._update_progress(backtest_id, 40, "Running simulation", progress_callback)
            simulation_results = await self._run_simulation(
                mock_wallet, historical_data, strategy, config, backtest_id, progress_callback
            )

            # Calculate performance metrics
            await self._update_progress(backtest_id, 90, "Calculating performance metrics", progress_callback)
            performance_metrics = self.performance_calculator.calculate_comprehensive_metrics(
                mock_wallet.portfolio_history,
                mock_wallet.trade_history,
                config.initial_capital
            )

            # Compile final results
            results = await self._compile_results(
                backtest_id, config, simulation_results, performance_metrics, mock_wallet
            )

            # Mark as completed
            self.active_backtests[backtest_id]['status'] = BacktestStatus.COMPLETED
            await self._update_progress(backtest_id, 100, "Backtest completed", progress_callback)

            logger.info(f"Backtest {backtest_id} completed: {performance_metrics.get('total_return_pct', 0):.2f}% return")
            return results

        except Exception as e:
            logger.error(f"Backtest {backtest_id} failed: {str(e)}")
            self.active_backtests[backtest_id]['status'] = BacktestStatus.FAILED
            self.active_backtests[backtest_id]['error'] = str(e)
            raise

    async def _fetch_historical_data(self, config: BacktestConfig) -> Dict[str, pd.DataFrame]:
        """Fetch historical data for all symbols"""
        logger.info(f"Fetching data for {len(config.symbols)} symbols from {config.start_date} to {config.end_date}")

        # Initialize data service with context manager
        async with HistoricalDataService() as data_service:
            historical_data = {}

            # Fetch data for each symbol
            for symbol in config.symbols:
                try:
                    data = await data_service.get_ohlcv_data(
                        symbol, config.start_date, config.end_date, config.timeframe
                    )

                    if not data.empty:
                        # Add technical indicators
                        indicator_config = self._get_indicator_config(config)
                        data = calculate_technical_indicators(data, indicator_config)
                        historical_data[symbol] = data
                        logger.info(f"Loaded {len(data)} rows for {symbol}")
                    else:
                        logger.warning(f"No data available for {symbol}")

                except Exception as e:
                    logger.error(f"Failed to fetch data for {symbol}: {e}")
                    raise

            # Align timeframes across symbols
            historical_data = TimeSeriesUtils.align_timeframes(historical_data)

            return historical_data

    async def _validate_historical_data(self, historical_data: Dict[str, pd.DataFrame], symbols: List[str]):
        """Validate the quality of historical data"""
        for symbol in symbols:
            if symbol not in historical_data:
                raise ValueError(f"No data available for symbol: {symbol}")

            data = historical_data[symbol]
            is_valid, errors = DataValidator.validate_ohlcv_data(data, symbol)

            if not is_valid:
                logger.warning(f"Data quality issues for {symbol}: {errors}")
                # Continue with warnings but don't fail the backtest

    async def _initialize_strategy(self, config: BacktestConfig):
        """Initialize the trading strategy"""
        strategy_name = config.strategy_name.lower()

        try:
            if strategy_name == 'ema_crossover' or strategy_name == 'moving_average_crossover':
                # Import the existing strategy
                from ..strategies.ma_crossover import MovingAverageCrossoverStrategy

                strategy = MovingAverageCrossoverStrategy()

                # Configure strategy parameters
                if hasattr(strategy, 'configure'):
                    strategy.configure(config.strategy_params)

                return strategy

            elif strategy_name == 'rsi_mean_reversion':
                # Placeholder for RSI strategy
                return self._create_rsi_strategy(config.strategy_params)

            elif strategy_name == 'momentum':
                # Placeholder for momentum strategy
                return self._create_momentum_strategy(config.strategy_params)

            else:
                raise ValueError(f"Unknown strategy: {config.strategy_name}")

        except ImportError as e:
            logger.error(f"Failed to import strategy {strategy_name}: {e}")
            # Fallback to a simple buy-and-hold strategy
            return self._create_simple_strategy(config.strategy_params)

    def _create_simple_strategy(self, params: Dict):
        """Create a simple buy-and-hold strategy for testing"""
        class SimpleBuyHoldStrategy:
            def __init__(self, params):
                self.params = params
                self.position_taken = False

            def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Dict]:
                if data.empty or len(data) < 2:
                    return []

                signals = []

                # Buy at the beginning if we haven't taken a position
                if not self.position_taken and len(data) > 10:
                    signals.append({
                        'symbol': symbol,
                        'side': 'BUY',
                        'size': self.params.get('position_size', 0.1),
                        'timestamp': data.iloc[-1]['timestamp'],
                        'price': data.iloc[-1]['close'],
                        'reason': 'Buy and hold strategy entry'
                    })
                    self.position_taken = True

                return signals

        return SimpleBuyHoldStrategy(params)

    def _create_rsi_strategy(self, params: Dict):
        """Create RSI mean reversion strategy"""
        class RSIMeanReversionStrategy:
            def __init__(self, params):
                self.params = params
                self.rsi_period = params.get('period', 14)
                self.oversold = params.get('oversoldLevel', 30)
                self.overbought = params.get('overboughtLevel', 70)
                self.position_size = params.get('positionSize', 0.05)

            def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Dict]:
                if data.empty or len(data) < self.rsi_period + 1:
                    return []

                signals = []
                latest = data.iloc[-1]
                previous = data.iloc[-2]

                if 'rsi' in data.columns:
                    current_rsi = latest['rsi']
                    prev_rsi = previous['rsi']

                    # Buy signal: RSI crosses above oversold
                    if prev_rsi <= self.oversold and current_rsi > self.oversold:
                        signals.append({
                            'symbol': symbol,
                            'side': 'BUY',
                            'size': self.position_size,
                            'timestamp': latest['timestamp'],
                            'price': latest['close'],
                            'reason': f'RSI oversold recovery: {current_rsi:.1f}'
                        })

                    # Sell signal: RSI crosses below overbought
                    elif prev_rsi >= self.overbought and current_rsi < self.overbought:
                        signals.append({
                            'symbol': symbol,
                            'side': 'SELL',
                            'size': self.position_size,
                            'timestamp': latest['timestamp'],
                            'price': latest['close'],
                            'reason': f'RSI overbought pullback: {current_rsi:.1f}'
                        })

                return signals

        return RSIMeanReversionStrategy(params)

    def _create_momentum_strategy(self, params: Dict):
        """Create momentum strategy"""
        class MomentumStrategy:
            def __init__(self, params):
                self.params = params
                self.lookback = params.get('lookback', 20)
                self.threshold = params.get('threshold', 0.02)
                self.position_size = params.get('positionSize', 0.05)

            def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Dict]:
                if data.empty or len(data) < self.lookback + 1:
                    return []

                signals = []
                latest = data.iloc[-1]

                # Calculate momentum (price change over lookback period)
                old_price = data.iloc[-(self.lookback + 1)]['close']
                current_price = latest['close']
                momentum = (current_price - old_price) / old_price

                if momentum > self.threshold:
                    signals.append({
                        'symbol': symbol,
                        'side': 'BUY',
                        'size': self.position_size,
                        'timestamp': latest['timestamp'],
                        'price': current_price,
                        'reason': f'Positive momentum: {momentum:.2%}'
                    })
                elif momentum < -self.threshold:
                    signals.append({
                        'symbol': symbol,
                        'side': 'SELL',
                        'size': self.position_size,
                        'timestamp': latest['timestamp'],
                        'price': current_price,
                        'reason': f'Negative momentum: {momentum:.2%}'
                    })

                return signals

        return MomentumStrategy(params)

    def _get_indicator_config(self, config: BacktestConfig) -> Dict:
        """Get technical indicator configuration based on strategy"""
        strategy_name = config.strategy_name.lower()

        base_config = {
            'sma_periods': [20, 50],
            'ema_periods': [12, 26],
            'rsi_period': 14,
            'macd_config': {'fast': 12, 'slow': 26, 'signal': 9},
            'bollinger_config': {'period': 20, 'std_dev': 2}
        }

        if strategy_name == 'ema_crossover':
            return {
                'ema_periods': [
                    config.strategy_params.get('fastPeriod', 12),
                    config.strategy_params.get('slowPeriod', 26)
                ]
            }
        elif strategy_name == 'rsi_mean_reversion':
            return {
                'rsi_period': config.strategy_params.get('period', 14)
            }
        else:
            return base_config

    async def _run_simulation(self, mock_wallet: MockWallet, historical_data: Dict[str, pd.DataFrame],
                             strategy, config: BacktestConfig, backtest_id: str, progress_callback) -> Dict:
        """Execute the main backtesting simulation"""

        # Determine simulation timeline
        all_timestamps = set()
        for data in historical_data.values():
            if not data.empty:
                all_timestamps.update(data['timestamp'].tolist())

        timeline = sorted(all_timestamps)
        if len(timeline) < config.warmup_period:
            raise ValueError(f"Insufficient data: {len(timeline)} periods, need at least {config.warmup_period}")

        logger.info(f"Simulation timeline: {len(timeline)} periods from {timeline[0]} to {timeline[-1]}")

        # Simulation state
        total_signals_generated = 0
        total_trades_executed = 0
        simulation_start = datetime.utcnow()

        # Main simulation loop
        for i, current_time in enumerate(timeline[config.warmup_period:], start=config.warmup_period):

            # Update progress
            if i % 100 == 0:
                progress = 40 + (50 * i / len(timeline))
                await self._update_progress(
                    backtest_id, progress,
                    f"Processing {current_time.date()} ({i}/{len(timeline)})",
                    progress_callback
                )

            # Get current market data for all symbols
            current_prices = {}
            symbol_data = {}

            for symbol, data in historical_data.items():
                # Find data up to current timestamp
                mask = data['timestamp'] <= current_time
                available_data = data[mask]

                if not available_data.empty:
                    latest_price = available_data.iloc[-1]['close']
                    current_prices[symbol] = latest_price
                    symbol_data[symbol] = available_data

            if not current_prices:
                continue

            # Record portfolio snapshot
            mock_wallet.record_portfolio_snapshot(current_prices, current_time)

            # Generate trading signals for each symbol
            for symbol in config.symbols:
                if symbol in symbol_data:
                    try:
                        signals = strategy.generate_signals(symbol_data[symbol], symbol)
                        total_signals_generated += len(signals)

                        # Execute signals
                        for signal in signals:
                            if self._should_execute_signal(signal, mock_wallet, config):
                                trade = mock_wallet.execute_trade(
                                    symbol=signal['symbol'],
                                    side=signal['side'],
                                    size=signal['size'],
                                    price=signal['price'],
                                    timestamp=current_time,
                                    slippage_rate=config.slippage_rate
                                )

                                if trade:
                                    total_trades_executed += 1
                                    logger.debug(f"Executed: {trade.side} {trade.size} {trade.symbol} @ ${trade.price:.2f}")

                    except Exception as e:
                        logger.warning(f"Strategy error at {current_time} for {symbol}: {e}")

        simulation_end = datetime.utcnow()
        simulation_duration = (simulation_end - simulation_start).total_seconds()

        logger.info(f"Simulation completed: {total_signals_generated} signals, {total_trades_executed} trades in {simulation_duration:.1f}s")

        return {
            'total_signals_generated': total_signals_generated,
            'total_trades_executed': total_trades_executed,
            'simulation_duration_seconds': simulation_duration,
            'periods_processed': len(timeline),
            'warmup_periods': config.warmup_period
        }

    def _should_execute_signal(self, signal: Dict, mock_wallet: MockWallet, config: BacktestConfig) -> bool:
        """Determine if a trading signal should be executed"""
        symbol = signal['symbol']
        side = signal['side']
        size = signal['size']

        # Check position size limits
        portfolio_value = mock_wallet.cash_balance + sum(
            abs(pos.size) * float(signal['price'])
            for pos in mock_wallet.positions.values()
            if pos.size != 0
        )

        position_value = size * signal['price']
        position_pct = position_value / portfolio_value

        if position_pct > config.max_position_size:
            logger.debug(f"Rejected signal: position size {position_pct:.2%} > limit {config.max_position_size:.2%}")
            return False

        # Check total exposure
        total_exposure = sum(
            abs(pos.size) * float(signal['price'])
            for pos in mock_wallet.positions.values()
            if pos.size != 0
        ) / portfolio_value

        if total_exposure > config.max_total_exposure:
            logger.debug(f"Rejected signal: total exposure {total_exposure:.2%} > limit {config.max_total_exposure:.2%}")
            return False

        return True

    async def _compile_results(self, backtest_id: str, config: BacktestConfig,
                              simulation_results: Dict, performance_metrics: Dict,
                              mock_wallet: MockWallet) -> Dict:
        """Compile comprehensive backtest results"""

        results = {
            'backtest_id': backtest_id,
            'strategy_name': config.strategy_name,
            'symbols': config.symbols,
            'start_date': config.start_date.isoformat(),
            'end_date': config.end_date.isoformat(),
            'timeframe': config.timeframe,

            # Performance metrics (from PerformanceCalculator)
            **performance_metrics,

            # Simulation metadata
            'simulation_metadata': simulation_results,

            # Configuration
            'config': {
                'initial_capital': config.initial_capital,
                'commission_rate': config.commission_rate,
                'slippage_rate': config.slippage_rate,
                'max_position_size': config.max_position_size,
                'max_total_exposure': config.max_total_exposure,
                'strategy_params': config.strategy_params
            },

            # Portfolio summary
            'portfolio_summary': mock_wallet.get_performance_summary(),

            # Execution timestamp
            'created_at': datetime.utcnow().isoformat(),
            'backtest_version': '1.0.0'
        }

        return results

    async def _update_progress(self, backtest_id: str, progress: float, message: str, callback=None):
        """Update backtest progress"""
        if backtest_id in self.active_backtests:
            self.active_backtests[backtest_id]['progress'] = progress
            self.active_backtests[backtest_id]['status_message'] = message

        if callback:
            await callback(backtest_id, progress, message)

    def get_backtest_status(self, backtest_id: str) -> Optional[Dict]:
        """Get status of running backtest"""
        return self.active_backtests.get(backtest_id)

    def cancel_backtest(self, backtest_id: str) -> bool:
        """Cancel a running backtest"""
        if backtest_id in self.active_backtests:
            self.active_backtests[backtest_id]['status'] = BacktestStatus.CANCELLED
            return True
        return False

    def list_active_backtests(self) -> List[Dict]:
        """List all active backtests"""
        return [
            {
                'backtest_id': bid,
                'strategy_name': info['config'].strategy_name,
                'status': info['status'],
                'progress': info['progress'],
                'start_time': info['start_time'].isoformat()
            }
            for bid, info in self.active_backtests.items()
        ]