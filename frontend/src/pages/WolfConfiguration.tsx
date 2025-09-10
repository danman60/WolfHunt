import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { PositionsTable } from '../components/dashboard/PositionsTable';
import type { Position } from '../components/dashboard/PositionsTable';
import { apiService, getMockPositions } from '../services/api';

interface StrategyConfig {
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

interface PortfolioAllocation {
  'BTC-USD': number;
  'ETH-USD': number;
  'LINK-USD': number;
}

export function WolfConfiguration() {
  const [strategyConfig, setStrategyConfig] = useState<StrategyConfig>({
    strategy_name: 'MovingAverageCrossover',
    ema_fast_period: 12,
    ema_slow_period: 26,
    rsi_period: 14,
    rsi_oversold: 30,
    rsi_overbought: 70,
    max_position_size_pct: 0.25,
    max_leverage: 3.0,
    stop_loss_pct: 0.02,
    take_profit_ratio: 2.0,
    daily_loss_limit: 1000,
    enabled: true,
    paper_mode: false
  });

  const [portfolioAllocation, setPortfolioAllocation] = useState<PortfolioAllocation>({
    'BTC-USD': 60,
    'ETH-USD': 30,
    'LINK-USD': 10
  });

  const [positions, setPositions] = useState<Position[]>([]);
  const [gmxPrices, setGmxPrices] = useState<{[symbol: string]: {price: number, change24h: number}}>({});
  const [botRunning, setBotRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);

  // Fetch current positions and prices
  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Get real prices with fallback
      try {
        const prices = await apiService.getGMXPrices();
        if (prices && typeof prices === 'object') {
          setGmxPrices(prices);
        } else {
          throw new Error('Invalid price data received');
        }
      } catch (priceError) {
        console.warn('Failed to fetch prices, using fallback:', priceError);
        setGmxPrices({
          'BTC-USD': { price: 95000, change24h: 1.67 },
          'ETH-USD': { price: 4200, change24h: 1.58 },
          'LINK-USD': { price: 23.50, change24h: 3.61 }
        });
      }
      
      // Try to get strategy config
      try {
        const config = await apiService.getStrategyConfig();
        if (config && typeof config === 'object') {
          setStrategyConfig(config);
          setApiConnected(true);
        } else {
          throw new Error('Invalid strategy config received');
        }
      } catch (error) {
        console.warn('Strategy config API not available - using demo mode:', error);
        setApiConnected(false);
        // Keep using the default strategy config when API is unavailable
      }

      // Get positions (using mock for now)
      try {
        const mockPositions = getMockPositions();
        if (Array.isArray(mockPositions)) {
          setPositions(mockPositions);
        }
      } catch (positionError) {
        console.warn('Failed to get positions:', positionError);
        setPositions([]);
      }
      
    } catch (error) {
      console.error('Error fetching configuration data:', error);
      setApiConnected(false);
      // Set safe fallback data
      setGmxPrices({
        'BTC-USD': { price: 95000, change24h: 1.67 },
        'ETH-USD': { price: 4200, change24h: 1.58 },
        'LINK-USD': { price: 23.50, change24h: 3.61 }
      });
      setPositions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh prices every 30 seconds with error handling
    const interval = setInterval(async () => {
      try {
        const prices = await apiService.getGMXPrices();
        if (prices && typeof prices === 'object') {
          setGmxPrices(prices);
        }
      } catch (error) {
        console.warn('Failed to refresh prices:', error);
        // Don't update state on error to keep existing data
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const handleStopBot = async () => {
    try {
      setLoading(true);
      await apiService.emergencyStop('User requested bot stop', false);
      setBotRunning(false);
      console.log('Bot stopped successfully');
    } catch (error) {
      console.error('Failed to stop bot:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResumeBot = async () => {
    try {
      setLoading(true);
      await apiService.resumeTrading();
      setBotRunning(true);
      console.log('Bot resumed successfully');
    } catch (error) {
      console.error('Failed to resume bot:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveStrategy = async () => {
    try {
      setLoading(true);
      if (apiConnected) {
        await apiService.updateStrategyConfig(strategyConfig);
        console.log('Strategy configuration saved to backend');
      } else {
        console.log('Demo mode - strategy configuration saved locally');
        // In demo mode, the config is only saved locally in state
      }
    } catch (error) {
      console.error('Failed to save strategy:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAllocationChange = (symbol: string, value: number) => {
    setPortfolioAllocation(prev => {
      const newAllocation = { ...prev, [symbol]: value };
      // Ensure total doesn't exceed 100%
      const total = Object.values(newAllocation).reduce((sum, val) => sum + val, 0);
      if (total <= 100) {
        return newAllocation;
      }
      return prev;
    });
  };

  const getTotalAllocation = () => {
    return Object.values(portfolioAllocation).reduce((sum, val) => sum + val, 0);
  };

  return (
    <div className="p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">🐺 Wolf Configuration</h1>
          <p className="text-gray-400">Configure your GMX trading bot strategies and portfolio allocation</p>
        </div>
        
        {/* Quick Actions */}
        <div className="flex items-center space-x-3">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            botRunning ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            Bot: {botRunning ? 'RUNNING' : 'STOPPED'}
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            apiConnected ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'
          }`}>
            {apiConnected ? 'LIVE' : 'DEMO'}
          </div>
          
          {botRunning ? (
            <button 
              onClick={handleStopBot}
              disabled={loading}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? 'Stopping...' : 'STOP BOT'}
            </button>
          ) : (
            <button 
              onClick={handleResumeBot}
              disabled={loading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? 'Starting...' : 'RESUME BOT'}
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
        
        {/* Left Column - Strategy Configuration */}
        <div className="xl:col-span-1 space-y-3">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Strategy Settings</h3>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Strategy Type</label>
                <select 
                  value={strategyConfig.strategy_name}
                  onChange={(e) => setStrategyConfig(prev => ({ ...prev, strategy_name: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                >
                  <option value="MovingAverageCrossover">Moving Average Crossover</option>
                  <option value="RSIMeanReversion">RSI Mean Reversion</option>
                  <option value="TrendFollowing">Trend Following</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Fast EMA</label>
                  <input 
                    type="number" 
                    value={strategyConfig.ema_fast_period}
                    onChange={(e) => setStrategyConfig(prev => ({ ...prev, ema_fast_period: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Slow EMA</label>
                  <input 
                    type="number" 
                    value={strategyConfig.ema_slow_period}
                    onChange={(e) => setStrategyConfig(prev => ({ ...prev, ema_slow_period: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Max Leverage</label>
                  <input 
                    type="number" 
                    value={strategyConfig.max_leverage}
                    onChange={(e) => setStrategyConfig(prev => ({ ...prev, max_leverage: parseFloat(e.target.value) }))}
                    step="0.1"
                    min="1"
                    max="10"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Stop Loss %</label>
                  <input 
                    type="number" 
                    value={strategyConfig.stop_loss_pct * 100}
                    onChange={(e) => setStrategyConfig(prev => ({ ...prev, stop_loss_pct: parseFloat(e.target.value) / 100 }))}
                    step="0.1"
                    min="0.1"
                    max="10"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                  />
                </div>
              </div>

              <button 
                onClick={handleSaveStrategy}
                disabled={loading}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Strategy'}
              </button>
            </CardContent>
          </Card>

          {/* Portfolio Allocation */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Portfolio Allocation</h3>
              <p className="text-sm text-gray-400">Total: {getTotalAllocation()}%</p>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(portfolioAllocation).map(([symbol, percentage]) => {
                const priceData = gmxPrices[symbol] || {};
                const price = typeof priceData.price === 'number' && !isNaN(priceData.price) ? priceData.price : 0;
                const change = typeof priceData.change24h === 'number' && !isNaN(priceData.change24h) ? priceData.change24h : 0;
                
                return (
                  <div key={symbol} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="text-white font-medium">{symbol}</span>
                        {price > 0 && (
                          <div className="text-sm text-gray-400">
                            ${typeof price === 'number' && !isNaN(price) ? price.toLocaleString() : '0'} 
                            <span className={`ml-1 ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {change >= 0 ? '+' : ''}{typeof change === 'number' && !isNaN(change) ? change.toFixed(2) : '0.00'}%
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <input 
                          type="number" 
                          value={percentage}
                          onChange={(e) => handleAllocationChange(symbol, parseInt(e.target.value) || 0)}
                          min="0"
                          max="100"
                          className="w-16 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm text-center"
                        />
                        <span className="text-gray-400">%</span>
                      </div>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
              
              {getTotalAllocation() !== 100 && (
                <div className={`text-sm p-2 rounded ${
                  getTotalAllocation() > 100 
                    ? 'bg-red-900/20 text-red-400 border border-red-500' 
                    : 'bg-yellow-900/20 text-yellow-400 border border-yellow-500'
                }`}>
                  {getTotalAllocation() > 100 
                    ? '⚠️ Total allocation exceeds 100%' 
                    : `📊 ${100 - getTotalAllocation()}% unallocated`
                  }
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Open Positions */}
        <div className="xl:col-span-2">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Open Positions</h3>
              <p className="text-sm text-gray-400">Current active positions managed by the bot</p>
            </CardHeader>
            <CardContent>
              <PositionsTable 
                positions={positions}
                onClosePosition={async (id) => {
                  try {
                    if (apiConnected) {
                      await apiService.closePosition(id);
                      fetchData(); // Refresh data
                    } else {
                      console.log('Demo mode - would close position:', id);
                    }
                  } catch (error) {
                    console.error('Error closing position:', error);
                  }
                }}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}