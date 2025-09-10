// API service for connecting to the GMX trading bot backend
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/.netlify/functions' // Use Netlify Functions in production (direct path to working function)
  : 'http://localhost:8000'; // Local development - connect to local backend

// Types for API responses
export interface DashboardData {
  total_equity: number;
  account_balance: number;
  daily_pnl: number;
  daily_pnl_percent: number;
  total_unrealized_pnl: number;
  available_margin: number;
  used_margin: number;
  margin_utilization: number;
  open_positions: number;
  total_trades: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown: number;
  system_status: string;
  trading_enabled: boolean;
  paper_mode: boolean;
}

export interface Position {
  id: number;
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  notional_value: number;
  margin_used: number;
  leverage: number;
  stop_loss_price?: number;
  take_profit_price?: number;
  liquidation_price: number;
  strategy_name: string;
  opened_at: string;
  updated_at: string;
}

export interface Trade {
  id: number;
  order_id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  order_type: string;
  size: number;
  price: number;
  filled_size: number;
  notional_value: number;
  commission: number;
  realized_pnl: number;
  status: string;
  strategy_name: string;
  signal_strength?: number;
  entry_reason?: string;
  timestamp: string;
  created_at: string;
}

export interface StrategyConfig {
  strategy_name: string;
  ema_fast_period: number;
  ema_slow_period: number;
  rsi_period: number;
  rsi_oversold: number;
  rsi_overbought: number;
  max_position_size_pct: number;
  max_leverage: number;
  stop_loss_pct: number;
  take_profit_ratio: number;
  daily_loss_limit: number;
  enabled: boolean;
  paper_mode: boolean;
}

export interface PerformanceMetrics {
  period_days: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  net_pnl: number;
  total_volume: number;
  total_commission: number;
  avg_win: number;
  avg_loss: number;
  risk_reward_ratio: number;
  sharpe_ratio: number;
  max_drawdown: number;
  error?: string;
}

class ApiService {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    // Try to get token from localStorage
    this.token = localStorage.getItem('auth_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
      ...options,
    };

    let response: Response;
    let responseText: string;
    
    try {
      response = await fetch(url, config);
      // Always read the body once and only once
      responseText = await response.text();
    } catch (error) {
      console.error(`Network Error (${endpoint}):`, error);
      throw error;
    }

    try {
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, redirect to login
          localStorage.removeItem('auth_token');
          this.token = null;
          throw new Error('Authentication required');
        }
        
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        if (responseText) {
          try {
            const errorData = JSON.parse(responseText);
            errorMessage = errorData.detail || errorMessage;
          } catch (parseError) {
            // If JSON parsing fails, use the raw text or default message
            errorMessage = responseText || errorMessage;
          }
        }
        
        throw new Error(errorMessage);
      }

      // Parse successful response
      if (!responseText) {
        return {};
      }
      
      return JSON.parse(responseText);
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  // Authentication
  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  // Dashboard API
  async getDashboardData(): Promise<DashboardData> {
    return this.request<DashboardData>('/api/trading/dashboard');
  }

  // Positions API
  async getPositions(symbol?: string): Promise<Position[]> {
    const params = symbol ? `?symbol=${encodeURIComponent(symbol)}` : '';
    return this.request<Position[]>(`/api/trading/positions${params}`);
  }

  async closePosition(positionId: number): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/trading/positions/${positionId}/close`, {
      method: 'POST',
    });
  }

  // Trades API
  async getTrades(params: {
    limit?: number;
    offset?: number;
    symbol?: string;
    strategy?: string;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<Trade[]> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });
    
    const queryString = queryParams.toString();
    const endpoint = `/api/trading/trades${queryString ? `?${queryString}` : ''}`;
    
    return this.request<Trade[]>(endpoint);
  }

  // Strategy API
  async getStrategyConfig(): Promise<StrategyConfig> {
    return this.request<StrategyConfig>('/api/trading/strategy/config');
  }

  async updateStrategyConfig(config: Partial<StrategyConfig>): Promise<StrategyConfig> {
    return this.request<StrategyConfig>('/api/trading/strategy/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Emergency Controls
  async emergencyStop(reason: string, closePositions: boolean = true): Promise<{
    success: boolean;
    message: string;
    trading_enabled: boolean;
    timestamp: string;
  }> {
    return this.request('/api/trading/emergency-stop', {
      method: 'POST',
      body: JSON.stringify({
        reason,
        close_positions: closePositions,
      }),
    });
  }

  async resumeTrading(): Promise<{
    success: boolean;
    message: string;
    trading_enabled: boolean;
    timestamp: string;
  }> {
    return this.request('/api/trading/resume-trading', {
      method: 'POST',
    });
  }

  // Performance API
  async getPerformanceMetrics(days: number = 30): Promise<PerformanceMetrics> {
    return this.request<PerformanceMetrics>(`/api/trading/performance?days=${days}`);
  }

  // Signals API
  async getRecentSignals(params: {
    limit?: number;
    strategy?: string;
    symbol?: string;
  } = {}): Promise<any[]> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, value.toString());
      }
    });
    
    const queryString = queryParams.toString();
    const endpoint = `/api/trading/signals${queryString ? `?${queryString}` : ''}`;
    
    return this.request(endpoint);
  }

  // Health API
  async getSystemHealth(): Promise<{
    status: string;
    timestamp: string;
    checks: Record<string, string>;
    version: string;
  }> {
    return this.request('/api/trading/health');
  }

  // Check if API is available
  async checkConnection(): Promise<boolean> {
    try {
      await this.getSystemHealth();
      return true;
    } catch (error) {
      console.warn('Backend API not available:', error);
      return false;
    }
  }

  // GMX Price Feeds - Direct API Integration with CoinGecko backup
  async getGMXPrices(): Promise<{[symbol: string]: {price: number, change24h: number}}> {
    try {
      console.log('Fetching real prices from CoinGecko API...');
      
      // Use CoinGecko for reliable price and 24h change data
      const response = await fetch(
        'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,chainlink&vs_currencies=usd&include_24hr_change=true'
      );
      
      if (!response.ok) {
        throw new Error(`CoinGecko API responded with ${response.status}`);
      }
      
      const coinGeckoData = await response.json();
      
      const prices = {
        'BTC-USD': {
          price: coinGeckoData.bitcoin?.usd || 95000,
          change24h: coinGeckoData.bitcoin?.usd_24h_change || 0
        },
        'ETH-USD': {
          price: coinGeckoData.ethereum?.usd || 4200,
          change24h: coinGeckoData.ethereum?.usd_24h_change || 0
        },
        'LINK-USD': {
          price: coinGeckoData.chainlink?.usd || 23.50,
          change24h: coinGeckoData.chainlink?.usd_24h_change || 0
        }
      };
      
      console.log('Real CoinGecko prices loaded:', prices);
      return prices;
      
    } catch (error) {
      console.warn('CoinGecko API failed, trying GMX API:', error);
      
      // Fallback to GMX API
      try {
        const response = await fetch('https://arbitrum-api.gmxinfra.io/prices/tickers');
        if (!response.ok) {
          throw new Error(`GMX API responded with ${response.status}`);
        }
        
        const gmxData = await response.json();
        
        // GMX token addresses mapping
        const tokenMapping: {[address: string]: string} = {
          '0x47904963fc8b2340414262125aF798B9655E58Cd': 'BTC-USD',
          '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1': 'ETH-USD',
          '0xf97f4df75117a78c1A5a0DBb814Af92458539FB4': 'LINK-USD'
        };
        
        const prices: {[symbol: string]: {price: number, change24h: number}} = {};
        
        for (const ticker of gmxData) {
          const symbol = tokenMapping[ticker.tokenAddress];
          if (symbol && ticker.minPrice) {
            // Convert GMX price format (30 decimals)
            const price = parseFloat(ticker.minPrice) / Math.pow(10, 30);
            prices[symbol] = { price: price, change24h: 0 };
          }
        }
        
        console.log('GMX API prices loaded as fallback:', prices);
        return prices;
        
      } catch (gmxError) {
        console.warn('Both APIs failed, using static fallback:', gmxError);
        // Final fallback to static prices
        return {
          'BTC-USD': { price: 95000, change24h: 1.67 },
          'ETH-USD': { price: 4200, change24h: 1.58 },
          'LINK-USD': { price: 23.50, change24h: 3.61 }
        };
      }
    }
  }

  // Wolf Pack Intelligence API Methods
  async getUnifiedIntelligence(): Promise<any> {
    return this.request('/api/v1/unified-intelligence');
  }

  async getLiveSignals(): Promise<any> {
    return this.request('/api/v1/live-signals');
  }

  async executeStrategySuggestion(suggestionData: any): Promise<any> {
    return this.request('/api/v1/execute-suggestion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(suggestionData),
    });
  }

  async getPerformanceMetrics(): Promise<any> {
    return this.request('/api/v1/performance-metrics');
  }

  async getAutomationStatus(): Promise<any> {
    return this.request('/api/v1/automation/status');
  }

  async getSystemHealthV1(): Promise<any> {
    return this.request('/api/v1/system-health');
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export mock data fallback for when backend is not available
export const getMockDashboardData = (): DashboardData => ({
  total_equity: 99843,
  account_balance: 98000,
  daily_pnl: 2156,
  daily_pnl_percent: 2.34,
  total_unrealized_pnl: 1245,
  available_margin: 91323,
  used_margin: 8520,
  margin_utilization: 8.7,
  open_positions: 2,
  total_trades: 12,
  win_rate: 68.5,
  sharpe_ratio: 1.45,
  max_drawdown: 1.2,
  system_status: 'healthy',
  trading_enabled: true,
  paper_mode: true,
});

export const getMockPositions = (): Position[] => [
  {
    id: 1,
    symbol: 'BTC-USD',
    side: 'LONG',
    size: 0.5,
    entry_price: 44200,
    mark_price: 45750,
    unrealized_pnl: 775,
    unrealized_pnl_percent: 1.75,
    notional_value: 22875,
    margin_used: 7625,
    leverage: 3.0,
    liquidation_price: 40500,
    strategy_name: 'MovingAverageCrossover',
    opened_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    symbol: 'ETH-USD',
    side: 'SHORT',
    size: -2.0,
    entry_price: 2920,
    mark_price: 2895,
    unrealized_pnl: 50,
    unrealized_pnl_percent: 0.86,
    notional_value: 5790,
    margin_used: 1930,
    leverage: 3.0,
    liquidation_price: 3200,
    strategy_name: 'MovingAverageCrossover',
    opened_at: new Date(Date.now() - 1800000).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const getMockTrades = (): Trade[] => [
  {
    id: 1,
    order_id: 'order_001',
    symbol: 'BTC-USD',
    side: 'BUY',
    order_type: 'MARKET',
    size: 0.25,
    price: 44800,
    filled_size: 0.25,
    notional_value: 11200,
    commission: 11.2,
    realized_pnl: 237.5,
    status: 'FILLED',
    strategy_name: 'MovingAverageCrossover',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 2,
    order_id: 'order_002',
    symbol: 'LINK-USD',
    side: 'SELL',
    order_type: 'MARKET',
    size: -100,
    price: 15.62,
    filled_size: -100,
    notional_value: 1562,
    commission: 1.56,
    realized_pnl: -23.0,
    status: 'FILLED',
    strategy_name: 'MovingAverageCrossover',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    created_at: new Date(Date.now() - 1800000).toISOString(),
  },
];