import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { cn } from '../../utils/cn';

interface ChartData {
  time: string;
  price: number;
  ema12?: number;
  ema26?: number;
  volume?: number;
}

interface TradingChartProps {
  symbol: string;
  data: ChartData[];
  currentPrice: number;
  priceChange: number;
  priceChangePercent: number;
}

const timeframes = ['1M', '5M', '15M', '1H', '4H', '1D'];

export function TradingChart({ 
  symbol, 
  data, 
  currentPrice, 
  priceChange, 
  priceChangePercent 
}: TradingChartProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState('5M');
  
  const isPositive = priceChange >= 0;
  
  return (
    <Card className="h-96">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-semibold text-white">{symbol}</h3>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-bold text-white">
                ${currentPrice.toLocaleString()}
              </span>
              <div className={cn(
                'flex items-center text-sm font-medium',
                isPositive ? 'text-green-400' : 'text-red-400'
              )}>
                <span>{isPositive ? '+' : ''}${priceChange.toFixed(2)}</span>
                <span className="ml-1">({isPositive ? '+' : ''}{priceChangePercent.toFixed(2)}%)</span>
              </div>
            </div>
          </div>
          
          {/* Timeframe selector */}
          <div className="flex space-x-1 bg-gray-800 rounded-lg p-1">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => setSelectedTimeframe(tf)}
                className={cn(
                  'px-3 py-1 text-xs font-medium rounded transition-colors',
                  selectedTimeframe === tf
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                )}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
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
                domain={['dataMin - 50', 'dataMax + 50']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }}
                labelStyle={{ color: '#9CA3AF' }}
              />
              
              {/* Price line */}
              <Line
                type="monotone"
                dataKey="price"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#3B82F6' }}
              />
              
              {/* EMA lines */}
              {data[0]?.ema12 && (
                <Line
                  type="monotone"
                  dataKey="ema12"
                  stroke="#10B981"
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="5 5"
                />
              )}
              
              {data[0]?.ema26 && (
                <Line
                  type="monotone"
                  dataKey="ema26"
                  stroke="#F59E0B"
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="5 5"
                />
              )}
              
              {/* Current price reference line */}
              <ReferenceLine 
                y={currentPrice} 
                stroke={isPositive ? '#10B981' : '#EF4444'}
                strokeDasharray="3 3"
                strokeWidth={1}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        {/* Legend */}
        <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
            <span className="text-gray-400">Price</span>
          </div>
          {data[0]?.ema12 && (
            <div className="flex items-center">
              <div className="w-3 h-1 bg-green-500 mr-2"></div>
              <span className="text-gray-400">EMA 12</span>
            </div>
          )}
          {data[0]?.ema26 && (
            <div className="flex items-center">
              <div className="w-3 h-1 bg-yellow-500 mr-2"></div>
              <span className="text-gray-400">EMA 26</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}