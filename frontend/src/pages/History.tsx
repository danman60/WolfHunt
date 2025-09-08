import { useState } from 'react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, BarChart, Bar } from 'recharts';

interface TradeHistory {
  id: number;
  timestamp: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT';
  size: number;
  price: number;
  value: number;
  pnl: number;
  commission: number;
  strategy: string;
  status: 'FILLED' | 'PARTIAL' | 'CANCELLED';
}

interface DateFilter {
  period: '1D' | '7D' | '30D' | '90D' | 'ALL';
  startDate?: string;
  endDate?: string;
}

const mockTradeHistory: TradeHistory[] = [
  {
    id: 1,
    timestamp: '2024-01-15T14:32:15Z',
    symbol: 'BTC-USD',
    side: 'BUY',
    type: 'MARKET',
    size: 0.001,
    price: 45000,
    value: 45,
    pnl: 0,
    commission: 0.045,
    strategy: 'EMA Crossover',
    status: 'FILLED'
  },
  {
    id: 2,
    timestamp: '2024-01-15T15:45:22Z',
    symbol: 'BTC-USD',
    side: 'SELL',
    type: 'LIMIT',
    size: 0.001,
    price: 45500,
    value: 45.5,
    pnl: 4.55,
    commission: 0.045,
    strategy: 'EMA Crossover',
    status: 'FILLED'
  },
  {
    id: 3,
    timestamp: '2024-01-15T16:20:10Z',
    symbol: 'ETH-USD',
    side: 'BUY',
    type: 'MARKET',
    size: 0.01,
    price: 2850,
    value: 28.5,
    pnl: 0,
    commission: 0.029,
    strategy: 'Manual',
    status: 'FILLED'
  },
  {
    id: 4,
    timestamp: '2024-01-15T17:12:33Z',
    symbol: 'LINK-USD',
    side: 'BUY',
    type: 'MARKET',
    size: 10,
    price: 15.50,
    value: 155,
    pnl: 0,
    commission: 0.155,
    strategy: 'EMA Crossover',
    status: 'FILLED'
  },
  {
    id: 5,
    timestamp: '2024-01-15T18:05:44Z',
    symbol: 'ETH-USD',
    side: 'SELL',
    type: 'LIMIT',
    size: 0.01,
    price: 2890,
    value: 28.9,
    pnl: 0.37,
    commission: 0.029,
    strategy: 'Manual',
    status: 'FILLED'
  },
];

const performanceData = [
  { date: '2024-01-10', pnl: -12.5, cumPnl: -12.5 },
  { date: '2024-01-11', pnl: 34.2, cumPnl: 21.7 },
  { date: '2024-01-12', pnl: -8.1, cumPnl: 13.6 },
  { date: '2024-01-13', pnl: 45.8, cumPnl: 59.4 },
  { date: '2024-01-14', pnl: 23.1, cumPnl: 82.5 },
  { date: '2024-01-15', pnl: 15.3, cumPnl: 97.8 },
];

const dailyStats = [
  { date: '2024-01-10', trades: 8, volume: 1250 },
  { date: '2024-01-11', trades: 12, volume: 2100 },
  { date: '2024-01-12', trades: 6, volume: 950 },
  { date: '2024-01-13', trades: 15, volume: 3200 },
  { date: '2024-01-14', trades: 10, volume: 1800 },
  { date: '2024-01-15', trades: 5, volume: 850 },
];

export function History() {
  const [filter, setFilter] = useState<DateFilter>({ period: '30D' });
  const [selectedSymbol, setSelectedSymbol] = useState<string>('ALL');

  const symbols = ['ALL', ...Array.from(new Set(mockTradeHistory.map(t => t.symbol)))];

  const filteredTrades = mockTradeHistory.filter(trade => {
    if (selectedSymbol !== 'ALL' && trade.symbol !== selectedSymbol) return false;
    // Add date filtering logic here
    return true;
  });

  const totalPnL = filteredTrades.reduce((sum, trade) => sum + trade.pnl, 0);
  const totalCommission = filteredTrades.reduce((sum, trade) => sum + trade.commission, 0);
  const totalVolume = filteredTrades.reduce((sum, trade) => sum + trade.value, 0);
  const winRate = (filteredTrades.filter(t => t.pnl > 0).length / filteredTrades.length) * 100;

  return (
    <div className="p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Trading History</h1>
          <p className="text-gray-400">View your trading performance and history</p>
        </div>
        
        {/* Filters */}
        <div className="flex items-center space-x-3">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm"
          >
            {symbols.map(symbol => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>
          
          <div className="flex bg-gray-800 rounded-lg p-1">
            {(['1D', '7D', '30D', '90D', 'ALL'] as const).map((period) => (
              <button
                key={period}
                onClick={() => setFilter({ period })}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  filter.period === period
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {period}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
              </div>
              <div className="text-sm text-gray-400">Total P&L</div>
              <div className={`text-xs ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {((totalPnL / totalVolume) * 100).toFixed(2)}% Return
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{filteredTrades.length}</div>
              <div className="text-sm text-gray-400">Total Trades</div>
              <div className="text-xs text-green-400">
                {filteredTrades.filter(t => t.pnl > 0).length} Winners
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{winRate.toFixed(1)}%</div>
              <div className="text-sm text-gray-400">Win Rate</div>
              <div className="text-xs text-gray-400">
                Avg Win: ${(filteredTrades.filter(t => t.pnl > 0).reduce((s, t) => s + t.pnl, 0) / filteredTrades.filter(t => t.pnl > 0).length || 0).toFixed(2)}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">${totalVolume.toFixed(0)}</div>
              <div className="text-sm text-gray-400">Total Volume</div>
              <div className="text-xs text-red-400">
                -${totalCommission.toFixed(2)} Fees
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">Cumulative P&L</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performanceData}>
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
                    formatter={(value: number) => [`$${value.toFixed(2)}`, 'Cumulative P&L']}
                    labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="cumPnl" 
                    stroke="#10B981" 
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">Daily Trading Volume</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dailyStats}>
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
                      name === 'volume' ? `$${value}` : value,
                      name === 'volume' ? 'Volume' : 'Trades'
                    ]}
                    labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <Bar dataKey="volume" fill="#3B82F6" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trade History Table */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-white">Recent Trades</h3>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left p-3 text-gray-400">Time</th>
                  <th className="text-left p-3 text-gray-400">Symbol</th>
                  <th className="text-left p-3 text-gray-400">Side</th>
                  <th className="text-left p-3 text-gray-400">Type</th>
                  <th className="text-left p-3 text-gray-400">Size</th>
                  <th className="text-left p-3 text-gray-400">Price</th>
                  <th className="text-left p-3 text-gray-400">Value</th>
                  <th className="text-left p-3 text-gray-400">P&L</th>
                  <th className="text-left p-3 text-gray-400">Commission</th>
                  <th className="text-left p-3 text-gray-400">Strategy</th>
                  <th className="text-left p-3 text-gray-400">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrades.map((trade) => (
                  <tr key={trade.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                    <td className="p-3 text-gray-300">
                      {new Date(trade.timestamp).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="p-3 text-white font-medium">{trade.symbol}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        trade.side === 'BUY' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {trade.side}
                      </span>
                    </td>
                    <td className="p-3 text-gray-300">{trade.type}</td>
                    <td className="p-3 text-white">{trade.size}</td>
                    <td className="p-3 text-white">${trade.price.toLocaleString()}</td>
                    <td className="p-3 text-white">${trade.value.toFixed(2)}</td>
                    <td className={`p-3 font-medium ${
                      trade.pnl > 0 ? 'text-green-400' : trade.pnl < 0 ? 'text-red-400' : 'text-gray-400'
                    }`}>
                      {trade.pnl > 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                    </td>
                    <td className="p-3 text-gray-400">${trade.commission.toFixed(3)}</td>
                    <td className="p-3 text-gray-300">{trade.strategy}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        trade.status === 'FILLED'
                          ? 'bg-green-100 text-green-800'
                          : trade.status === 'PARTIAL'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {trade.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}