import { Card, CardHeader, CardContent } from '../ui/Card';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid';
import { cn } from '../../utils/cn';

export interface Position {
  id: number;
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  markPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
  leverage: number;
  margin: number;
  liquidationPrice?: number;
  openedAt: string;
}

interface PositionsTableProps {
  positions: Position[];
  onClosePosition?: (positionId: number) => void;
  compact?: boolean;
}

export function PositionsTable({ positions, onClosePosition, compact: _compact }: PositionsTableProps) {
  const totalPnl = positions.reduce((sum, pos) => sum + pos.unrealizedPnl, 0);
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Open Positions</h3>
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
              Positions: {positions.length}
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {positions.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            No open positions
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-700">
                <tr className="text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  <th className="px-6 py-3">Symbol</th>
                  <th className="px-6 py-3">Side</th>
                  <th className="px-6 py-3">Size</th>
                  <th className="px-6 py-3">Entry Price</th>
                  <th className="px-6 py-3">Mark Price</th>
                  <th className="px-6 py-3">Unrealized P&L</th>
                  <th className="px-6 py-3">Leverage</th>
                  <th className="px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {positions.map((position) => (
                  <PositionRow 
                    key={position.id} 
                    position={position}
                    onClose={() => onClosePosition?.(position.id)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PositionRow({ position, onClose }: { position: Position; onClose: () => void }) {
  const pnlColor = position.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400';
  const sideColor = position.side === 'LONG' ? 'text-green-400' : 'text-red-400';
  const sideBgColor = position.side === 'LONG' 
    ? 'bg-green-400/10 border-green-400/20' 
    : 'bg-red-400/10 border-red-400/20';

  return (
    <tr className="hover:bg-gray-800/50 transition-colors">
      <td className="px-6 py-4">
        <div className="flex items-center">
          <div className="font-medium text-white">{position.symbol}</div>
        </div>
      </td>
      
      <td className="px-6 py-4">
        <span className={cn(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
          sideBgColor,
          sideColor
        )}>
          {position.side === 'LONG' ? (
            <ArrowUpIcon className="w-3 h-3 mr-1" />
          ) : (
            <ArrowDownIcon className="w-3 h-3 mr-1" />
          )}
          {position.side}
        </span>
      </td>
      
      <td className="px-6 py-4">
        <div className="text-sm text-white font-medium">
          {position.size.toFixed(4)}
        </div>
        <div className="text-xs text-gray-400">
          ${((position.size || 0) * (position.markPrice || 0)).toLocaleString()}
        </div>
      </td>
      
      <td className="px-6 py-4">
        <div className="text-sm text-white font-medium">
          ${(position.entryPrice || 0).toLocaleString()}
        </div>
      </td>
      
      <td className="px-6 py-4">
        <div className="text-sm text-white font-medium">
          ${(position.markPrice || 0).toLocaleString()}
        </div>
        <div className="text-xs text-gray-400">
          {((position.markPrice - position.entryPrice) / position.entryPrice * 100).toFixed(2)}%
        </div>
      </td>
      
      <td className="px-6 py-4">
        <div className={cn('text-sm font-medium', pnlColor)}>
          ${position.unrealizedPnl.toFixed(2)}
        </div>
        <div className={cn('text-xs', pnlColor)}>
          ({position.unrealizedPnlPercent >= 0 ? '+' : ''}{position.unrealizedPnlPercent.toFixed(2)}%)
        </div>
      </td>
      
      <td className="px-6 py-4">
        <div className="flex items-center">
          <span className="text-sm text-white font-medium">
            {position.leverage.toFixed(1)}x
          </span>
          <div className="ml-2 w-8 h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className={cn(
                'h-full transition-all',
                position.leverage > 5 ? 'bg-red-500' : 
                position.leverage > 3 ? 'bg-yellow-500' : 'bg-green-500'
              )}
              style={{ width: `${Math.min(100, (position.leverage / 10) * 100)}%` }}
            />
          </div>
        </div>
        <div className="text-xs text-gray-400">
          Margin: ${position.margin.toFixed(2)}
        </div>
      </td>
      
      <td className="px-6 py-4">
        <div className="flex space-x-2">
          <button
            onClick={onClose}
            className="text-xs bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded transition-colors"
          >
            Close
          </button>
        </div>
      </td>
    </tr>
  );
}