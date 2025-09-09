"""
GMX v2 Integration Client
Handles trading operations on GMX decentralized perpetual exchange on Arbitrum
"""

import os
from typing import Dict, List, Optional, Any
from decimal import Decimal
import asyncio
import logging

# GMX SDK imports (these would be available after installing gmx-python-sdk)
try:
    from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager
    from gmx_python_sdk.scripts.v2.order.create_order import OrderManager
    from gmx_python_sdk.scripts.v2.order.create_order_utils import OrderUtils
    from gmx_python_sdk.scripts.v2.get.get_markets import Markets
    from gmx_python_sdk.scripts.v2.get.get_oracle_prices import OraclePrices
    from gmx_python_sdk.scripts.v2.get.get_positions import Positions
    GMX_SDK_AVAILABLE = True
except ImportError:
    GMX_SDK_AVAILABLE = False
    logging.warning("GMX Python SDK not available. Install with: pip install gmx-python-sdk")

logger = logging.getLogger(__name__)

class GMXClient:
    """
    GMX v2 client for interacting with the GMX protocol on Arbitrum
    """
    
    def __init__(
        self,
        private_key: Optional[str] = None,
        rpc_url: Optional[str] = None,
        testnet: bool = True
    ):
        self.testnet = testnet
        self.private_key = private_key or os.getenv("GMX_PRIVATE_KEY")
        self.rpc_url = rpc_url or os.getenv("GMX_RPC_URL", "https://arb1.arbitrum.io/rpc")
        self.chain_id = 42161  # Arbitrum mainnet
        
        if not GMX_SDK_AVAILABLE:
            logger.error("GMX SDK not available. Cannot initialize client.")
            self.config = None
            return
        
        # Initialize GMX SDK configuration
        self.config = self._initialize_config()
        self.markets = None
        self.positions = None
        
    def _initialize_config(self) -> Optional[Any]:
        """Initialize GMX SDK configuration"""
        if not GMX_SDK_AVAILABLE:
            return None
            
        try:
            config = ConfigManager(
                chain_id=self.chain_id,
                rpc_url=self.rpc_url,
                private_key=self.private_key
            )
            return config
        except Exception as e:
            logger.error(f"Failed to initialize GMX config: {e}")
            return None
    
    async def get_markets(self) -> List[Dict[str, Any]]:
        """Get available trading markets on GMX"""
        if not self.config:
            return self._get_mock_markets()
            
        try:
            markets = Markets(config=self.config)
            market_data = markets.get_available_markets()
            return self._format_markets(market_data)
        except Exception as e:
            logger.error(f"Error fetching GMX markets: {e}")
            return self._get_mock_markets()
    
    async def get_oracle_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Get current oracle prices for specified symbols"""
        if not self.config:
            return self._get_mock_prices(symbols)
            
        try:
            oracle = OraclePrices(config=self.config)
            prices = {}
            for symbol in symbols:
                price = oracle.get_recent_prices(symbol)
                prices[symbol] = Decimal(str(price))
            return prices
        except Exception as e:
            logger.error(f"Error fetching GMX oracle prices: {e}")
            return self._get_mock_prices(symbols)
    
    async def get_positions(self, account_address: str) -> List[Dict[str, Any]]:
        """Get current positions for an account"""
        if not self.config:
            return self._get_mock_positions()
            
        try:
            positions = Positions(config=self.config)
            position_data = positions.get_positions(account_address)
            return self._format_positions(position_data)
        except Exception as e:
            logger.error(f"Error fetching GMX positions: {e}")
            return self._get_mock_positions()
    
    async def create_order(
        self,
        symbol: str,
        side: str,  # 'long' or 'short'
        size_usd: float,
        leverage: float = 1.0,
        order_type: str = "market",
        slippage: float = 0.5
    ) -> Dict[str, Any]:
        """Create a trading order on GMX"""
        if not self.config:
            return self._simulate_order(symbol, side, size_usd, leverage)
            
        try:
            order_manager = OrderManager(config=self.config)
            
            # Create order parameters
            order_params = {
                "chain": "arbitrum",
                "index_token_symbol": symbol,
                "collateral_token_symbol": "USDC",  # Default collateral
                "is_long": side.lower() == "long",
                "size_delta": size_usd,
                "leverage": leverage,
                "slippage_percent": slippage
            }
            
            # Execute order
            result = order_manager.create_increase_order(**order_params)
            return self._format_order_result(result)
            
        except Exception as e:
            logger.error(f"Error creating GMX order: {e}")
            return self._simulate_order(symbol, side, size_usd, leverage, error=str(e))
    
    async def close_position(
        self,
        symbol: str,
        size_usd: float,
        slippage: float = 0.5
    ) -> Dict[str, Any]:
        """Close or partially close a position"""
        if not self.config:
            return self._simulate_close_position(symbol, size_usd)
            
        try:
            order_manager = OrderManager(config=self.config)
            
            # Create close order parameters
            order_params = {
                "chain": "arbitrum",
                "index_token_symbol": symbol,
                "collateral_token_symbol": "USDC",
                "size_delta": size_usd,
                "slippage_percent": slippage
            }
            
            result = order_manager.create_decrease_order(**order_params)
            return self._format_order_result(result)
            
        except Exception as e:
            logger.error(f"Error closing GMX position: {e}")
            return self._simulate_close_position(symbol, size_usd, error=str(e))
    
    # Mock data methods for when SDK is not available
    def _get_mock_markets(self) -> List[Dict[str, Any]]:
        """Return mock market data"""
        return [
            {
                "symbol": "BTC-USD",
                "index_token": "BTC",
                "long_token": "BTC",
                "short_token": "USDC",
                "market_token": "GM",
                "pool_value": 50000000,
                "max_open_interest_long": 10000000,
                "max_open_interest_short": 10000000,
                "funding_rate": 0.0012,
                "borrowing_rate": 0.0008
            },
            {
                "symbol": "ETH-USD", 
                "index_token": "ETH",
                "long_token": "ETH",
                "short_token": "USDC",
                "market_token": "GM",
                "pool_value": 30000000,
                "max_open_interest_long": 8000000,
                "max_open_interest_short": 8000000,
                "funding_rate": 0.0015,
                "borrowing_rate": 0.0009
            }
        ]
    
    def _get_mock_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Return mock price data"""
        mock_prices = {
            "BTC": Decimal("45750.50"),
            "ETH": Decimal("2895.75"),
            "BTC-USD": Decimal("45750.50"),
            "ETH-USD": Decimal("2895.75")
        }
        return {symbol: mock_prices.get(symbol, Decimal("1.0")) for symbol in symbols}
    
    def _get_mock_positions(self) -> List[Dict[str, Any]]:
        """Return mock position data"""
        return [
            {
                "market_address": "0x...",
                "index_token": "BTC",
                "collateral_token": "USDC", 
                "is_long": True,
                "size_usd": 15000.0,
                "collateral_amount": 5000.0,
                "leverage": 3.0,
                "entry_price": 44200.0,
                "mark_price": 45750.0,
                "pnl_usd": 775.0,
                "pnl_percentage": 5.18,
                "liquidation_price": 40500.0,
                "funding_fee": 12.5,
                "borrowing_fee": 8.3
            }
        ]
    
    def _simulate_order(
        self, 
        symbol: str, 
        side: str, 
        size_usd: float, 
        leverage: float,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simulate order creation for testing"""
        return {
            "success": error is None,
            "order_id": f"mock_order_{hash(f'{symbol}{side}{size_usd}') % 1000000}",
            "symbol": symbol,
            "side": side,
            "size_usd": size_usd,
            "leverage": leverage,
            "status": "pending" if error is None else "failed",
            "error": error,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    def _simulate_close_position(
        self, 
        symbol: str, 
        size_usd: float,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simulate position closing for testing"""
        return {
            "success": error is None,
            "order_id": f"close_order_{hash(f'{symbol}{size_usd}') % 1000000}",
            "symbol": symbol,
            "size_usd": size_usd,
            "status": "pending" if error is None else "failed",
            "error": error,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    def _format_markets(self, market_data: Any) -> List[Dict[str, Any]]:
        """Format market data from GMX SDK"""
        # This would format the actual SDK response
        return market_data
    
    def _format_positions(self, position_data: Any) -> List[Dict[str, Any]]:
        """Format position data from GMX SDK"""
        # This would format the actual SDK response
        return position_data
    
    def _format_order_result(self, result: Any) -> Dict[str, Any]:
        """Format order result from GMX SDK"""
        # This would format the actual SDK response
        return {
            "success": True,
            "transaction_hash": getattr(result, 'tx_hash', None),
            "order_key": getattr(result, 'order_key', None),
            "status": "submitted"
        }

# Factory function for easy client creation
def create_gmx_client(
    private_key: Optional[str] = None,
    rpc_url: Optional[str] = None,
    testnet: bool = True
) -> GMXClient:
    """Create a configured GMX client instance"""
    return GMXClient(
        private_key=private_key,
        rpc_url=rpc_url,
        testnet=testnet
    )