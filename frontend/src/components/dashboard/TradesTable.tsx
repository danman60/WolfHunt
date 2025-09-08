import { Card, CardHeader, CardContent } from '../ui/Card';
import { ArrowUpIcon, ArrowDownIcon, ClockIcon } from '@heroicons/react/24/solid';
import { cn } from '../../utils/cn';
import { format } from 'date-fns';

export interface Trade {
  id: number;
  orderId: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  orderType: 'MARKET' | 'LIMIT' | 'STOP_LIMIT';
  size: number;
  price: number;
  filledSize: number;
  notionalValue: number;
  commission: number;
  realizedPnl?: number;
  status: 'FILLED' | 'PARTIALLY_FILLED' | 'CANCELLED' | 'PENDING';
  strategyName?: string;
  timestamp: string;
}

interface TradesTableProps {
  trades: Trade[];
  showAll?: boolean;
  onShowAll?: () => void;
}

export function TradesTable({ trades, showAll = false, onShowAll }: TradesTableProps) {
  const displayTrades = showAll ? trades : trades.slice(0, 10);
  const totalPnl = trades.reduce((sum, trade) => sum + (trade.realizedPnl || 0), 0);
  const totalVolume = trades.reduce((sum, trade) => sum + trade.notionalValue, 0);
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Recent Trades</h3>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-400">
              Total P&L: 
              <span className={cn(
                'ml-1 font-medium',
                totalPnl >= 0 ? 'text-green-400' : 'text-red-400'
              )}>
                ${totalPnl.toFixed(2)}
              </span>
            </div>
            <div className="text-sm text-gray-400">
              Volume: ${totalVolume.toLocaleString()}
            </div>
            {!showAll && trades.length > 10 && onShowAll && (
              <button
                onClick={onShowAll}
                className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                View All ({trades.length})
              </button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {displayTrades.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            No trades yet
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-700">
                <tr className="text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  <th className="px-6 py-3">Time</th>
                  <th className="px-6 py-3">Symbol</th>
                  <th className="px-6 py-3">Side</th>
                  <th className="px-6 py-3">Size</th>
                  <th className="px-6 py-3">Price</th>
                  <th className="px-6 py-3">Value</th>
                  <th className="px-6 py-3">P&L</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Strategy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {displayTrades.map((trade) => (
                  <TradeRow key={trade.id} trade={trade} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TradeRow({ trade }: { trade: Trade }) {
  const sideColor = trade.side === 'BUY' ? 'text-green-400' : 'text-red-400';
  const sideBgColor = trade.side === 'BUY' 
    ? 'bg-green-400/10 border-green-400/20' 
    : 'bg-red-400/10 border-red-400/20';
  
  const pnlColor = trade.realizedPnl && trade.realizedPnl !== 0
    ? trade.realizedPnl > 0 ? 'text-green-400' : 'text-red-400'
    : 'text-gray-400';
  
  const statusConfig = {
    FILLED: { color: 'text-green-400', bg: 'bg-green-400/10 border-green-400/20' },
    PARTIALLY_FILLED: { color: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/20' },
    CANCELLED: { color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/20' },
    PENDING: { color: 'text-blue-400', bg: 'bg-blue-400/10 border-blue-400/20' }
  };

  return (
    <tr className="hover:bg-gray-800/50 transition-colors">
      <td className="px-6 py-4">
        <div className="flex items-center">
          <ClockIcon className="w-3 h-3 text-gray-400 mr-1" />
          <div className="text-sm text-white">
            {format(new Date(trade.timestamp), 'HH:mm:ss')}
          </div>
        </div>
        <div className="text-xs text-gray-400">
          {format(new Date(trade.timestamp), 'MMM dd')}
        </div>
      </td>
      
      <td className="px-6 py-4">
        <div className="font-medium text-white">{trade.symbol}</div>
        <div className="text-xs text-gray-400">{trade.orderType}</div>
      </td>
      
      <td className="px-6 py-4">
        <span className={cn(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
          sideBgColor,
          sideColor
        )}>
          {trade.side === 'BUY' ? (
            <ArrowUpIcon className="w-3 h-3 mr-1" />
          ) : (
            <ArrowDownIcon className="w-3 h-3 mr-1" />
          )}
          {trade.side}
        </span>
      </td>
      
      <td className="px-6 py-4">
        <div className="text-sm text-white font-medium">
          {trade.size.toFixed(4)}
        </div>
        <div className="text-xs text-gray-400">
          Filled: {trade.filledSize.toFixed(4)}
        </div>
      </td>
      
      <td className="px-6 py-4">
        <div className="text-sm text-white font-medium">
          ${trade.price.toLocaleString()}
        </div>
      </td>
      
      <td className="px-6 py-4">
        <div className="text-sm text-white font-medium">
          ${trade.notionalValue.toLocaleString()}
        </div>
        <div className="text-xs text-gray-400">
          Fee: ${trade.commission.toFixed(2)}
        </div>
      </td>
      
      <td className="px-6 py-4">
        {trade.realizedPnl !== undefined ? (
          <div className={cn('text-sm font-medium', pnlColor)}>
            {trade.realizedPnl > 0 ? '+' : ''}${trade.realizedPnl.toFixed(2)}
          </div>
        ) : (
          <span className="text-gray-500 text-sm">-</span>
        )}
      </td>
      
      <td className="px-6 py-4">
        <span className={cn(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
          statusConfig[trade.status].bg,
          statusConfig[trade.status].color
        )}>
          {trade.status}
        </span>
      </td>
      
      <td className="px-6 py-4">
        <div className="text-sm text-gray-300">
          {trade.strategyName || 'Manual'}
        </div>
      </td>
    </tr>
  );
}