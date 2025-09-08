import { Card, CardContent } from '../ui/Card';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid';
import { cn } from '../../utils/cn';

interface StatItem {
  label: string;
  value: string | number;
  change?: number;
  changeType?: 'percentage' | 'currency';
  color?: 'green' | 'red' | 'blue' | 'gray';
}

interface PortfolioStatsProps {
  stats: StatItem[];
}

export function PortfolioStats({ stats }: PortfolioStatsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4 mb-6">
      {stats.map((stat, index) => (
        <StatCard key={index} stat={stat} />
      ))}
    </div>
  );
}

function StatCard({ stat }: { stat: StatItem }) {
  const getColorClasses = (color?: string, isChange = false) => {
    if (isChange) {
      return {
        green: 'text-green-400',
        red: 'text-red-400',
        blue: 'text-blue-400',
        gray: 'text-gray-400'
      }[color || 'gray'];
    }

    return {
      green: 'text-green-400 border-green-400/20 bg-green-400/5',
      red: 'text-red-400 border-red-400/20 bg-red-400/5',
      blue: 'text-blue-400 border-blue-400/20 bg-blue-400/5',
      gray: 'text-gray-300 border-gray-600'
    }[color || 'gray'];
  };

  const formatValue = (value: string | number) => {
    if (typeof value === 'number') {
      if (value >= 1000000) {
        return `${(value / 1000000).toFixed(2)}M`;
      }
      if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
      }
      return value.toFixed(2);
    }
    return value;
  };

  const formatChange = (change: number, type?: string) => {
    const prefix = change > 0 ? '+' : '';
    if (type === 'percentage') {
      return `${prefix}${change.toFixed(2)}%`;
    }
    return `${prefix}$${Math.abs(change).toFixed(2)}`;
  };

  return (
    <Card className={cn(
      'border transition-all duration-200 hover:border-opacity-60',
      getColorClasses(stat.color)
    )} padding="sm">
      <CardContent>
        <div className="text-xs text-gray-400 mb-1 uppercase tracking-wider">
          {stat.label}
        </div>
        <div className="text-xl font-bold text-white mb-1">
          {formatValue(stat.value)}
        </div>
        {stat.change !== undefined && (
          <div className={cn(
            'flex items-center text-sm font-medium',
            getColorClasses(stat.change > 0 ? 'green' : 'red', true)
          )}>
            {stat.change > 0 ? (
              <ArrowUpIcon className="w-3 h-3 mr-1" />
            ) : (
              <ArrowDownIcon className="w-3 h-3 mr-1" />
            )}
            {formatChange(stat.change, stat.changeType)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}