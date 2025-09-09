"""
🔥 REAL MARKET DATA SERVICE
Live price feeds and market data for Wolf Pack Intelligence
"""

import asyncio
import httpx
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealMarketDataService:
    """Service for fetching real market data from multiple sources"""
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.binance_base = "https://api.binance.com/api/v3"
        self.cache = {}
        self.cache_ttl = 30  # Cache for 30 seconds
        
        # Mapping of our symbols to CoinGecko IDs
        self.symbol_mapping = {
            'ETH': 'ethereum',
            'WBTC': 'wrapped-bitcoin', 
            'LINK': 'chainlink'
        }
        
        # Mapping of our symbols to Binance symbols
        self.binance_mapping = {
            'ETH': 'ETHUSDT',
            'WBTC': 'BTCUSDT',  # Use BTC for WBTC
            'LINK': 'LINKUSDT'
        }
    
    async def get_live_prices(self) -> Dict[str, float]:
        """Get current prices for all tracked cryptocurrencies"""
        cache_key = "live_prices"
        
        # Check cache first
        if self._is_cached(cache_key):
            logger.info(f"Using cached prices (age: {time.time() - self.cache[cache_key]['timestamp']:.1f}s)")
            return self.cache[cache_key]['data']
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get prices from CoinGecko
                coingecko_ids = ','.join(self.symbol_mapping.values())
                url = f"{self.coingecko_base}/simple/price"
                params = {
                    'ids': coingecko_ids,
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_24hr_vol': 'true'
                }
                
                logger.info(f"Fetching live prices from CoinGecko: {url}")
                response = await client.get(url, params=params)
                
                # Log response details for debugging
                logger.info(f"CoinGecko API Response: Status={response.status_code}, Headers={dict(response.headers)}")
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Raw CoinGecko data: {data}")
                
                # Convert to our format
                prices = {}
                for symbol, coingecko_id in self.symbol_mapping.items():
                    if coingecko_id in data:
                        prices[symbol] = {
                            'price': data[coingecko_id]['usd'],
                            '24h_change': data[coingecko_id].get('usd_24h_change', 0),
                            '24h_volume': data[coingecko_id].get('usd_24h_vol', 0),
                            'last_updated': datetime.utcnow().isoformat(),
                            'source': 'coingecko_api'
                        }
                    else:
                        logger.warning(f"No data found for {symbol} ({coingecko_id})")
                
                if not prices:
                    logger.error("No price data extracted from CoinGecko response")
                    return self._get_fallback_prices()
                
                # Cache the result with additional metadata
                self.cache[cache_key] = {
                    'data': prices,
                    'timestamp': time.time(),
                    'source': 'coingecko_api',
                    'response_status': response.status_code
                }
                
                logger.info(f"Successfully fetched {len(prices)} live prices: {prices}")
                return prices
                
        except httpx.TimeoutException:
            logger.error("CoinGecko API timeout")
            return self._get_fallback_prices_with_error("API_TIMEOUT")
        except httpx.HTTPStatusError as e:
            logger.error(f"CoinGecko API HTTP error: {e.response.status_code} - {e.response.text}")
            return self._get_fallback_prices_with_error(f"HTTP_{e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error fetching live prices: {e}")
            return self._get_fallback_prices_with_error(f"ERROR_{type(e).__name__}")
    
    async def get_historical_data(self, symbol: str, days: int = 7) -> List[Dict]:
        """Get historical price data for technical analysis"""
        cache_key = f"historical_{symbol}_{days}"
        
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                coingecko_id = self.symbol_mapping.get(symbol)
                if not coingecko_id:
                    return []
                
                url = f"{self.coingecko_base}/coins/{coingecko_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'hourly'
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Format the data for technical analysis
                formatted_data = []
                prices = data.get('prices', [])
                volumes = data.get('total_volumes', [])
                
                for i, (timestamp, price) in enumerate(prices):
                    volume = volumes[i][1] if i < len(volumes) else 0
                    formatted_data.append({
                        'timestamp': timestamp,
                        'price': price,
                        'volume': volume,
                        'datetime': datetime.fromtimestamp(timestamp / 1000)
                    })
                
                # Cache the result
                self.cache[cache_key] = {
                    'data': formatted_data,
                    'timestamp': time.time()
                }
                
                return formatted_data
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    async def calculate_technical_indicators(self, symbol: str) -> Dict:
        """Calculate technical indicators from real historical data"""
        try:
            historical_data = await self.get_historical_data(symbol, days=30)
            
            if len(historical_data) < 20:
                logger.warning(f"Insufficient historical data for {symbol}")
                return self._get_fallback_indicators(symbol)
            
            # Extract prices for calculations
            prices = [item['price'] for item in historical_data]
            volumes = [item['volume'] for item in historical_data]
            
            # Calculate RSI (simple implementation)
            rsi = self._calculate_rsi(prices)
            
            # Calculate moving averages
            sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else prices[-1]
            sma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else sma_20
            
            # Calculate volume ratio
            recent_volume = sum(volumes[-24:]) / 24 if len(volumes) >= 24 else volumes[-1]
            avg_volume = sum(volumes) / len(volumes)
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Determine trend
            current_price = prices[-1]
            price_change_24h = (current_price - prices[-24]) / prices[-24] * 100 if len(prices) >= 24 else 0
            
            # Pattern detection based on price action
            pattern = self._detect_pattern(prices, volumes)
            
            # Calculate technical score
            technical_score = self._calculate_technical_score(rsi, current_price, sma_20, sma_50, volume_ratio)
            
            return {
                'price': current_price,
                'rsi': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'volume_ratio': volume_ratio,
                'price_change_24h': price_change_24h,
                'technical_score': technical_score,
                'pattern_detected': pattern,
                'signal_strength': self._get_signal_strength(technical_score),
                'confidence_level': min(0.95, max(0.3, technical_score / 100)),
                'data_quality': 'LIVE_DATA'
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return self._get_fallback_indicators(symbol)
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI using simple method"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas[-period:]]
        losses = [-delta if delta < 0 else 0 for delta in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _detect_pattern(self, prices: List[float], volumes: List[float]) -> str:
        """Simple pattern detection based on recent price action"""
        if len(prices) < 10:
            return "Insufficient Data"
        
        recent_prices = prices[-10:]
        recent_volumes = volumes[-10:]
        
        # Check for support/resistance
        current_price = recent_prices[-1]
        high_point = max(recent_prices)
        low_point = min(recent_prices)
        
        # Volume analysis
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        current_volume = recent_volumes[-1]
        
        if current_volume > avg_volume * 1.5:
            if current_price > sum(recent_prices) / len(recent_prices):
                return "Breakout"
            else:
                return "Breakdown"
        
        if abs(current_price - low_point) / low_point < 0.02:
            return "Support Bounce"
        elif abs(high_point - current_price) / current_price < 0.02:
            return "Resistance Test"
        elif current_price > sum(recent_prices[:-1]) / (len(recent_prices) - 1):
            return "Bull Flag"
        else:
            return "Consolidation"
    
    def _calculate_technical_score(self, rsi: float, price: float, sma_20: float, sma_50: float, volume_ratio: float) -> float:
        """Calculate technical score from indicators"""
        score = 50  # Base score
        
        # RSI contribution (0-30 points)
        if 30 <= rsi <= 70:
            score += 10  # Neutral RSI
        elif rsi > 70:
            score += 5   # Overbought but bullish
        elif rsi < 30:
            score += 15  # Oversold, potential bounce
        
        # Moving average contribution (0-25 points)
        if price > sma_20 > sma_50:
            score += 25  # Strong uptrend
        elif price > sma_20:
            score += 15  # Above short MA
        elif price > sma_50:
            score += 10  # Above long MA
        
        # Volume contribution (0-15 points)
        if volume_ratio > 1.5:
            score += 15  # High volume
        elif volume_ratio > 1.0:
            score += 10  # Above average volume
        
        return min(100, max(0, score))
    
    def _get_signal_strength(self, technical_score: float) -> str:
        """Convert technical score to signal strength"""
        if technical_score >= 80:
            return "VERY_STRONG"
        elif technical_score >= 65:
            return "STRONG"
        elif technical_score >= 45:
            return "MODERATE"
        elif technical_score >= 30:
            return "WEAK"
        else:
            return "VERY_WEAK"
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid"""
        if key not in self.cache:
            return False
        return time.time() - self.cache[key]['timestamp'] < self.cache_ttl
    
    def _get_fallback_prices(self) -> Dict[str, Dict]:
        """Fallback prices when API fails"""
        fallback_timestamp = datetime.utcnow().isoformat()
        return {
            'ETH': {
                'price': 2850.0, 
                '24h_change': 2.5, 
                '24h_volume': 15000000000,
                'last_updated': fallback_timestamp,
                'source': 'fallback_data'
            },
            'WBTC': {
                'price': 45800.0, 
                '24h_change': 1.8, 
                '24h_volume': 500000000,
                'last_updated': fallback_timestamp,
                'source': 'fallback_data'
            },
            'LINK': {
                'price': 15.75, 
                '24h_change': 3.2, 
                '24h_volume': 800000000,
                'last_updated': fallback_timestamp,
                'source': 'fallback_data'
            }
        }
    
    def _get_fallback_prices_with_error(self, error_code: str) -> Dict[str, Dict]:
        """Fallback prices with error information"""
        fallback_timestamp = datetime.utcnow().isoformat()
        return {
            'ETH': {
                'price': 2850.0, 
                '24h_change': 2.5, 
                '24h_volume': 15000000000,
                'last_updated': fallback_timestamp,
                'source': 'fallback_data',
                'error': error_code
            },
            'WBTC': {
                'price': 45800.0, 
                '24h_change': 1.8, 
                '24h_volume': 500000000,
                'last_updated': fallback_timestamp,
                'source': 'fallback_data',
                'error': error_code
            },
            'LINK': {
                'price': 15.75, 
                '24h_change': 3.2, 
                '24h_volume': 800000000,
                'last_updated': fallback_timestamp,
                'source': 'fallback_data',
                'error': error_code
            }
        }
    
    def _get_fallback_indicators(self, symbol: str) -> Dict:
        """Fallback indicators when calculation fails"""
        base_prices = {'ETH': 2850.0, 'WBTC': 45800.0, 'LINK': 15.75}
        return {
            'price': base_prices.get(symbol, 1000.0),
            'rsi': 55.0,
            'sma_20': base_prices.get(symbol, 1000.0) * 0.98,
            'sma_50': base_prices.get(symbol, 1000.0) * 0.95,
            'volume_ratio': 1.2,
            'price_change_24h': 2.0,
            'technical_score': 65.0,
            'pattern_detected': 'Consolidation',
            'signal_strength': 'MODERATE',
            'confidence_level': 0.7,
            'data_quality': 'FALLBACK_DATA'
        }

# Global instance
market_data_service = RealMarketDataService()