# WolfHunt Backtesting Implementation Plan
**Status**: 61.5% Ready → 100% Complete Backtesting with Mock Wallet
**Estimated Development Time**: 8-12 hours
**Priority**: High - Close 38.5% implementation gap

## 🎯 Implementation Strategy

### Phase 1: Foundation (2-3 hours)
**Leverage existing paper trading infrastructure as the base**

#### 1.1 Directory Structure Setup
```
backend/src/trading/backtesting/
├── __init__.py
├── engine.py              # Core backtesting orchestration
├── mock_wallet.py         # Virtual portfolio state management
├── historical_data.py     # OHLCV data fetching and caching
├── performance.py         # Metrics calculation (Sharpe, drawdown, etc.)
└── utils.py              # Time series and data processing utilities
```

#### 1.2 Database Schema Extensions
```sql
-- Portfolio/Account balance tracking (missing component)
CREATE TABLE portfolios (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    initial_capital DECIMAL(15,2) NOT NULL,
    current_balance DECIMAL(15,2) NOT NULL,
    unrealized_pnl DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Backtest runs tracking
CREATE TABLE backtest_runs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    strategy_config JSONB NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15,2) NOT NULL,
    final_capital DECIMAL(15,2),
    total_return_pct DECIMAL(8,4),
    max_drawdown_pct DECIMAL(8,4),
    sharpe_ratio DECIMAL(8,4),
    status VARCHAR(20) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 2: Core Components (4-5 hours)

#### 2.1 Mock Wallet Implementation
**File**: `backend/src/trading/backtesting/mock_wallet.py`

```python
class MockWallet:
    """Virtual portfolio for backtesting with realistic trading simulation"""

    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.cash_balance = initial_capital
        self.positions = {}  # {symbol: {size, entry_price, timestamp}}
        self.trade_history = []
        self.portfolio_value_history = []

    def execute_trade(self, symbol: str, side: str, size: float, price: float,
                     timestamp: datetime, commission_rate: float = 0.001):
        """Execute trade with realistic slippage and commission"""

    def get_portfolio_value(self, current_prices: dict) -> float:
        """Calculate total portfolio value including positions"""

    def get_performance_metrics(self) -> dict:
        """Calculate returns, drawdown, Sharpe ratio"""
```

#### 2.2 Historical Data Service
**File**: `backend/src/trading/backtesting/historical_data.py`

```python
class HistoricalDataService:
    """Fetch and cache OHLCV data for backtesting"""

    def __init__(self):
        self.cache = {}  # In-memory caching for development

    async def get_ohlcv_data(self, symbol: str, start_date: datetime,
                           end_date: datetime, timeframe: str = '1h') -> pd.DataFrame:
        """Fetch historical OHLCV data from multiple sources"""
        # Primary: CoinGecko API (free tier: 10-50 calls/min)
        # Fallback: dYdX historical data
        # Cache: Store locally for repeated backtests

    def _fetch_coingecko_data(self, symbol: str, start: datetime, end: datetime):
        """CoinGecko historical price API integration"""

    def _cache_data(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """Cache historical data to avoid repeated API calls"""
```

#### 2.3 Backtesting Engine Core
**File**: `backend/src/trading/backtesting/engine.py`

```python
class BacktestEngine:
    """Core backtesting orchestration leveraging existing paper trading"""

    def __init__(self, strategy, mock_wallet: MockWallet,
                 historical_data: HistoricalDataService):
        self.strategy = strategy
        self.wallet = mock_wallet
        self.data_service = historical_data

    async def run_backtest(self, symbols: List[str], start_date: datetime,
                          end_date: datetime, strategy_config: dict) -> dict:
        """
        Main backtesting loop:
        1. Fetch historical data for date range
        2. Replay market conditions chronologically
        3. Execute strategy decisions via mock wallet
        4. Track performance metrics
        5. Return comprehensive results
        """

        # Leverage existing strategy framework from ma_crossover.py
        # Use paper trading execution logic with historical prices
        # Generate performance report
```

### Phase 3: API Integration (1-2 hours)

#### 3.1 Backtesting API Endpoints
**File**: `backend/src/api/backtesting_routes.py`

```python
@router.post("/backtesting/run", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest,
                      current_user: User = Depends(get_current_user)):
    """Execute backtest with historical data"""

@router.get("/backtesting/results/{backtest_id}")
async def get_backtest_results(backtest_id: str):
    """Retrieve completed backtest results"""

@router.get("/backtesting/history")
async def get_user_backtests(current_user: User = Depends(get_current_user)):
    """List user's previous backtests"""
```

#### 3.2 Frontend Integration Points
**Modify**: `frontend/src/pages/Strategy.tsx`

```typescript
// Connect existing "Run Backtest" button to real backend
const handleBacktest = async () => {
  const backtestRequest = {
    strategy_config: selectedStrategy.parameters,
    symbols: ['BTC', 'ETH', 'LINK'],
    start_date: backtestDateRange.start,
    end_date: backtestDateRange.end,
    initial_capital: 10000
  };

  const result = await api.post('/api/backtesting/run', backtestRequest);
  setBacktestResults(result.data);
};
```

### Phase 4: Performance & Optimization (1-2 hours)

#### 4.1 Performance Metrics Implementation
**File**: `backend/src/trading/backtesting/performance.py`

```python
class PerformanceCalculator:
    """Calculate comprehensive trading performance metrics"""

    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02):
    def calculate_max_drawdown(self, portfolio_values: pd.Series):
    def calculate_win_rate(self, trades: List[dict]):
    def calculate_profit_factor(self, trades: List[dict]):
    def generate_performance_report(self, wallet: MockWallet) -> dict:
```

#### 4.2 Data Optimization
- **Caching Strategy**: Store historical data locally to avoid repeated API calls
- **Batch Processing**: Fetch data in chunks to respect API rate limits
- **Memory Management**: Stream large datasets for multi-year backtests

## 🛠 Implementation Steps

### Step 1: Create Foundation (30 minutes)
```bash
# Create directory structure
mkdir -p backend/src/trading/backtesting
touch backend/src/trading/backtesting/__init__.py
touch backend/src/trading/backtesting/{engine,mock_wallet,historical_data,performance,utils}.py

# Add database migration
python backend/create_migration.py "Add backtesting tables"
```

### Step 2: Mock Wallet (90 minutes)
**Start with the missing portfolio balance tracking**
- Implement MockWallet class with position management
- Connect to existing Trade models
- Add portfolio value calculation
- Test with simple buy/hold scenario

### Step 3: Historical Data (120 minutes)
**Integrate with CoinGecko API (free tier)**
- Build OHLCV data fetcher with caching
- Handle API rate limits and fallbacks
- Create data preprocessing utilities
- Test with BTC/ETH/LINK historical data

### Step 4: Backtesting Engine (150 minutes)
**Leverage existing strategy and paper trading code**
- Create time series replay mechanism
- Integrate with existing MovingAverageCrossover strategy
- Connect mock wallet execution
- Generate basic performance metrics

### Step 5: API Integration (60 minutes)
**Connect frontend to backend**
- Add backtesting routes to FastAPI
- Modify existing Strategy.tsx backtest button
- Test end-to-end backtest execution
- Display results in existing UI components

### Step 6: Testing & Validation (60 minutes)
**Ensure reliability**
- Test with known profitable/losing scenarios
- Validate performance metric calculations
- Check edge cases (insufficient balance, etc.)
- Compare against manual calculations

## 📊 Expected Outcomes

### Immediate Capabilities (After Implementation)
- **Full Backtesting**: Run strategies over historical periods
- **Mock Wallet**: Virtual $10K starting portfolio
- **Performance Metrics**: Returns, Sharpe ratio, max drawdown, win rate
- **Multi-Asset**: BTC, ETH, LINK backtesting
- **Strategy Testing**: Validate MovingAverageCrossover parameters

### Sample Backtest Output
```json
{
  "strategy_name": "EMA Crossover",
  "period": "2024-01-01 to 2024-12-31",
  "initial_capital": 10000,
  "final_capital": 12850,
  "total_return_pct": 28.5,
  "max_drawdown_pct": -15.2,
  "sharpe_ratio": 1.35,
  "win_rate": 62.5,
  "total_trades": 87,
  "avg_trade_return": 0.85
}
```

## 🚀 Quick Start Options

### Option A: Minimal Viable Backtest (2-3 hours)
Focus on core functionality only:
1. Simple MockWallet with basic position tracking
2. CoinGecko historical data integration
3. Basic backtest loop with existing strategy
4. Connect to existing frontend button

### Option B: Production-Ready System (8-12 hours)
Complete implementation with:
1. Full performance metrics suite
2. Database persistence for backtest history
3. Advanced caching and optimization
4. Comprehensive error handling and logging

## 💡 Key Advantages of This Approach

1. **Leverage Existing Code**: 61.5% already implemented
2. **Proven Components**: Paper trading system works
3. **Incremental Development**: Each phase adds value
4. **Low Risk**: Build on stable foundation
5. **Fast Time-to-Value**: Working backtest in 2-3 hours

Ready to start implementation? I recommend beginning with Option A (Minimal Viable Backtest) to get quick results, then expanding to full production system.