"""
OrderBook Manager for dYdX v4
Maintains real-time order book state with efficient bid/ask tracking and analysis.
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PriceLevel:
    """Represents a single price level in the order book"""
    price: float
    size: float
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        self.price = float(self.price)
        self.size = float(self.size)


@dataclass
class OrderBookSnapshot:
    """Complete order book snapshot"""
    symbol: str
    bids: List[PriceLevel]
    asks: List[PriceLevel]
    timestamp: float
    sequence: Optional[int] = None
    
    def get_mid_price(self) -> Optional[float]:
        """Calculate mid price from best bid and ask"""
        if not self.bids or not self.asks:
            return None
        return (self.bids[0].price + self.asks[0].price) / 2.0
    
    def get_spread(self) -> Optional[float]:
        """Calculate bid-ask spread"""
        if not self.bids or not self.asks:
            return None
        return self.asks[0].price - self.bids[0].price
    
    def get_spread_bps(self) -> Optional[float]:
        """Calculate spread in basis points"""
        spread = self.get_spread()
        mid = self.get_mid_price()
        if spread is None or mid is None or mid == 0:
            return None
        return (spread / mid) * 10000


@dataclass
class LiquidityAnalysis:
    """Liquidity analysis for a given size"""
    symbol: str
    side: str  # BUY or SELL
    target_size: float
    available_size: float
    average_price: float
    price_impact: float  # in basis points
    levels_consumed: int
    worst_price: float


class OrderBook:
    """
    Single symbol order book with efficient price level management
    """
    
    def __init__(self, symbol: str, max_depth: int = 50):
        self.symbol = symbol
        self.max_depth = max_depth
        
        # Price levels stored as sorted lists
        self.bids: List[PriceLevel] = []  # Sorted descending by price
        self.asks: List[PriceLevel] = []  # Sorted ascending by price
        
        # Metadata
        self.last_update_time = 0.0
        self.sequence_number = 0
        self.update_count = 0
        
        # Performance tracking
        self.stats = {
            "updates_processed": 0,
            "snapshots_processed": 0,
            "last_mid_price": None,
            "price_change_24h": None,
            "average_spread_bps": 0.0
        }
    
    def update_snapshot(self, bids: List[List[float]], asks: List[List[float]]) -> bool:
        """
        Update order book with complete snapshot
        
        Args:
            bids: List of [price, size] pairs sorted by price descending
            asks: List of [price, size] pairs sorted by price ascending
            
        Returns:
            bool: True if update was successful
        """
        try:
            self.bids = [
                PriceLevel(price=price, size=size) 
                for price, size in bids[:self.max_depth]
                if size > 0
            ]
            
            self.asks = [
                PriceLevel(price=price, size=size) 
                for price, size in asks[:self.max_depth]
                if size > 0
            ]
            
            self.last_update_time = time.time()
            self.stats["snapshots_processed"] += 1
            
            return True
            
        except Exception as e:
            logger.error("Failed to update order book snapshot", 
                        symbol=self.symbol, error=str(e))
            return False
    
    def update_incremental(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Apply incremental updates to order book
        
        Args:
            updates: List of price level updates
            
        Returns:
            bool: True if all updates were applied successfully
        """
        try:
            for update in updates:
                side = update.get("side")  # "bid" or "ask"
                price = float(update.get("price", 0))
                size = float(update.get("size", 0))
                
                if side == "bid":
                    self._update_bid_level(price, size)
                elif side == "ask":
                    self._update_ask_level(price, size)
            
            self.last_update_time = time.time()
            self.update_count += 1
            self.stats["updates_processed"] += 1
            
            # Clean up empty levels and maintain depth limit
            self._cleanup_levels()
            
            return True
            
        except Exception as e:
            logger.error("Failed to apply incremental update", 
                        symbol=self.symbol, error=str(e))
            return False
    
    def _update_bid_level(self, price: float, size: float) -> None:
        """Update a single bid level"""
        # Find existing level or insertion point
        insert_index = 0
        found_index = -1
        
        for i, level in enumerate(self.bids):
            if level.price == price:
                found_index = i
                break
            elif level.price < price:
                insert_index = i
                break
            insert_index = i + 1
        
        if size == 0:
            # Remove level
            if found_index >= 0:
                self.bids.pop(found_index)
        else:
            # Update or insert level
            new_level = PriceLevel(price=price, size=size)
            if found_index >= 0:
                self.bids[found_index] = new_level
            else:
                self.bids.insert(insert_index, new_level)
    
    def _update_ask_level(self, price: float, size: float) -> None:
        """Update a single ask level"""
        # Find existing level or insertion point
        insert_index = len(self.asks)
        found_index = -1
        
        for i, level in enumerate(self.asks):
            if level.price == price:
                found_index = i
                break
            elif level.price > price:
                insert_index = i
                break
        
        if size == 0:
            # Remove level
            if found_index >= 0:
                self.asks.pop(found_index)
        else:
            # Update or insert level
            new_level = PriceLevel(price=price, size=size)
            if found_index >= 0:
                self.asks[found_index] = new_level
            else:
                self.asks.insert(insert_index, new_level)
    
    def _cleanup_levels(self) -> None:
        """Remove empty levels and enforce depth limits"""
        # Remove empty levels
        self.bids = [level for level in self.bids if level.size > 0]
        self.asks = [level for level in self.asks if level.size > 0]
        
        # Enforce depth limits
        if len(self.bids) > self.max_depth:
            self.bids = self.bids[:self.max_depth]
        if len(self.asks) > self.max_depth:
            self.asks = self.asks[:self.max_depth]
    
    def get_best_bid(self) -> Optional[PriceLevel]:
        """Get best bid (highest price)"""
        return self.bids[0] if self.bids else None
    
    def get_best_ask(self) -> Optional[PriceLevel]:
        """Get best ask (lowest price)"""
        return self.asks[0] if self.asks else None
    
    def get_mid_price(self) -> Optional[float]:
        """Calculate mid price from best bid and ask"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return (best_bid.price + best_ask.price) / 2.0
        return None
    
    def get_spread(self) -> Optional[float]:
        """Calculate absolute bid-ask spread"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return best_ask.price - best_bid.price
        return None
    
    def get_spread_bps(self) -> Optional[float]:
        """Calculate spread in basis points"""
        spread = self.get_spread()
        mid = self.get_mid_price()
        
        if spread is not None and mid is not None and mid > 0:
            return (spread / mid) * 10000
        return None
    
    def analyze_liquidity(self, size: float, side: str) -> LiquidityAnalysis:
        """
        Analyze available liquidity for a given order size
        
        Args:
            size: Order size to analyze
            side: "BUY" or "SELL"
            
        Returns:
            LiquidityAnalysis with impact metrics
        """
        if side.upper() == "BUY":
            levels = self.asks  # Buying consumes ask liquidity
        else:
            levels = self.bids  # Selling consumes bid liquidity
        
        remaining_size = size
        total_cost = 0.0
        levels_consumed = 0
        worst_price = None
        
        for level in levels:
            if remaining_size <= 0:
                break
                
            consumed_size = min(remaining_size, level.size)
            total_cost += consumed_size * level.price
            remaining_size -= consumed_size
            levels_consumed += 1
            worst_price = level.price
            
            if remaining_size <= 0:
                break
        
        available_size = size - remaining_size
        average_price = total_cost / available_size if available_size > 0 else 0.0
        
        # Calculate price impact
        mid_price = self.get_mid_price()
        price_impact = 0.0
        if mid_price and average_price and mid_price > 0:
            if side.upper() == "BUY":
                price_impact = ((average_price - mid_price) / mid_price) * 10000
            else:
                price_impact = ((mid_price - average_price) / mid_price) * 10000
        
        return LiquidityAnalysis(
            symbol=self.symbol,
            side=side.upper(),
            target_size=size,
            available_size=available_size,
            average_price=average_price,
            price_impact=price_impact,
            levels_consumed=levels_consumed,
            worst_price=worst_price or 0.0
        )
    
    def get_snapshot(self) -> OrderBookSnapshot:
        """Get current order book snapshot"""
        return OrderBookSnapshot(
            symbol=self.symbol,
            bids=self.bids.copy(),
            asks=self.asks.copy(),
            timestamp=self.last_update_time,
            sequence=self.sequence_number
        )
    
    def get_depth_chart_data(self, levels: int = 20) -> Dict[str, List[Tuple[float, float]]]:
        """
        Generate data for depth chart visualization
        
        Args:
            levels: Number of levels to include
            
        Returns:
            Dict with 'bids' and 'asks' cumulative depth data
        """
        bid_depth = []
        ask_depth = []
        
        # Calculate cumulative bid depth
        cumulative_bid_size = 0.0
        for level in self.bids[:levels]:
            cumulative_bid_size += level.size
            bid_depth.append((level.price, cumulative_bid_size))
        
        # Calculate cumulative ask depth  
        cumulative_ask_size = 0.0
        for level in self.asks[:levels]:
            cumulative_ask_size += level.size
            ask_depth.append((level.price, cumulative_ask_size))
        
        return {
            "bids": bid_depth,
            "asks": ask_depth
        }
    
    def is_healthy(self) -> bool:
        """Check if order book is in healthy state"""
        # Check basic health conditions
        if not self.bids or not self.asks:
            return False
        
        # Check spread reasonableness (not too wide)
        spread_bps = self.get_spread_bps()
        if spread_bps is None or spread_bps > 1000:  # > 10% spread
            return False
        
        # Check recent updates
        if time.time() - self.last_update_time > 60:  # No updates for 1 minute
            return False
        
        return True


class OrderBookManager:
    """
    Multi-symbol order book manager with real-time updates and analysis
    """
    
    def __init__(self, symbols: List[str], max_depth: int = 50):
        self.symbols = symbols
        self.max_depth = max_depth
        
        # Order books for each symbol
        self.order_books: Dict[str, OrderBook] = {
            symbol: OrderBook(symbol, max_depth) for symbol in symbols
        }
        
        # Aggregated statistics
        self.stats = {
            "total_updates": 0,
            "total_snapshots": 0,
            "symbols_healthy": 0,
            "average_spread_bps": 0.0,
            "last_update_time": None
        }
        
        # Event callbacks
        self.update_callbacks: List[callable] = []
        
        logger.info("OrderBook manager initialized", 
                   symbols=symbols, max_depth=max_depth)
    
    def add_update_callback(self, callback: callable) -> None:
        """Add callback to be called on order book updates"""
        self.update_callbacks.append(callback)
    
    async def handle_orderbook_message(self, message: Dict[str, Any]) -> None:
        """
        Handle incoming order book WebSocket message
        
        Args:
            message: WebSocket message containing order book data
        """
        try:
            # Extract symbol from message
            symbol = message.get("id", "")
            if symbol not in self.order_books:
                logger.warning("Received order book data for unknown symbol", symbol=symbol)
                return
            
            # Get message contents
            contents = message.get("contents", {})
            if not contents:
                logger.warning("Empty order book message", symbol=symbol)
                return
            
            order_book = self.order_books[symbol]
            
            # Handle different message types
            if contents.get("type") == "snapshot":
                # Full snapshot update
                bids = contents.get("bids", [])
                asks = contents.get("asks", [])
                
                if order_book.update_snapshot(bids, asks):
                    logger.debug("Order book snapshot updated", symbol=symbol)
                    await self._notify_callbacks(symbol, order_book)
                    
            elif contents.get("type") == "update":
                # Incremental update
                updates = contents.get("changes", [])
                
                if order_book.update_incremental(updates):
                    logger.debug("Order book incrementally updated", 
                               symbol=symbol, updates=len(updates))
                    await self._notify_callbacks(symbol, order_book)
            
            # Update global stats
            self._update_global_stats()
            
        except Exception as e:
            logger.error("Error handling order book message", error=str(e))
    
    async def _notify_callbacks(self, symbol: str, order_book: OrderBook) -> None:
        """Notify registered callbacks of order book update"""
        if self.update_callbacks:
            snapshot = order_book.get_snapshot()
            tasks = [callback(symbol, snapshot) for callback in self.update_callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _update_global_stats(self) -> None:
        """Update global statistics across all order books"""
        healthy_count = 0
        total_spread_bps = 0.0
        spread_count = 0
        
        for order_book in self.order_books.values():
            if order_book.is_healthy():
                healthy_count += 1
            
            spread_bps = order_book.get_spread_bps()
            if spread_bps is not None:
                total_spread_bps += spread_bps
                spread_count += 1
        
        self.stats.update({
            "symbols_healthy": healthy_count,
            "average_spread_bps": total_spread_bps / spread_count if spread_count > 0 else 0.0,
            "last_update_time": datetime.utcnow()
        })
    
    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get order book for specific symbol"""
        return self.order_books.get(symbol)
    
    def get_best_prices(self, symbol: str) -> Optional[Tuple[float, float]]:
        """
        Get best bid and ask prices for symbol
        
        Returns:
            Tuple of (best_bid, best_ask) or None
        """
        order_book = self.order_books.get(symbol)
        if not order_book:
            return None
        
        best_bid = order_book.get_best_bid()
        best_ask = order_book.get_best_ask()
        
        if best_bid and best_ask:
            return (best_bid.price, best_ask.price)
        return None
    
    def get_mid_price(self, symbol: str) -> Optional[float]:
        """Get mid price for symbol"""
        order_book = self.order_books.get(symbol)
        return order_book.get_mid_price() if order_book else None
    
    def get_spread_bps(self, symbol: str) -> Optional[float]:
        """Get spread in basis points for symbol"""
        order_book = self.order_books.get(symbol)
        return order_book.get_spread_bps() if order_book else None
    
    def analyze_liquidity(self, symbol: str, size: float, side: str) -> Optional[LiquidityAnalysis]:
        """Analyze liquidity for given size and side"""
        order_book = self.order_books.get(symbol)
        return order_book.analyze_liquidity(size, side) if order_book else None
    
    def get_all_snapshots(self) -> Dict[str, OrderBookSnapshot]:
        """Get snapshots for all symbols"""
        return {
            symbol: order_book.get_snapshot() 
            for symbol, order_book in self.order_books.items()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for all order books"""
        symbol_health = {}
        for symbol, order_book in self.order_books.items():
            symbol_health[symbol] = {
                "is_healthy": order_book.is_healthy(),
                "mid_price": order_book.get_mid_price(),
                "spread_bps": order_book.get_spread_bps(),
                "last_update": order_book.last_update_time,
                "bid_levels": len(order_book.bids),
                "ask_levels": len(order_book.asks)
            }
        
        return {
            "global_stats": self.stats,
            "symbols": symbol_health
        }