"""
Historical Data Service for Backtesting

Fetches and caches OHLCV data from multiple sources with intelligent fallbacks,
rate limiting, and optimized storage for backtesting scenarios.
"""

import asyncio
import aiohttp
import pandas as pd
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import time
import json

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(self, calls_per_minute: int = 50):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call = 0

    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        time_since_last = now - self.last_call
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        self.last_call = time.time()


class DataCache:
    """Intelligent caching system for historical data"""

    def __init__(self, cache_dir: str = "data_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"DataCache initialized at {self.cache_dir}")

    def _get_cache_key(self, symbol: str, start: datetime, end: datetime, timeframe: str) -> str:
        """Generate cache key for data request"""
        key_string = f"{symbol}_{start.isoformat()}_{end.isoformat()}_{timeframe}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{cache_key}.pkl"

    def get(self, symbol: str, start: datetime, end: datetime, timeframe: str) -> Optional[pd.DataFrame]:
        """Retrieve cached data if available and fresh"""
        cache_key = self._get_cache_key(symbol, start, end, timeframe)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            # Check cache age (refresh if older than 1 hour for recent data)
            cache_age = time.time() - cache_path.stat().st_mtime
            max_age = 3600 if end > datetime.now() - timedelta(days=7) else 86400  # 1h vs 24h

            if cache_age > max_age:
                logger.debug(f"Cache expired for {symbol} ({cache_age:.0f}s old)")
                return None

            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
                logger.debug(f"Cache hit for {symbol}: {len(data)} rows")
                return data

        except Exception as e:
            logger.warning(f"Cache read error for {symbol}: {e}")
            return None

    def set(self, symbol: str, start: datetime, end: datetime, timeframe: str, data: pd.DataFrame):
        """Cache data with metadata"""
        cache_key = self._get_cache_key(symbol, start, end, timeframe)
        cache_path = self._get_cache_path(cache_key)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            logger.debug(f"Cached {len(data)} rows for {symbol}")
        except Exception as e:
            logger.warning(f"Cache write error for {symbol}: {e}")

    def clear(self):
        """Clear all cached data"""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
        logger.info("Cache cleared")


class HistoricalDataService:
    """
    Production-grade historical data service with multiple sources and intelligent caching

    Features:
    - CoinGecko API integration (free tier: 10-50 calls/min)
    - Intelligent caching with freshness checks
    - Rate limiting and retry logic
    - Data quality validation
    - Multiple timeframe support
    - Fallback to synthetic data for testing
    """

    def __init__(self, cache_dir: str = "data_cache"):
        self.cache = DataCache(cache_dir)
        self.rate_limiter = RateLimiter(calls_per_minute=45)  # Conservative rate
        self.session: Optional[aiohttp.ClientSession] = None

        # Symbol mapping for CoinGecko API
        self.symbol_mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'LINK': 'chainlink',
            'WBTC': 'wrapped-bitcoin'
        }

        # Timeframe mapping
        self.timeframe_mapping = {
            '1h': 'hourly',
            '4h': 'hourly',
            '1d': 'daily',
            '1w': 'daily'
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'WolfHunt-Trading-Bot/1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_ohlcv_data(self, symbol: str, start_date: datetime, end_date: datetime,
                            timeframe: str = '1h') -> pd.DataFrame:
        """
        Get OHLCV data for backtesting with intelligent caching

        Args:
            symbol: Trading symbol (BTC, ETH, LINK, etc.)
            start_date: Start date for data
            end_date: End date for data
            timeframe: Data timeframe (1h, 4h, 1d, 1w)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        logger.info(f"Fetching {symbol} data from {start_date.date()} to {end_date.date()} ({timeframe})")

        # Check cache first
        cached_data = self.cache.get(symbol, start_date, end_date, timeframe)
        if cached_data is not None and not cached_data.empty:
            logger.info(f"Using cached data for {symbol} ({len(cached_data)} rows)")
            return cached_data

        try:
            # Fetch fresh data from CoinGecko
            data = await self._fetch_coingecko_data(symbol, start_date, end_date, timeframe)

            if data is not None and not data.empty:
                # Validate and clean data
                data = self._validate_and_clean_data(data, symbol)

                # Cache the data
                self.cache.set(symbol, start_date, end_date, timeframe, data)

                logger.info(f"Fetched {len(data)} rows for {symbol} from CoinGecko")
                return data

        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")

        # Fallback to synthetic data for testing
        logger.warning(f"Generating synthetic data for {symbol}")
        return self._generate_synthetic_data(symbol, start_date, end_date, timeframe)

    async def _fetch_coingecko_data(self, symbol: str, start_date: datetime,
                                   end_date: datetime, timeframe: str) -> Optional[pd.DataFrame]:
        """Fetch data from CoinGecko API"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        coingecko_id = self.symbol_mapping.get(symbol)
        if not coingecko_id:
            raise ValueError(f"Symbol {symbol} not supported")

        await self.rate_limiter.wait_if_needed()

        # Calculate days for CoinGecko API
        days = (end_date - start_date).days
        if days > 365:
            days = 365  # CoinGecko free tier limit

        # Build API URL
        url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'hourly' if timeframe in ['1h', '4h'] else 'daily'
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_coingecko_response(data, timeframe)
                elif response.status == 429:
                    logger.warning("Rate limited by CoinGecko, waiting...")
                    await asyncio.sleep(60)
                    return None
                else:
                    logger.error(f"CoinGecko API error: {response.status}")
                    return None

        except asyncio.TimeoutError:
            logger.error("Timeout fetching data from CoinGecko")
            return None
        except Exception as e:
            logger.error(f"Error fetching from CoinGecko: {e}")
            return None

    def _parse_coingecko_response(self, data: dict, timeframe: str) -> pd.DataFrame:
        """Parse CoinGecko API response into OHLCV format"""
        prices = data.get('prices', [])
        volumes = data.get('total_volumes', [])

        if not prices:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(prices, columns=['timestamp', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Add volume data
        if volumes:
            volume_df = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
            volume_df['timestamp'] = pd.to_datetime(volume_df['timestamp'], unit='ms')
            df = df.merge(volume_df, on='timestamp', how='left')
        else:
            df['volume'] = 0

        # Generate OHLC from price data (approximation for hourly data)
        df = df.set_index('timestamp')

        if timeframe == '1h':
            # Keep hourly resolution
            df['open'] = df['close'].shift(1).fillna(df['close'])
            df['high'] = df['close'] * 1.002  # Approximate high
            df['low'] = df['close'] * 0.998   # Approximate low
        elif timeframe == '4h':
            # Resample to 4H
            df = df.resample('4H').agg({
                'close': 'last',
                'volume': 'sum'
            })
            df['open'] = df['close'].shift(1).fillna(df['close'])
            df['high'] = df['close'] * 1.008
            df['low'] = df['close'] * 0.992
        elif timeframe == '1d':
            # Resample to daily
            df = df.resample('1D').agg({
                'close': 'last',
                'volume': 'sum'
            })
            df['open'] = df['close'].shift(1).fillna(df['close'])
            df['high'] = df['close'] * 1.02
            df['low'] = df['close'] * 0.98

        # Reset index and reorder columns
        df = df.reset_index()
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].dropna()

        return df

    def _validate_and_clean_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Validate and clean OHLCV data"""
        if data.empty:
            return data

        # Remove invalid rows
        data = data.dropna()
        data = data[data['close'] > 0]
        data = data[data['volume'] >= 0]

        # Ensure proper column order
        expected_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        data = data[expected_columns]

        # Sort by timestamp
        data = data.sort_values('timestamp').reset_index(drop=True)

        # Validate OHLC relationships
        invalid_ohlc = (
            (data['high'] < data['low']) |
            (data['high'] < data['open']) |
            (data['high'] < data['close']) |
            (data['low'] > data['open']) |
            (data['low'] > data['close'])
        )

        if invalid_ohlc.any():
            logger.warning(f"Found {invalid_ohlc.sum()} invalid OHLC rows for {symbol}")
            # Fix invalid OHLC by setting high/low based on open/close
            for idx in data[invalid_ohlc].index:
                row = data.loc[idx]
                data.loc[idx, 'high'] = max(row['open'], row['close']) * 1.001
                data.loc[idx, 'low'] = min(row['open'], row['close']) * 0.999

        logger.info(f"Validated {len(data)} rows for {symbol}")
        return data

    def _generate_synthetic_data(self, symbol: str, start_date: datetime,
                                end_date: datetime, timeframe: str) -> pd.DataFrame:
        """Generate synthetic OHLCV data for testing"""
        logger.info(f"Generating synthetic data for {symbol}")

        # Time interval mapping
        interval_map = {
            '1h': timedelta(hours=1),
            '4h': timedelta(hours=4),
            '1d': timedelta(days=1),
            '1w': timedelta(weeks=1)
        }

        interval = interval_map.get(timeframe, timedelta(hours=1))

        # Generate timestamps
        timestamps = []
        current = start_date
        while current <= end_date:
            timestamps.append(current)
            current += interval

        # Base prices for different symbols
        base_prices = {
            'BTC': 45000,
            'ETH': 3000,
            'LINK': 15,
            'WBTC': 45000
        }

        base_price = base_prices.get(symbol, 100)

        # Generate realistic price movement
        import random
        random.seed(42)  # Reproducible synthetic data

        data = []
        current_price = base_price

        for timestamp in timestamps:
            # Generate random price movement (-2% to +2%)
            change = random.uniform(-0.02, 0.02)
            new_price = current_price * (1 + change)

            # Generate OHLC
            open_price = current_price
            close_price = new_price

            # High and low around open/close
            high_price = max(open_price, close_price) * random.uniform(1.001, 1.02)
            low_price = min(open_price, close_price) * random.uniform(0.98, 0.999)

            # Volume (higher volume on larger price moves)
            volume = random.uniform(1000, 10000) * (1 + abs(change) * 10)

            data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 2)
            })

            current_price = new_price

        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} synthetic rows for {symbol}")
        return df

    async def preload_data(self, symbols: List[str], start_date: datetime,
                          end_date: datetime, timeframe: str = '1h'):
        """Preload data for multiple symbols to optimize backtesting"""
        logger.info(f"Preloading data for {len(symbols)} symbols")

        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(
                self.get_ohlcv_data(symbol, start_date, end_date, timeframe)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in results if isinstance(r, pd.DataFrame) and not r.empty)
        logger.info(f"Preloaded data for {successful}/{len(symbols)} symbols")

        return results

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        cache_files = list(self.cache.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            'cache_files': len(cache_files),
            'cache_size_mb': round(total_size / 1024 / 1024, 2),
            'cache_directory': str(self.cache.cache_dir)
        }