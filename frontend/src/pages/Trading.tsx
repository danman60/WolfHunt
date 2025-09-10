import { useState } from 'react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { TradingChart } from '../components/dashboard/TradingChart';
import { PositionsTable } from '../components/dashboard/PositionsTable';

interface OrderFormData {
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT';
  size: string;
  price: string;
  leverage: string;
}

const dydxAssets = [
  { symbol: 'BTC-USD', price: 45750, change: 1.67, changeAbs: 750, volume: '2.4M' },
  { symbol: 'ETH-USD', price: 2895, change: 1.58, changeAbs: 45, volume: '8.1M' },
  { symbol: 'LINK-USD', price: 15.75, change: 3.61, changeAbs: 0.55, volume: '124K' }
];

const mockPositions = [
  {
    id: 1,
    symbol: 'LINK-USD',
    side: 'LONG' as const,
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

const mockChartData = [
  { time: '09:00', price: 45000, ema12: 44980, ema26: 44920, volume: 1250 },
  { time: '09:15', price: 45200, ema12: 45050, ema26: 44980, volume: 980 },
  { time: '09:30', price: 45400, ema12: 45180, ema26: 45080, volume: 1450 },
  { time: '09:45', price: 45300, ema12: 45250, ema26: 45150, volume: 1100 },
  { time: '10:00', price: 45500, ema12: 45350, ema26: 45220, volume: 1680 },
  { time: '10:15', price: 45600, ema12: 45450, ema26: 45300, volume: 920 },
  { time: '10:30', price: 45750, ema12: 45580, ema26: 45400, volume: 1380 }
];

export function Trading() {
  const [selectedAsset, setSelectedAsset] = useState('BTC-USD');
  const [orderForm, setOrderForm] = useState<OrderFormData>({
    symbol: 'BTC-USD',
    side: 'BUY',
    type: 'MARKET',
    size: '',
    price: '',
    leverage: '3'
  });

  const selectedAssetData = dydxAssets.find(asset => asset.symbol === selectedAsset);

  const handleOrderSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Order submitted:', orderForm);
    // In real app, this would submit to your trading API
  };

  return (
    <div className="p-3 space-y-3">
      {/* Trading Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Trading Bot Configuration</h1>
          <p className="text-gray-400">Configure and monitor your GMX trading bot</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
            Bot: PAUSED
          </div>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">
            Resume Bot
          </button>
        </div>
      </div>

      {/* Asset Selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {dydxAssets.map((asset) => (
          <Card 
            key={asset.symbol}
            className={`cursor-pointer transition-colors ${
              selectedAsset === asset.symbol 
                ? 'border-blue-500 bg-blue-900/20' 
                : 'hover:border-gray-600'
            }`}
            onClick={() => {
              setSelectedAsset(asset.symbol);
              setOrderForm(prev => ({ ...prev, symbol: asset.symbol }));
            }}
          >
            <CardContent className="p-4">
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-medium text-white text-lg">{asset.symbol}</div>
                  <div className="text-2xl font-bold text-white">
                    ${asset.symbol === 'LINK-USD' ? asset.price.toFixed(2) : asset.price.toLocaleString()}
                  </div>
                </div>
                <div className={`text-right ${asset.change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  <div className="text-lg font-semibold">+{asset.changeAbs}</div>
                  <div className="text-sm">+{asset.change}%</div>
                  <div className="text-xs text-gray-400 mt-1">{asset.volume}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Trading Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Trading Chart */}
        <div className="lg:col-span-2">
          <TradingChart
            symbol={selectedAsset}
            data={mockChartData}
            currentPrice={selectedAssetData?.price || 45750}
            priceChange={selectedAssetData?.changeAbs || 750}
            priceChangePercent={selectedAssetData?.change || 1.67}
          />
        </div>

        {/* Order Entry */}
        <div className="space-y-3">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Place Order</h3>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleOrderSubmit} className="space-y-4">
                {/* Buy/Sell Tabs */}
                <div className="grid grid-cols-2 gap-1 p-1 bg-gray-800 rounded-lg">
                  <button
                    type="button"
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      orderForm.side === 'BUY'
                        ? 'bg-green-600 text-white'
                        : 'text-gray-400 hover:text-white'
                    }`}
                    onClick={() => setOrderForm(prev => ({ ...prev, side: 'BUY' }))}
                  >
                    BUY
                  </button>
                  <button
                    type="button"
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      orderForm.side === 'SELL'
                        ? 'bg-red-600 text-white'
                        : 'text-gray-400 hover:text-white'
                    }`}
                    onClick={() => setOrderForm(prev => ({ ...prev, side: 'SELL' }))}
                  >
                    SELL
                  </button>
                </div>

                {/* Order Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Order Type
                  </label>
                  <select
                    value={orderForm.type}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, type: e.target.value as 'MARKET' | 'LIMIT' }))}
                    className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                  >
                    <option value="MARKET">Market</option>
                    <option value="LIMIT">Limit</option>
                  </select>
                </div>

                {/* Size */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Size
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    placeholder="0.001"
                    value={orderForm.size}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, size: e.target.value }))}
                    className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                  />
                </div>

                {/* Price (only for limit orders) */}
                {orderForm.type === 'LIMIT' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Price
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder={selectedAssetData?.price.toString() || "45750"}
                      value={orderForm.price}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, price: e.target.value }))}
                      className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                    />
                  </div>
                )}

                {/* Leverage */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Leverage
                  </label>
                  <select
                    value={orderForm.leverage}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, leverage: e.target.value }))}
                    className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                  >
                    <option value="1">1x</option>
                    <option value="2">2x</option>
                    <option value="3">3x</option>
                    <option value="5">5x</option>
                    <option value="10">10x</option>
                  </select>
                </div>

                {/* Order Summary */}
                <div className="p-3 bg-gray-800 rounded-lg text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Est. Size:</span>
                    <span className="text-white">{orderForm.size || '0'} {selectedAsset.split('-')[0]}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Est. Value:</span>
                    <span className="text-white">
                      ${orderForm.size ? (parseFloat(orderForm.size) * (selectedAssetData?.price || 0)).toFixed(2) : '0.00'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Margin Required:</span>
                    <span className="text-white">
                      ${orderForm.size && orderForm.leverage 
                        ? ((parseFloat(orderForm.size) * (selectedAssetData?.price || 0)) / parseFloat(orderForm.leverage)).toFixed(2) 
                        : '0.00'}
                    </span>
                  </div>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  className={`w-full py-3 rounded-lg text-white font-medium transition-colors ${
                    orderForm.side === 'BUY'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                  disabled={!orderForm.size}
                >
                  {orderForm.side} {selectedAsset}
                </button>
              </form>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Quick Actions</h3>
            </CardHeader>
            <CardContent className="space-y-2">
              <button className="w-full py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors">
                Close All Positions
              </button>
              <button className="w-full py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium transition-colors">
                Cancel All Orders
              </button>
              <button className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">
                Set Stop Loss
              </button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Current Positions */}
      <PositionsTable 
        positions={mockPositions}
        onClosePosition={(id) => console.log('Close position:', id)}
        compact={false}
      />
    </div>
  );
}