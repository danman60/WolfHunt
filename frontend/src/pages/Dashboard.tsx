import { useState, useEffect } from 'react';
import { PortfolioStats } from '../components/dashboard/PortfolioStats';
import { TradingChart } from '../components/dashboard/TradingChart';
import { PositionsTable } from '../components/dashboard/PositionsTable';
import type { Position } from '../components/dashboard/PositionsTable';
// import { TradesTable } from '../components/dashboard/TradesTable';
import type { Trade } from '../components/dashboard/TradesTable';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { apiService, getMockDashboardData, type DashboardData } from '../services/api';
import { WolfPackDashboard, LiveAlertBanner } from '../components/WolfPack/WolfPackIntelligence';

// Generate portfolio stats from dashboard data
const getPortfolioStats = (data: DashboardData | null) => {
  if (!data) {
    return [
      { label: 'Total Equity', value: '...', color: 'blue' as const },
      { label: 'Daily P&L', value: '...', color: 'green' as const },
      { label: 'Unrealized P&L', value: '...', color: 'green' as const },
      { label: 'Used Margin', value: '...', color: 'blue' as const },
      { label: 'Available Margin', value: '...', color: 'gray' as const },
      { label: 'Win Rate', value: '...', color: 'green' as const }
    ];
  }

  return [
    { 
      label: 'Total Equity', 
      value: `$${data.total_equity.toLocaleString()}`, 
      change: data.daily_pnl_percent, 
      changeType: 'percentage' as const, 
      color: 'blue' as const 
    },
    { 
      label: 'Daily P&L', 
      value: `${data.daily_pnl >= 0 ? '+' : ''}$${data.daily_pnl.toLocaleString()}`, 
      change: data.daily_pnl_percent, 
      changeType: 'percentage' as const, 
      color: data.daily_pnl >= 0 ? 'green' as const : 'red' as const 
    },
    { 
      label: 'Unrealized P&L', 
      value: `${data.total_unrealized_pnl >= 0 ? '+' : ''}$${data.total_unrealized_pnl.toLocaleString()}`, 
      color: data.total_unrealized_pnl >= 0 ? 'green' as const : 'red' as const 
    },
    { 
      label: 'Used Margin', 
      value: `$${data.used_margin.toLocaleString()}`, 
      color: 'blue' as const 
    },
    { 
      label: 'Available Margin', 
      value: `$${data.available_margin.toLocaleString()}`, 
      color: 'gray' as const 
    },
    { 
      label: 'Win Rate', 
      value: `${data.win_rate.toFixed(1)}%`, 
      change: 0, // Could track change over time
      changeType: 'percentage' as const, 
      color: 'green' as const 
    }
  ];
};

// GMX perpetuals price data
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
  {
    id: 1,
    symbol: 'LINK-USD',
    side: 'LONG',
    size: 10.0,
    entryPrice: 15.50,
    markPrice: 15.75,
    unrealizedPnl: 2.50,
    unrealizedPnlPercent: 1.61,
    leverage: 3.0,
    margin: 51.67,
    liquidationPrice: 14.25,
    openedAt: '2024-01-15T10:30:00Z'
  }
];

const mockTrades: Trade[] = [
  {
    id: 1,
    orderId: 'test_order_1',
    symbol: 'BTC-USD',
    side: 'BUY',
    orderType: 'MARKET',
    size: 0.001,
    price: 45000,
    filledSize: 0.001,
    notionalValue: 45,
    commission: 0.045,
    realizedPnl: 0,
    status: 'FILLED',
    strategyName: 'MovingAverageCrossover',
    timestamp: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: 2,
    orderId: 'test_order_2',
    symbol: 'BTC-USD',
    side: 'SELL',
    orderType: 'MARKET',
    size: 0.001,
    price: 45500,
    filledSize: 0.001,
    notionalValue: 45.5,
    commission: 0.045,
    realizedPnl: 4.55,
    status: 'FILLED',
    strategyName: 'MovingAverageCrossover',
    timestamp: new Date(Date.now() - 1800000).toISOString()
  }
];

// Mock data for additional charts
const volumeData = [
  { time: '09:00', volume: 1250 },
  { time: '10:00', volume: 2100 },
  { time: '11:00', volume: 1800 },
  { time: '12:00', volume: 2800 },
  { time: '13:00', volume: 1900 },
  { time: '14:00', volume: 3200 },
  { time: '15:00', volume: 2600 }
];

// GMX perpetuals position distribution
const positionDistribution = [
  { name: 'BTC-USD', value: 65.0, color: '#F59E0B', exposure: '$52,000' },
  { name: 'ETH-USD', value: 25.0, color: '#3B82F6', exposure: '$20,000' },
  { name: 'LINK-USD', value: 10.0, color: '#10B981', exposure: '$8,000' }
];

// Bot performance metrics
const botMetrics = {
  status: 'ACTIVE',
  uptime: '2d 14h 32m',
  lastSignal: '2m ago',
  signalsToday: 15,
  executedToday: 12,
  avgExecutionTime: '145ms',
  successRate: 94.2
};

// const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

export function Dashboard() {
  const [selectedAsset, setSelectedAsset] = useState('BTC-USD');
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [gmxPrices, setGmxPrices] = useState<{[symbol: string]: {price: number, change24h: number}}>({});
  // const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const [draggedPanel, setDraggedPanel] = useState<string | null>(null);
  const [botStatus, setBotStatus] = useState(botMetrics);

  const handleDragStart = (e: React.DragEvent, panelId: string) => {
    setDraggedPanel(panelId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragEnd = () => {
    setDraggedPanel(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetPanelId: string) => {
    e.preventDefault();
    if (draggedPanel && draggedPanel !== targetPanelId) {
      console.log(`Moving panel ${draggedPanel} to position of ${targetPanelId}`);
      // Panel reordering logic would go here
    }
  };

  // Fetch data from API or use mock data
  const fetchDashboardData = async () => {
    try {
      // setLoading(true);
      
      // Always try to fetch GMX prices (fallback is built into the service)
      const prices = await apiService.getGMXPrices();
      setGmxPrices(prices);
      
      // Try to fetch dashboard data regardless of health check
      try {
        const dashData = await apiService.getDashboardData();
        setDashboardData(dashData);
        setApiConnected(true);
        console.log('Dashboard data loaded successfully');
      } catch (dashError) {
        console.warn('Dashboard API not available, using mock data:', dashError);
        setDashboardData(getMockDashboardData());
        setApiConnected(false);
      }
      
      // For now, keep using mock data for positions and trades until we align the types
      setPositions(mockPositions);
      setTrades(mockTrades);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      // Fallback to mock data on error
      setDashboardData(getMockDashboardData());
      setPositions(mockPositions);
      setTrades(mockTrades);
      setApiConnected(false);
    } finally {
      // setLoading(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      if (apiConnected) {
        fetchDashboardData();
      } else {
        // Update mock bot status for demo
        setBotStatus(prev => ({
          ...prev,
          signalsToday: prev.signalsToday + Math.floor(Math.random() * 2),
          executedToday: prev.executedToday + Math.floor(Math.random() * 1.5),
          avgExecutionTime: Math.floor(120 + Math.random() * 60) + 'ms',
          successRate: Math.max(90, Math.min(98, prev.successRate + (Math.random() - 0.5) * 2))
        }));
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [apiConnected]);

  return (
    <div className="p-2 space-y-1">
      {/* Live Alert Banner */}
      <LiveAlertBanner />

      {/* Bot Status Bar - Primary Focus */}
      <div 
        className="bg-gradient-to-r from-blue-900 to-blue-800 border-blue-700 relative group hover:border-blue-500 transition-colors rounded-lg border"
        draggable={true}
        onDragStart={(e) => handleDragStart(e, 'bot-status')}
        onDragEnd={handleDragEnd}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDrop(e, 'bot-status')}
      >
        <Card className="bg-transparent border-0">
        <CardContent className="p-4">
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-70 transition-opacity cursor-move text-blue-300" title="Drag to reposition" draggable={false}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <circle cx="3" cy="3" r="1"/>
              <circle cx="8" cy="3" r="1"/>
              <circle cx="13" cy="3" r="1"/>
              <circle cx="3" cy="8" r="1"/>
              <circle cx="8" cy="8" r="1"/>
              <circle cx="13" cy="8" r="1"/>
              <circle cx="3" cy="13" r="1"/>
              <circle cx="8" cy="13" r="1"/>
              <circle cx="13" cy="13" r="1"/>
            </svg>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full animate-pulse ${
                  botStatus.status === 'ACTIVE' ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
                <span className="text-white font-semibold text-lg">WolfHunt Bot</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  (dashboardData?.trading_enabled || botStatus.status === 'ACTIVE') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>{dashboardData?.trading_enabled ? 'ACTIVE' : botStatus.status}</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  apiConnected ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'
                }`}>{apiConnected ? 'API' : 'DEMO'}</span>
              </div>
              <div className="text-sm text-blue-200">
                Uptime: <span className="text-white font-medium">{botStatus.uptime}</span>
              </div>
              <div className="text-sm text-blue-200">
                Last Signal: <span className="text-white font-medium">{botStatus.lastSignal}</span>
              </div>
            </div>
            <div className="flex items-center space-x-6 text-sm">
              <div className="text-center">
                <div className="text-white font-bold text-lg">{dashboardData?.total_trades || botStatus.signalsToday}</div>
                <div className="text-blue-200">{apiConnected ? 'Total Trades' : 'Signals Today'}</div>
              </div>
              <div className="text-center">
                <div className="text-white font-bold text-lg">{dashboardData?.open_positions || botStatus.executedToday}</div>
                <div className="text-blue-200">{apiConnected ? 'Open Positions' : 'Executed'}</div>
              </div>
              <div className="text-center">
                <div className="text-white font-bold text-lg">{dashboardData?.win_rate?.toFixed(1) || botStatus.successRate.toFixed(1)}%</div>
                <div className="text-blue-200">{apiConnected ? 'Win Rate' : 'Success Rate'}</div>
              </div>
            </div>
          </div>
        </CardContent>
        </Card>
      </div>

      {/* 🐺 WOLF PACK INTELLIGENCE SECTION */}
      <WolfPackDashboard />

      {/* Portfolio Performance Stats */}
      <PortfolioStats stats={getPortfolioStats(dashboardData)} />

      {/* Main Trading Interface - Optimized Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-2">
        {/* Primary Chart - BTC-USD */}
        <div className="xl:col-span-2">
          <TradingChart
            symbol={selectedAsset}
            data={mockChartData[selectedAsset as keyof typeof mockChartData] || mockChartData['BTC-USD']}
            currentPrice={gmxPrices[selectedAsset]?.price || (selectedAsset === 'BTC-USD' ? 45750 : selectedAsset === 'ETH-USD' ? 2895 : 15.75)}
            priceChange={gmxPrices[selectedAsset]?.change24h || (selectedAsset === 'BTC-USD' ? 1.67 : selectedAsset === 'ETH-USD' ? 1.58 : 3.61)}
            priceChangePercent={gmxPrices[selectedAsset]?.change24h || (selectedAsset === 'BTC-USD' ? 1.67 : selectedAsset === 'ETH-USD' ? 1.58 : 3.61)}
          />
        </div>

        {/* Asset Selector & Mini Charts */}
        <div className="xl:col-span-1 space-y-2">
          {/* Asset Selection */}
          <Card 
            className="relative group hover:border-green-400 transition-colors"
            draggable={true}
            onDragStart={(e) => handleDragStart(e, 'asset-selector')}
            onDragEnd={handleDragEnd}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, 'asset-selector')}
          >
            <CardHeader className="pb-2">
              <h3 className="text-lg font-semibold text-white">GMX Perpetuals</h3>
            </CardHeader>
            <CardContent className="space-y-3">
              {['BTC-USD', 'ETH-USD', 'LINK-USD'].map((symbol) => {
                const priceData = gmxPrices[symbol];
                const price = priceData?.price || (symbol === 'BTC-USD' ? 45750 : symbol === 'ETH-USD' ? 2895 : 15.75);
                const change = priceData?.change24h || (symbol === 'BTC-USD' ? 1.67 : symbol === 'ETH-USD' ? 1.58 : 3.61);
                const changeAbs = Math.abs(change * price / 100); // Calculate absolute change from percentage
                return (
                  <div 
                    key={symbol}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedAsset === symbol 
                        ? 'bg-blue-600 border border-blue-500' 
                        : 'bg-gray-800 hover:bg-gray-700 border border-gray-700'
                    }`}
                    onClick={() => setSelectedAsset(symbol)}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium text-white">{symbol}</div>
                        <div className="text-2xl font-bold text-white">
                          ${symbol === 'LINK-USD' ? price.toFixed(2) : price.toLocaleString()}
                        </div>
                      </div>
                      <div className={`text-right ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        <div className="text-sm font-medium">{change > 0 ? '+' : ''}{changeAbs.toFixed(2)}</div>
                        <div className="text-sm">{change > 0 ? '+' : ''}{change.toFixed(2)}%</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Position Distribution */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Position Exposure</h3>
            </CardHeader>
            <CardContent>
              <div className="h-48 mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={positionDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={30}
                      outerRadius={70}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {positionDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F3F4F6'
                      }}
                      formatter={(value, name, props) => [
                        `${value}% (${props.payload.exposure})`,
                        name
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2">
                {positionDistribution.map((item) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center">
                      <div 
                        className="w-3 h-3 rounded-full mr-2"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-gray-300">{item.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-medium">{item.value}%</div>
                      <div className="text-gray-400 text-xs">{item.exposure}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance Metrics & Bot Stats */}
        <div className="xl:col-span-1 space-y-2">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Performance Today</h3>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">+$2,156</div>
                <div className="text-sm text-gray-400">Daily P&L</div>
                <div className="text-xs text-green-400">+2.34%</div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="text-center p-2 bg-gray-800 rounded">
                  <div className="text-lg font-semibold text-white">{botStatus.executedToday}</div>
                  <div className="text-gray-400">Trades</div>
                </div>
                <div className="text-center p-2 bg-gray-800 rounded">
                  <div className="text-lg font-semibold text-white">1</div>
                  <div className="text-gray-400">Open</div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Execution Speed</span>
                  <span className="text-white font-medium">{botStatus.avgExecutionTime}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Win Rate</span>
                  <span className="text-green-400 font-medium">68.5%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Max Drawdown</span>
                  <span className="text-red-400 font-medium">-1.2%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Strategy Status</h3>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-2 bg-gray-800 rounded">
                <span className="text-gray-300">EMA Crossover</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">ACTIVE</span>
              </div>
              <div className="text-sm space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-400">Fast EMA (12)</span>
                  <span className="text-blue-400">45,580</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Slow EMA (26)</span>
                  <span className="text-red-400">45,400</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Signal</span>
                  <span className="text-green-400 font-medium">BULLISH</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Compact Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
        <Card 
          className="relative group hover:border-blue-400 transition-colors"
          draggable={true}
          onDragStart={(e) => handleDragStart(e, 'volume-chart')}
          onDragEnd={handleDragEnd}
          onDragOver={handleDragOver}
          onDrop={(e) => handleDrop(e, 'volume-chart')}
        >
          <CardHeader className="relative">
            <h3 className="text-lg font-semibold text-white">Daily Trading Volume</h3>
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-70 transition-opacity cursor-move text-gray-400" title="Drag to reposition" draggable={false}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <circle cx="3" cy="3" r="1"/>
                <circle cx="8" cy="3" r="1"/>
                <circle cx="13" cy="3" r="1"/>
                <circle cx="3" cy="8" r="1"/>
                <circle cx="8" cy="8" r="1"/>
                <circle cx="13" cy="8" r="1"/>
                <circle cx="3" cy="13" r="1"/>
                <circle cx="8" cy="13" r="1"/>
                <circle cx="13" cy="13" r="1"/>
              </svg>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={volumeData}>
                  <XAxis 
                    dataKey="time" 
                    stroke="#9CA3AF"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
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
                  />
                  <Bar dataKey="volume" fill="#3B82F6" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Strategy Performance */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">Strategy Performance</h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 h-40">
              <div className="flex flex-col justify-center items-center">
                <div className="relative w-24 h-24">
                  <div className="w-24 h-24 rounded-full border-4 border-gray-700"></div>
                  <div className="absolute inset-0 rounded-full border-4 border-green-400 border-r-transparent border-b-transparent transform rotate-45"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-xl font-bold text-white">68.5%</div>
                      <div className="text-xs text-gray-400">Win Rate</div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Trades</span>
                  <span className="text-white font-medium">847</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Profitable</span>
                  <span className="text-green-400 font-medium">580</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Losses</span>
                  <span className="text-red-400 font-medium">267</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg. Profit</span>
                  <span className="text-green-400 font-medium">+$45.20</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg. Loss</span>
                  <span className="text-red-400 font-medium">-$28.50</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Combined Positions & Activity Feed */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-2">
        {/* Current Positions - Compact */}
        <div className="xl:col-span-1">
          <PositionsTable 
            positions={positions}
            onClosePosition={async (id) => {
              try {
                if (apiConnected) {
                  await apiService.closePosition(id);
                  fetchDashboardData(); // Refresh data
                } else {
                  console.log('Demo mode - would close position:', id);
                }
              } catch (error) {
                console.error('Error closing position:', error);
              }
            }}
          />
        </div>

        {/* Bot Activity Feed */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">Live Bot Activity</h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-400 mb-2">Recent Trades</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {trades.slice(0, 4).map((trade) => (
                    <div key={trade.id} className="flex items-center justify-between p-2 bg-gray-800 rounded text-sm">
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${
                          trade.side === 'BUY' ? 'bg-green-400' : 'bg-red-400'
                        }`}></div>
                        <div>
                          <div className="text-white font-medium">{trade.side} {trade.symbol}</div>
                          <div className="text-gray-400 text-xs">{trade.size} @ ${trade.price.toLocaleString()}</div>
                        </div>
                      </div>
                      <div className={`text-right ${
                        (trade.realizedPnl || 0) > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        <div className="font-medium">
                          {(trade.realizedPnl || 0) > 0 ? '+' : ''}${(trade.realizedPnl || 0).toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(trade.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-400 mb-2">Signal & System Events</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  <div className="flex items-start space-x-2 p-2 bg-gray-800 rounded text-sm">
                    <div className="w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <div className="text-white font-medium">Position Opened</div>
                      <div className="text-gray-400">LONG LINK-USD @ $15.50 (3.0x leverage)</div>
                      <div className="text-xs text-gray-500">45 min ago</div>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-2 p-2 bg-gray-800 rounded text-sm">
                    <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <div className="text-white font-medium">EMA Signal</div>
                      <div className="text-gray-400">Bullish crossover detected BTC-USD</div>
                      <div className="text-xs text-gray-500">1h ago</div>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-2 p-2 bg-gray-800 rounded text-sm">
                    <div className="w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <div className="text-white font-medium">Trade Executed</div>
                      <div className="text-gray-400">SELL BTC-USD @ $45,500 (+$4.55)</div>
                      <div className="text-xs text-gray-500">3h ago</div>
                    </div>
                  </div>

                  <div className="flex items-start space-x-2 p-2 bg-gray-800 rounded text-sm">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <div className="text-white font-medium">Risk Check</div>
                      <div className="text-gray-400">Portfolio risk within limits (1.2%)</div>
                      <div className="text-xs text-gray-500">4h ago</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}