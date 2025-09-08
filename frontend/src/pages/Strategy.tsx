import { useState } from 'react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

interface StrategyConfig {
  id: string;
  name: string;
  enabled: boolean;
  parameters: Record<string, any>;
}

interface BacktestResult {
  period: string;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  totalTrades: number;
}

const strategies: StrategyConfig[] = [
  {
    id: 'ema_crossover',
    name: 'EMA Crossover',
    enabled: true,
    parameters: {
      fastPeriod: 12,
      slowPeriod: 26,
      minSpread: 0.001,
      positionSize: 0.005,
      stopLoss: 0.02,
      takeProfit: 0.03
    }
  },
  {
    id: 'rsi_mean_reversion',
    name: 'RSI Mean Reversion',
    enabled: false,
    parameters: {
      period: 14,
      oversoldLevel: 30,
      overboughtLevel: 70,
      positionSize: 0.003,
      stopLoss: 0.015,
      takeProfit: 0.025
    }
  },
  {
    id: 'momentum',
    name: 'Momentum Strategy',
    enabled: false,
    parameters: {
      lookbackPeriod: 20,
      momentumThreshold: 0.02,
      volumeConfirmation: true,
      positionSize: 0.004,
      stopLoss: 0.025,
      takeProfit: 0.04
    }
  }
];

const backtestData = [
  { date: '2024-01-01', portfolio: 10000, benchmark: 10000 },
  { date: '2024-01-02', portfolio: 10150, benchmark: 10080 },
  { date: '2024-01-03', portfolio: 10080, benchmark: 10120 },
  { date: '2024-01-04', portfolio: 10320, benchmark: 10200 },
  { date: '2024-01-05', portfolio: 10280, benchmark: 10180 },
  { date: '2024-01-06', portfolio: 10450, benchmark: 10250 },
  { date: '2024-01-07', portfolio: 10520, benchmark: 10300 },
  { date: '2024-01-08', portfolio: 10480, benchmark: 10280 },
  { date: '2024-01-09', portfolio: 10650, benchmark: 10350 },
  { date: '2024-01-10', portfolio: 10720, benchmark: 10400 },
];

const backtestResults: BacktestResult = {
  period: '30D',
  totalReturn: 7.2,
  sharpeRatio: 1.85,
  maxDrawdown: -2.1,
  winRate: 68.5,
  totalTrades: 42
};

export function Strategy() {
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyConfig>(strategies[0]);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [showBacktest, setShowBacktest] = useState(false);

  const handleParameterChange = (key: string, value: any) => {
    setSelectedStrategy(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [key]: value
      }
    }));
  };

  const handleStrategyToggle = (strategyId: string) => {
    const updatedStrategies = strategies.map(s => 
      s.id === strategyId 
        ? { ...s, enabled: !s.enabled }
        : s
    );
    console.log('Updated strategies:', updatedStrategies);
  };

  const handleBacktest = async () => {
    setIsBacktesting(true);
    // Simulate backtest execution
    setTimeout(() => {
      setIsBacktesting(false);
      setShowBacktest(true);
    }, 3000);
  };

  const handleSaveStrategy = () => {
    console.log('Saving strategy:', selectedStrategy);
    // In real app, this would save to your API
  };

  return (
    <div className="p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Strategy Configuration</h1>
          <p className="text-gray-400">Configure and backtest your trading strategies</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button 
            onClick={handleBacktest}
            disabled={isBacktesting}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {isBacktesting ? 'Running Backtest...' : 'Run Backtest'}
          </button>
          <button 
            onClick={handleSaveStrategy}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Save Configuration
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Strategy List */}
        <div className="space-y-3">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Available Strategies</h3>
            </CardHeader>
            <CardContent className="space-y-3">
              {strategies.map((strategy) => (
                <div 
                  key={strategy.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedStrategy.id === strategy.id
                      ? 'border-blue-500 bg-blue-900/20'
                      : 'border-gray-700 hover:border-gray-600'
                  }`}
                  onClick={() => setSelectedStrategy(strategy)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-white">{strategy.name}</div>
                      <div className="text-sm text-gray-400">{strategy.id}</div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStrategyToggle(strategy.id);
                        }}
                        className={`w-10 h-6 rounded-full transition-colors relative ${
                          strategy.enabled ? 'bg-green-600' : 'bg-gray-600'
                        }`}
                      >
                        <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                          strategy.enabled ? 'translate-x-5' : 'translate-x-1'
                        }`} />
                      </button>
                    </div>
                  </div>
                  
                  {strategy.enabled && (
                    <div className="mt-2 text-xs">
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full">
                        ACTIVE
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Quick Stats</h3>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Active Strategies:</span>
                <span className="text-white font-medium">
                  {strategies.filter(s => s.enabled).length}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Signals Today:</span>
                <span className="text-white font-medium">15</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Executed:</span>
                <span className="text-green-400 font-medium">12</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Success Rate:</span>
                <span className="text-blue-400 font-medium">80%</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Strategy Configuration */}
        <div className="lg:col-span-2 space-y-3">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">
                {selectedStrategy.name} Configuration
              </h3>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(selectedStrategy.parameters).map(([key, value]) => (
                  <div key={key}>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                    </label>
                    {typeof value === 'boolean' ? (
                      <div className="flex items-center">
                        <button
                          onClick={() => handleParameterChange(key, !value)}
                          className={`w-10 h-6 rounded-full transition-colors relative ${
                            value ? 'bg-blue-600' : 'bg-gray-600'
                          }`}
                        >
                          <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                            value ? 'translate-x-5' : 'translate-x-1'
                          }`} />
                        </button>
                      </div>
                    ) : (
                      <input
                        type="number"
                        step={typeof value === 'number' && value < 1 ? '0.001' : '1'}
                        value={value}
                        onChange={(e) => handleParameterChange(key, parseFloat(e.target.value) || 0)}
                        className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                      />
                    )}
                  </div>
                ))}
              </div>

              {/* Strategy Description */}
              <div className="mt-6 p-4 bg-gray-800 rounded-lg">
                <h4 className="font-medium text-white mb-2">Strategy Description</h4>
                <p className="text-sm text-gray-300">
                  {selectedStrategy.id === 'ema_crossover' && 
                    'This strategy uses exponential moving averages to identify trend changes. It generates buy signals when the fast EMA crosses above the slow EMA and sell signals when it crosses below.'
                  }
                  {selectedStrategy.id === 'rsi_mean_reversion' && 
                    'This strategy uses the Relative Strength Index to identify overbought and oversold conditions, entering positions when RSI reaches extreme levels expecting mean reversion.'
                  }
                  {selectedStrategy.id === 'momentum' && 
                    'This strategy identifies strong price momentum by analyzing price changes over a lookback period, entering positions in the direction of momentum with volume confirmation.'
                  }
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Backtest Results */}
          {showBacktest && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-white">Backtest Results</h3>
              </CardHeader>
              <CardContent>
                {/* Performance Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                  <div className="text-center p-3 bg-gray-800 rounded-lg">
                    <div className="text-xl font-bold text-green-400">
                      +{backtestResults.totalReturn}%
                    </div>
                    <div className="text-sm text-gray-400">Total Return</div>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-800 rounded-lg">
                    <div className="text-xl font-bold text-white">{backtestResults.sharpeRatio}</div>
                    <div className="text-sm text-gray-400">Sharpe Ratio</div>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-800 rounded-lg">
                    <div className="text-xl font-bold text-red-400">
                      {backtestResults.maxDrawdown}%
                    </div>
                    <div className="text-sm text-gray-400">Max Drawdown</div>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-800 rounded-lg">
                    <div className="text-xl font-bold text-blue-400">
                      {backtestResults.winRate}%
                    </div>
                    <div className="text-sm text-gray-400">Win Rate</div>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-800 rounded-lg">
                    <div className="text-xl font-bold text-white">{backtestResults.totalTrades}</div>
                    <div className="text-sm text-gray-400">Total Trades</div>
                  </div>

                  <div className="text-center p-3 bg-gray-800 rounded-lg">
                    <div className="text-xl font-bold text-gray-400">{backtestResults.period}</div>
                    <div className="text-sm text-gray-400">Period</div>
                  </div>
                </div>

                {/* Performance Chart */}
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={backtestData}>
                      <XAxis 
                        dataKey="date" 
                        stroke="#9CA3AF"
                        fontSize={11}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      />
                      <YAxis 
                        stroke="#9CA3AF"
                        fontSize={11}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1F2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                          color: '#F3F4F6'
                        }}
                        formatter={(value: number, name: string) => [
                          `$${value.toLocaleString()}`,
                          name === 'portfolio' ? 'Strategy' : 'Benchmark'
                        ]}
                        labelFormatter={(value) => new Date(value).toLocaleDateString()}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="portfolio" 
                        stroke="#10B981" 
                        strokeWidth={2}
                        dot={false}
                        name="Strategy"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="benchmark" 
                        stroke="#6B7280" 
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={false}
                        name="Benchmark"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}