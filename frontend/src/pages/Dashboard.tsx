import { useState, useEffect } from 'react';
import { PortfolioStats } from '../components/dashboard/PortfolioStats';
import { TradingChart } from '../components/dashboard/TradingChart';
import { PositionsTable, Position } from '../components/dashboard/PositionsTable';
import { TradesTable, Trade } from '../components/dashboard/TradesTable';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

// Mock data - In real app, this would come from your API/WebSocket connections
const mockPortfolioStats = [
  { label: 'Balance', value: '$99,843', change: 2.34, changeType: 'percentage' as const, color: 'blue' as const },
  { label: 'Invested', value: '$0', color: 'gray' as const },
  { label: 'Available Cash', value: '$99,343', color: 'green' as const },
  { label: 'Total Bonus', value: '$500', color: 'blue' as const },
  { label: 'Traded Bonus', value: '$1,145', change: 5.2, changeType: 'percentage' as const, color: 'green' as const },
  { label: 'Pending Bonus', value: '$43,855', color: 'gray' as const }
];

const mockChartData = [
  { time: '09:00', price: 45000, ema12: 44980, ema26: 44920 },
  { time: '09:15', price: 45200, ema12: 45050, ema26: 44980 },
  { time: '09:30', price: 45400, ema12: 45180, ema26: 45080 },
  { time: '09:45', price: 45300, ema12: 45250, ema26: 45150 },
  { time: '10:00', price: 45500, ema12: 45350, ema26: 45220 },
  { time: '10:15', price: 45600, ema12: 45450, ema26: 45300 },
  { time: '10:30', price: 45750, ema12: 45580, ema26: 45400 }
];

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

const assetDistribution = [
  { name: 'EUR/USD', value: 70.6, color: '#3B82F6' },
  { name: 'EUR/GBP', value: 17.6, color: '#10B981' },
  { name: 'GBP/JPY', value: 5.9, color: '#F59E0B' },
  { name: 'Gold', value: 2.9, color: '#EF4444' },
  { name: 'Banknotes', value: 2.9, color: '#8B5CF6' }
];

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

export function Dashboard() {
  const [selectedAsset] = useState('BTC-USD');
  const [totalVolume, setTotalVolume] = useState(5645);
  const [tradeCount, setTradeCount] = useState(34);
  const [avgVolume, setAverageVolume] = useState(166.03);

  // Mock real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate some data updates
      setTotalVolume(prev => prev + Math.random() * 10 - 5);
      setTradeCount(prev => prev + Math.floor(Math.random() * 2));
      setAverageVolume(prev => prev + Math.random() * 2 - 1);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 space-y-6">
      {/* Portfolio Stats */}
      <PortfolioStats stats={mockPortfolioStats} />

      {/* Main Chart and Asset Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trading Chart - Takes 2/3 width */}
        <div className="lg:col-span-2">
          <TradingChart
            symbol={selectedAsset}
            data={mockChartData}
            currentPrice={45750}
            priceChange={750}
            priceChangePercent={1.67}
          />
        </div>

        {/* Asset Distribution - Takes 1/3 width */}
        <div className="space-y-6">
          {/* Top Traded Assets Pie Chart */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Top Traded Assets</h3>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={assetDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {assetDistribution.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F3F4F6'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              {/* Legend */}
              <div className="space-y-2 mt-4">
                {assetDistribution.map((item, index) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center">
                      <div 
                        className="w-3 h-3 rounded-full mr-2"
                        style={{ backgroundColor: COLORS[index] }}
                      />
                      <span className="text-gray-300">{item.name}</span>
                    </div>
                    <span className="text-white font-medium">{item.value}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Trading Volume */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Trading Metrics</h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">
                    ${totalVolume.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-400">Total Traded Volume</div>
                </div>
                
                <div className="flex justify-between text-sm">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-white">{tradeCount}</div>
                    <div className="text-gray-400">Trades</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-white">0</div>
                    <div className="text-gray-400">Open</div>
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="text-lg font-semibold text-white">
                    ${avgVolume.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-400">Average Volume</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Volume Per Day Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">Volume Per Day</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={volumeData}>
                  <XAxis 
                    dataKey="time" 
                    stroke="#9CA3AF"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis 
                    stroke="#9CA3AF"
                    fontSize={12}
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
                  <Bar dataKey="volume" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* High/Low Ratio Donut Chart */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">High/Low Ratio</h3>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-64">
              <div className="relative">
                <div className="w-32 h-32 rounded-full border-8 border-green-400 border-r-red-400 animate-spin-slow"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">72%</div>
                    <div className="text-xs text-gray-400">High Ratio</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-center space-x-6 mt-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-400 rounded-full mr-2"></div>
                <span className="text-sm text-gray-400">High</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-400 rounded-full mr-2"></div>
                <span className="text-sm text-gray-400">Low</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Positions and Recent Updates */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PositionsTable 
          positions={mockPositions}
          onClosePosition={(id) => console.log('Close position:', id)}
        />

        {/* Recent Updates */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">Recent Updates</h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3 text-sm">
                <div className="w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                <div>
                  <div className="text-white font-medium">Position Opened</div>
                  <div className="text-gray-400">Long LINK-USD position opened at $15.50</div>
                  <div className="text-xs text-gray-500 mt-1">45 minutes ago</div>
                </div>
              </div>
              
              <div className="flex items-start space-x-3 text-sm">
                <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                <div>
                  <div className="text-white font-medium">Signal Generated</div>
                  <div className="text-gray-400">EMA crossover signal detected for BTC-USD</div>
                  <div className="text-xs text-gray-500 mt-1">1 hour ago</div>
                </div>
              </div>
              
              <div className="flex items-start space-x-3 text-sm">
                <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2 flex-shrink-0"></div>
                <div>
                  <div className="text-white font-medium">Risk Alert</div>
                  <div className="text-gray-400">Portfolio correlation above 80% threshold</div>
                  <div className="text-xs text-gray-500 mt-1">2 hours ago</div>
                </div>
              </div>
              
              <div className="flex items-start space-x-3 text-sm">
                <div className="w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                <div>
                  <div className="text-white font-medium">Trade Executed</div>
                  <div className="text-gray-400">Sold 0.001 BTC at $45,500 (+$4.55 profit)</div>
                  <div className="text-xs text-gray-500 mt-1">3 hours ago</div>
                </div>
              </div>
              
              <div className="text-center">
                <button className="text-blue-400 hover:text-blue-300 text-sm transition-colors">
                  Load More Updates
                </button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Trades */}
      <TradesTable 
        trades={mockTrades}
        onShowAll={() => console.log('Show all trades')}
      />
    </div>
  );
}