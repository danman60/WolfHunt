import { useState, useEffect } from 'react';
import { PortfolioStats } from '../components/dashboard/PortfolioStats';
import { TradingChart } from '../components/dashboard/TradingChart';
import { PositionsTable, Position } from '../components/dashboard/PositionsTable';
import { TradesTable, Trade } from '../components/dashboard/TradesTable';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';

const ResponsiveGridLayout = WidthProvider(Responsive);

// Mock data - focused on dYdX perpetuals trading bot performance
const mockPortfolioStats = [
  { label: 'Total Equity', value: '$99,843', change: 2.34, changeType: 'percentage' as const, color: 'blue' as const },
  { label: 'Daily P&L', value: '+$2,156', change: 2.34, changeType: 'percentage' as const, color: 'green' as const },
  { label: 'Unrealized P&L', value: '+$1,245', color: 'green' as const },
  { label: 'Used Margin', value: '$8,520', color: 'blue' as const },
  { label: 'Available Margin', value: '$91,323', color: 'gray' as const },
  { label: 'Win Rate', value: '68.5%', change: 3.2, changeType: 'percentage' as const, color: 'green' as const }
];

// dYdX perpetuals price data
const mockChartData = {
  'BTC-USD': [
    { time: '09:00', price: 45000, ema12: 44980, ema26: 44920, volume: 1250 },
    { time: '09:15', price: 45200, ema12: 45050, ema26: 44980, volume: 980 },
    { time: '09:30', price: 45400, ema12: 45180, ema26: 45080, volume: 1450 },
    { time: '09:45', price: 45300, ema12: 45250, ema26: 45150, volume: 1100 },
    { time: '10:00', price: 45500, ema12: 45350, ema26: 45220, volume: 1680 },
    { time: '10:15', price: 45600, ema12: 45450, ema26: 45300, volume: 920 },
    { time: '10:30', price: 45750, ema12: 45580, ema26: 45400, volume: 1380 }
  ],
  'ETH-USD': [
    { time: '09:00', price: 2850, ema12: 2845, ema26: 2840, volume: 2200 },
    { time: '09:15', price: 2860, ema12: 2852, ema26: 2843, volume: 1950 },
    { time: '09:30', price: 2875, ema12: 2863, ema26: 2848, volume: 2450 },
    { time: '09:45', price: 2870, ema12: 2867, ema26: 2852, volume: 2100 },
    { time: '10:00', price: 2885, ema12: 2874, ema26: 2857, volume: 2650 },
    { time: '10:15', price: 2890, ema12: 2880, ema26: 2862, volume: 1800 },
    { time: '10:30', price: 2895, ema12: 2886, ema26: 2867, volume: 2300 }
  ],
  'LINK-USD': [
    { time: '09:00', price: 15.20, ema12: 15.18, ema26: 15.15, volume: 8500 },
    { time: '09:15', price: 15.35, ema12: 15.25, ema26: 15.18, volume: 7200 },
    { time: '09:30', price: 15.45, ema12: 15.32, ema26: 15.22, volume: 9100 },
    { time: '09:45', price: 15.40, ema12: 15.37, ema26: 15.26, volume: 6800 },
    { time: '10:00', price: 15.55, ema12: 15.43, ema26: 15.30, volume: 8900 },
    { time: '10:15', price: 15.60, ema12: 15.48, ema26: 15.34, volume: 7500 },
    { time: '10:30', price: 15.75, ema12: 15.56, ema26: 15.38, volume: 8200 }
  ]
};

const mockPositions: Position[] = [
  { symbol: 'BTC-USD', side: 'LONG', size: 0.5, entryPrice: 44200, currentPrice: 45750, pnl: 775, percentage: 1.75, margin: 7350 },
  { symbol: 'ETH-USD', side: 'SHORT', size: -2.0, entryPrice: 2920, currentPrice: 2895, pnl: 50, percentage: 0.86, margin: 1460 }
];

const mockTrades: Trade[] = [
  { id: '1', symbol: 'BTC-USD', side: 'BUY', size: 0.25, price: 44800, time: '10:28:45', pnl: 237.50, status: 'FILLED' },
  { id: '2', symbol: 'LINK-USD', side: 'SELL', size: -100, price: 15.62, time: '10:15:23', pnl: -23.00, status: 'FILLED' },
  { id: '3', symbol: 'ETH-USD', side: 'SELL', size: -1.5, price: 2910, time: '09:45:12', pnl: 22.50, status: 'FILLED' }
];

const positionDistribution = [
  { name: 'BTC-USD', value: 65, exposure: '$7,350', color: '#F59E0B' },
  { name: 'ETH-USD', value: 25, exposure: '$1,460', color: '#3B82F6' },
  { name: 'LINK-USD', value: 10, exposure: '$520', color: '#10B981' }
];

// Bot performance metrics
const botMetrics = {
  status: 'ACTIVE',
  uptime: '4h 23m',
  lastSignal: '2 min ago',
  signalsToday: 34,
  executedToday: 12,
  avgExecutionTime: '156ms',
  successRate: 94.2,
  strategies: [
    { name: 'EMA Crossover', status: 'ACTIVE', positions: 2, performance: 2.45 },
    { name: 'RSI Momentum', status: 'ACTIVE', positions: 1, performance: 1.23 },
    { name: 'Volume Breakout', status: 'PAUSED', positions: 0, performance: -0.15 }
  ]
};

export function DashboardGrid() {
  const [selectedAsset, setSelectedAsset] = useState('BTC-USD');
  const [botStatus, setBotStatus] = useState(botMetrics);
  const [layouts, setLayouts] = useState({
    lg: [
      { i: 'bot-status', x: 0, y: 0, w: 12, h: 2, minH: 2 },
      { i: 'portfolio-stats', x: 0, y: 2, w: 12, h: 2, minH: 2 },
      { i: 'trading-chart', x: 0, y: 4, w: 8, h: 8, minH: 6 },
      { i: 'asset-selector', x: 8, y: 4, w: 2, h: 8, minH: 6 },
      { i: 'performance-metrics', x: 10, y: 4, w: 2, h: 4, minH: 3 },
      { i: 'strategy-status', x: 10, y: 8, w: 2, h: 4, minH: 3 },
      { i: 'open-positions', x: 0, y: 12, w: 6, h: 6, minH: 4 },
      { i: 'recent-trades', x: 6, y: 12, w: 6, h: 6, minH: 4 }
    ],
    md: [
      { i: 'bot-status', x: 0, y: 0, w: 10, h: 2, minH: 2 },
      { i: 'portfolio-stats', x: 0, y: 2, w: 10, h: 2, minH: 2 },
      { i: 'trading-chart', x: 0, y: 4, w: 10, h: 8, minH: 6 },
      { i: 'asset-selector', x: 0, y: 12, w: 5, h: 6, minH: 4 },
      { i: 'performance-metrics', x: 5, y: 12, w: 5, h: 6, minH: 4 },
      { i: 'strategy-status', x: 0, y: 18, w: 5, h: 4, minH: 3 },
      { i: 'open-positions', x: 5, y: 18, w: 5, h: 4, minH: 3 },
      { i: 'recent-trades', x: 0, y: 22, w: 10, h: 6, minH: 4 }
    ],
    sm: [
      { i: 'bot-status', x: 0, y: 0, w: 6, h: 2, minH: 2 },
      { i: 'portfolio-stats', x: 0, y: 2, w: 6, h: 3, minH: 2 },
      { i: 'trading-chart', x: 0, y: 5, w: 6, h: 8, minH: 6 },
      { i: 'asset-selector', x: 0, y: 13, w: 6, h: 6, minH: 4 },
      { i: 'performance-metrics', x: 0, y: 19, w: 6, h: 4, minH: 3 },
      { i: 'strategy-status', x: 0, y: 23, w: 6, h: 4, minH: 3 },
      { i: 'open-positions', x: 0, y: 27, w: 6, h: 6, minH: 4 },
      { i: 'recent-trades', x: 0, y: 33, w: 6, h: 6, minH: 4 }
    ]
  });

  // Mock real-time data updates for bot performance
  useEffect(() => {
    const interval = setInterval(() => {
      setBotStatus(prev => ({
        ...prev,
        signalsToday: prev.signalsToday + Math.floor(Math.random() * 2),
        executedToday: prev.executedToday + Math.floor(Math.random() * 1.5),
        avgExecutionTime: Math.floor(120 + Math.random() * 60) + 'ms',
        successRate: Math.max(90, Math.min(98, prev.successRate + (Math.random() - 0.5) * 2))
      }));
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const handleLayoutChange = (layout: Layout[], layouts: any) => {
    setLayouts(layouts);
  };

  return (
    <div className="p-2 h-screen bg-gray-950">
      <div className="mb-2 flex justify-between items-center">
        <h1 className="text-xl font-bold text-white">dYdX Trading Dashboard</h1>
        <div className="text-xs text-gray-400">Drag and resize panels • No dead space layout</div>
      </div>
      
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        onLayoutChange={handleLayoutChange}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={60}
        isDraggable={true}
        isResizable={true}
        margin={[4, 4]}
        containerPadding={[0, 0]}
      >
        {/* Bot Status Bar - Primary Focus */}
        <div key="bot-status">
          <Card className="bg-gradient-to-r from-blue-900 to-blue-800 border-blue-700 h-full">
            <CardContent className="p-3 h-full">
              <div className="flex items-center justify-between h-full">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full animate-pulse ${
                      botStatus.status === 'ACTIVE' ? 'bg-green-400' : 'bg-red-400'
                    }`}></div>
                    <span className="text-white font-semibold text-lg">WolfHunt Bot</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      botStatus.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>{botStatus.status}</span>
                  </div>
                  <div className="text-sm text-blue-200">
                    Uptime: <span className="text-white font-medium">{botStatus.uptime}</span>
                  </div>
                  <div className="text-sm text-blue-200">
                    Last Signal: <span className="text-white font-medium">{botStatus.lastSignal}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-4 text-sm">
                  <div className="text-center">
                    <div className="text-white font-bold text-lg">{botStatus.signalsToday}</div>
                    <div className="text-blue-200 text-xs">Signals Today</div>
                  </div>
                  <div className="text-center">
                    <div className="text-white font-bold text-lg">{botStatus.executedToday}</div>
                    <div className="text-blue-200 text-xs">Executed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-white font-bold text-lg">{botStatus.successRate.toFixed(1)}%</div>
                    <div className="text-blue-200 text-xs">Success Rate</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Portfolio Performance Stats */}
        <div key="portfolio-stats">
          <div className="h-full">
            <PortfolioStats stats={mockPortfolioStats} />
          </div>
        </div>

        {/* Trading Chart */}
        <div key="trading-chart">
          <div className="h-full">
            <TradingChart
              symbol={selectedAsset}
              data={mockChartData[selectedAsset] || mockChartData['BTC-USD']}
              currentPrice={selectedAsset === 'BTC-USD' ? 45750 : selectedAsset === 'ETH-USD' ? 2895 : 15.75}
              priceChange={selectedAsset === 'BTC-USD' ? 750 : selectedAsset === 'ETH-USD' ? 45 : 0.55}
              priceChangePercent={selectedAsset === 'BTC-USD' ? 1.67 : selectedAsset === 'ETH-USD' ? 1.58 : 3.61}
            />
          </div>
        </div>

        {/* Asset Selector */}
        <div key="asset-selector">
          <Card className="h-full">
            <CardHeader className="pb-2">
              <h3 className="text-base font-semibold text-white">dYdX Perpetuals</h3>
            </CardHeader>
            <CardContent className="space-y-2 overflow-y-auto">
              {['BTC-USD', 'ETH-USD', 'LINK-USD'].map((symbol) => {
                const price = symbol === 'BTC-USD' ? 45750 : symbol === 'ETH-USD' ? 2895 : 15.75;
                const change = symbol === 'BTC-USD' ? 1.67 : symbol === 'ETH-USD' ? 1.58 : 3.61;
                const changeAbs = symbol === 'BTC-USD' ? 750 : symbol === 'ETH-USD' ? 45 : 0.55;
                return (
                  <div 
                    key={symbol}
                    className={`p-2 rounded cursor-pointer transition-colors text-sm ${
                      selectedAsset === symbol 
                        ? 'bg-blue-600 border border-blue-500' 
                        : 'bg-gray-800 hover:bg-gray-700 border border-gray-700'
                    }`}
                    onClick={() => setSelectedAsset(symbol)}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium text-white text-xs">{symbol}</div>
                        <div className="text-lg font-bold text-white">
                          ${symbol === 'LINK-USD' ? price.toFixed(2) : price.toLocaleString()}
                        </div>
                      </div>
                      <div className={`text-right ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        <div className="text-xs font-medium">+{changeAbs}</div>
                        <div className="text-xs">+{change}%</div>
                      </div>
                    </div>
                  </div>
                );
              })}
              
              {/* Position Distribution Compact */}
              <div className="mt-4">
                <h4 className="text-sm font-medium text-white mb-2">Exposure</h4>
                <div className="h-24">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={positionDistribution}
                        cx="50%"
                        cy="50%"
                        innerRadius={15}
                        outerRadius={35}
                        paddingAngle={1}
                        dataKey="value"
                      >
                        {positionDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance Metrics */}
        <div key="performance-metrics">
          <Card className="h-full">
            <CardHeader className="pb-2">
              <h3 className="text-base font-semibold text-white">Performance Today</h3>
            </CardHeader>
            <CardContent className="space-y-3 overflow-y-auto">
              <div className="text-center">
                <div className="text-xl font-bold text-green-400">+$2,156</div>
                <div className="text-xs text-gray-400">Daily P&L</div>
                <div className="text-xs text-green-400">+2.34%</div>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="text-center p-2 bg-gray-800 rounded">
                  <div className="text-sm font-semibold text-white">{botStatus.executedToday}</div>
                  <div className="text-gray-400">Trades</div>
                </div>
                <div className="text-center p-2 bg-gray-800 rounded">
                  <div className="text-sm font-semibold text-white">1</div>
                  <div className="text-gray-400">Open</div>
                </div>
              </div>
              
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Execution</span>
                  <span className="text-white font-medium">{botStatus.avgExecutionTime}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Win Rate</span>
                  <span className="text-green-400 font-medium">68.5%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Max DD</span>
                  <span className="text-red-400 font-medium">-1.2%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Strategy Status */}
        <div key="strategy-status">
          <Card className="h-full">
            <CardHeader className="pb-2">
              <h3 className="text-base font-semibold text-white">Strategy Status</h3>
            </CardHeader>
            <CardContent className="space-y-2 overflow-y-auto">
              {botMetrics.strategies.map((strategy, index) => {
                const isActive = strategy.status === 'ACTIVE';
                const performanceColor = strategy.performance > 0 ? 'text-green-400' : 'text-red-400';
                return (
                  <div key={index} className="p-2 bg-gray-800 rounded text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-medium text-white text-xs">{strategy.name}</div>
                      <div className={`px-1 py-0.5 rounded text-xs font-medium ${
                        isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {strategy.status}
                      </div>
                    </div>
                    <div className="flex justify-between text-xs">
                      <div className="text-gray-400">
                        Positions: <span className="text-white">{strategy.positions}</span>
                      </div>
                      <div className={`font-medium ${performanceColor}`}>
                        {strategy.performance > 0 ? '+' : ''}{strategy.performance.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                );
              })}
              
              <div className="pt-2 border-t border-gray-700">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-medium text-white">Auto Trading</span>
                  <button className="w-6 h-3 bg-green-600 rounded-full relative">
                    <div className="w-2 h-2 bg-white rounded-full absolute top-0.5 right-0.5"></div>
                  </button>
                </div>
                <div className="text-xs text-gray-400">
                  Bot executing trades automatically
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Open Positions */}
        <div key="open-positions">
          <Card className="h-full">
            <CardHeader className="pb-2">
              <h3 className="text-base font-semibold text-white">Open Positions</h3>
            </CardHeader>
            <CardContent className="overflow-auto">
              <PositionsTable positions={mockPositions} />
            </CardContent>
          </Card>
        </div>

        {/* Recent Trades */}
        <div key="recent-trades">
          <Card className="h-full">
            <CardHeader className="pb-2">
              <h3 className="text-base font-semibold text-white">Recent Trades</h3>
            </CardHeader>
            <CardContent className="overflow-auto">
              <TradesTable trades={mockTrades} />
            </CardContent>
          </Card>
        </div>
      </ResponsiveGridLayout>
    </div>
  );
}