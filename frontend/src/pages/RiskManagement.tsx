import { useState } from 'react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts';
import { apiService } from '../services/api';

interface RiskSettings {
  maxDailyLoss: number;
  maxPositionSize: number;
  maxLeverage: number;
  maxCorrelation: number;
  stopLossPercentage: number;
  takeProfitRatio: number;
  maxDrawdown: number;
  marginUtilizationLimit: number;
}

interface RiskMetric {
  name: string;
  current: number;
  limit: number;
  status: 'safe' | 'warning' | 'danger';
  unit: string;
}

const defaultRiskSettings: RiskSettings = {
  maxDailyLoss: 2.0,
  maxPositionSize: 0.5,
  maxLeverage: 3.0,
  maxCorrelation: 0.8,
  stopLossPercentage: 2.0,
  takeProfitRatio: 1.5,
  maxDrawdown: 5.0,
  marginUtilizationLimit: 80.0
};

const riskMetrics: RiskMetric[] = [
  { name: 'Daily P&L', current: -0.8, limit: -2.0, status: 'safe', unit: '%' },
  { name: 'Position Size', current: 0.3, limit: 0.5, status: 'safe', unit: '%' },
  { name: 'Max Leverage', current: 2.1, limit: 3.0, status: 'safe', unit: 'x' },
  { name: 'Correlation', current: 0.65, limit: 0.8, status: 'warning', unit: '' },
  { name: 'Drawdown', current: 1.2, limit: 5.0, status: 'safe', unit: '%' },
  { name: 'Margin Usage', current: 45.2, limit: 80.0, status: 'safe', unit: '%' }
];

const portfolioRiskData = [
  { name: 'BTC-USD', exposure: 65.0, var: 2.4, color: '#F59E0B' },
  { name: 'ETH-USD', exposure: 25.0, var: 1.8, color: '#3B82F6' },
  { name: 'LINK-USD', exposure: 10.0, var: 0.6, color: '#10B981' }
];

const riskHistory = [
  { date: '2024-01-10', var: 2.1, sharpe: 1.2, maxDD: 1.5 },
  { date: '2024-01-11', var: 2.3, sharpe: 1.4, maxDD: 1.3 },
  { date: '2024-01-12', var: 1.9, sharpe: 1.6, maxDD: 1.1 },
  { date: '2024-01-13', var: 2.5, sharpe: 1.3, maxDD: 1.8 },
  { date: '2024-01-14', var: 2.0, sharpe: 1.5, maxDD: 1.4 },
  { date: '2024-01-15', var: 2.2, sharpe: 1.7, maxDD: 1.2 }
];

export function RiskManagement() {
  const [riskSettings, setRiskSettings] = useState<RiskSettings>(defaultRiskSettings);
  const [emergencyMode, setEmergencyMode] = useState(false);

  const handleSettingChange = (key: keyof RiskSettings, value: number) => {
    setRiskSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleEmergencyStop = async () => {
    setEmergencyMode(true);
    console.log('Emergency stop activated - closing all positions');
    
    try {
      const result = await apiService.emergencyStop('User initiated emergency stop', true);
      console.log('Emergency stop result:', result);
    } catch (error) {
      console.error('Emergency stop failed:', error);
    } finally {
      // Re-enable button after 5 seconds
      setTimeout(() => {
        setEmergencyMode(false);
      }, 5000);
    }
  };

  const handleSaveSettings = async () => {
    console.log('Saving risk settings:', riskSettings);
    
    try {
      // Convert risk settings to strategy config format
      const strategyConfig = {
        max_leverage: riskSettings.maxLeverage,
        stop_loss_pct: riskSettings.stopLossPercentage / 100,
        daily_loss_limit: riskSettings.maxDailyLoss,
        max_position_size_pct: riskSettings.maxPositionSize / 100,
      };
      
      const result = await apiService.updateStrategyConfig(strategyConfig);
      console.log('Settings saved:', result);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'safe': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'danger': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'safe': return 'bg-green-100 text-green-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'danger': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Risk Management</h1>
          <p className="text-gray-400">Monitor and configure risk parameters</p>
        </div>
        
        <div className="flex items-center space-x-3">
          {emergencyMode && (
            <div className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium animate-pulse">
              EMERGENCY MODE ACTIVE
            </div>
          )}
          <button 
            onClick={handleEmergencyStop}
            disabled={emergencyMode}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {emergencyMode ? 'Stopping...' : 'Emergency Stop'}
          </button>
          <button 
            onClick={handleSaveSettings}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>

      {/* Risk Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {riskMetrics.map((metric) => (
          <Card key={metric.name}>
            <CardContent className="p-4">
              <div className="flex justify-between items-center mb-2">
                <div className="text-sm text-gray-400">{metric.name}</div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBg(metric.status)}`}>
                  {metric.status.toUpperCase()}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <div className={`text-xl font-bold ${getStatusColor(metric.status)}`}>
                    {metric.current}{metric.unit}
                  </div>
                  <div className="text-xs text-gray-400">
                    Limit: {metric.limit}{metric.unit}
                  </div>
                </div>
                
                <div className="w-12 h-12 relative">
                  <div className="w-12 h-12 rounded-full border-4 border-gray-700"></div>
                  <div 
                    className={`absolute top-0 left-0 w-12 h-12 rounded-full border-4 border-r-transparent border-b-transparent transform transition-transform ${
                      metric.status === 'safe' ? 'border-green-400' :
                      metric.status === 'warning' ? 'border-yellow-400' : 'border-red-400'
                    }`}
                    style={{
                      transform: `rotate(${(Math.abs(metric.current) / Math.abs(metric.limit)) * 180}deg)`
                    }}
                  ></div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Risk Settings */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">Risk Parameters</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(riskSettings).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-white">
                    {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                  </div>
                  <div className="text-xs text-gray-400">
                    {key.includes('Loss') || key.includes('Drawdown') ? 'Maximum loss threshold' :
                     key.includes('Size') ? 'Per position limit' :
                     key.includes('Leverage') ? 'Maximum leverage allowed' :
                     key.includes('Correlation') ? 'Portfolio correlation limit' :
                     key.includes('Ratio') ? 'Risk/reward ratio' :
                     key.includes('Margin') ? 'Margin utilization limit' :
                     'Risk parameter setting'}
                  </div>
                </div>
                
                <div className="w-32">
                  <input
                    type="number"
                    step={value < 1 ? '0.1' : '1'}
                    value={value}
                    onChange={(e) => handleSettingChange(key as keyof RiskSettings, parseFloat(e.target.value) || 0)}
                    className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm text-right"
                  />
                </div>
              </div>
            ))}

            <div className="pt-4 border-t border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">Auto Risk Management</span>
                <button className="w-10 h-6 bg-blue-600 rounded-full relative">
                  <div className="w-4 h-4 bg-white rounded-full absolute top-1 right-1"></div>
                </button>
              </div>
              <div className="text-xs text-gray-400">
                Automatically adjust position sizes and close positions when risk limits are breached
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Portfolio Risk Breakdown */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">Portfolio Risk Distribution</h3>
          </CardHeader>
          <CardContent>
            <div className="h-48 mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={portfolioRiskData}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={70}
                    paddingAngle={2}
                    dataKey="exposure"
                  >
                    {portfolioRiskData.map((entry, index) => (
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
                      `${value}% (VaR: ${props.payload.var}%)`,
                      name
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-3">
              {portfolioRiskData.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-gray-300">{item.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-medium">{item.exposure}%</div>
                    <div className="text-gray-400 text-xs">VaR: {item.var}%</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk History */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-white">Risk Metrics History</h3>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskHistory}>
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
                    name === 'var' ? `${value}%` : 
                    name === 'sharpe' ? value.toFixed(2) :
                    `${value}%`,
                    name === 'var' ? 'Value at Risk' :
                    name === 'sharpe' ? 'Sharpe Ratio' :
                    'Max Drawdown'
                  ]}
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <Bar dataKey="var" fill="#EF4444" name="VaR" radius={[2, 2, 0, 0]} />
                <Bar dataKey="maxDD" fill="#F59E0B" name="Max DD" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Risk Alerts */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-white">Recent Risk Events</h3>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start space-x-3 p-3 bg-yellow-900/20 border border-yellow-700 rounded-lg">
              <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2"></div>
              <div>
                <div className="font-medium text-white">Correlation Warning</div>
                <div className="text-sm text-gray-300">
                  Portfolio correlation increased to 0.65 (limit: 0.80)
                </div>
                <div className="text-xs text-gray-500 mt-1">2 hours ago</div>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-green-900/20 border border-green-700 rounded-lg">
              <div className="w-2 h-2 bg-green-400 rounded-full mt-2"></div>
              <div>
                <div className="font-medium text-white">Risk Limit Restored</div>
                <div className="text-sm text-gray-300">
                  Daily loss returned within acceptable limits (-0.8%)
                </div>
                <div className="text-xs text-gray-500 mt-1">4 hours ago</div>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-blue-900/20 border border-blue-700 rounded-lg">
              <div className="w-2 h-2 bg-blue-400 rounded-full mt-2"></div>
              <div>
                <div className="font-medium text-white">Position Adjustment</div>
                <div className="text-sm text-gray-300">
                  Reduced BTC-USD exposure from 70% to 65% due to volatility spike
                </div>
                <div className="text-xs text-gray-500 mt-1">6 hours ago</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}