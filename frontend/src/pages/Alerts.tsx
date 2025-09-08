import { useState } from 'react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';

interface Alert {
  id: number;
  type: 'price' | 'pnl' | 'risk' | 'system' | 'strategy';
  symbol?: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  timestamp: string;
  isRead: boolean;
  isActive: boolean;
}

interface AlertRule {
  id: number;
  name: string;
  type: 'price' | 'pnl' | 'risk' | 'system';
  symbol?: string;
  condition: string;
  value: number;
  enabled: boolean;
  notificationMethod: 'email' | 'push' | 'both';
}

const mockAlerts: Alert[] = [
  {
    id: 1,
    type: 'price',
    symbol: 'BTC-USD',
    title: 'Price Alert',
    message: 'BTC-USD reached target price of $45,750',
    severity: 'success',
    timestamp: '2024-01-15T14:32:15Z',
    isRead: false,
    isActive: true
  },
  {
    id: 2,
    type: 'risk',
    title: 'Risk Warning',
    message: 'Portfolio correlation exceeded 65% threshold',
    severity: 'warning',
    timestamp: '2024-01-15T13:15:22Z',
    isRead: false,
    isActive: true
  },
  {
    id: 3,
    type: 'strategy',
    symbol: 'ETH-USD',
    title: 'Strategy Signal',
    message: 'EMA crossover bullish signal detected for ETH-USD',
    severity: 'info',
    timestamp: '2024-01-15T12:45:10Z',
    isRead: true,
    isActive: true
  },
  {
    id: 4,
    type: 'pnl',
    title: 'P&L Alert',
    message: 'Daily profit target of $2,000 achieved',
    severity: 'success',
    timestamp: '2024-01-15T11:20:33Z',
    isRead: true,
    isActive: true
  },
  {
    id: 5,
    type: 'system',
    title: 'System Alert',
    message: 'Connection to dYdX API restored after brief interruption',
    severity: 'info',
    timestamp: '2024-01-15T10:15:44Z',
    isRead: true,
    isActive: false
  }
];

const mockAlertRules: AlertRule[] = [
  {
    id: 1,
    name: 'BTC Price Above 46K',
    type: 'price',
    symbol: 'BTC-USD',
    condition: 'above',
    value: 46000,
    enabled: true,
    notificationMethod: 'both'
  },
  {
    id: 2,
    name: 'Daily Loss Limit',
    type: 'pnl',
    condition: 'below',
    value: -2000,
    enabled: true,
    notificationMethod: 'email'
  },
  {
    id: 3,
    name: 'High Portfolio Risk',
    type: 'risk',
    condition: 'above',
    value: 0.8,
    enabled: true,
    notificationMethod: 'push'
  },
  {
    id: 4,
    name: 'ETH Support Level',
    type: 'price',
    symbol: 'ETH-USD',
    condition: 'below',
    value: 2800,
    enabled: false,
    notificationMethod: 'both'
  }
];

export function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [alertRules, setAlertRules] = useState<AlertRule[]>(mockAlertRules);
  const [selectedTab, setSelectedTab] = useState<'alerts' | 'rules'>('alerts');
  const [filterType, setFilterType] = useState<string>('all');
  const [showNewRuleForm, setShowNewRuleForm] = useState(false);

  const [newRule, setNewRule] = useState<Partial<AlertRule>>({
    name: '',
    type: 'price',
    symbol: 'BTC-USD',
    condition: 'above',
    value: 0,
    enabled: true,
    notificationMethod: 'both'
  });

  const filteredAlerts = alerts.filter(alert => 
    filterType === 'all' || alert.type === filterType
  );

  const unreadCount = alerts.filter(alert => !alert.isRead && alert.isActive).length;

  const handleMarkAsRead = (alertId: number) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, isRead: true } : alert
    ));
  };

  const handleMarkAllRead = () => {
    setAlerts(prev => prev.map(alert => ({ ...alert, isRead: true })));
  };

  const handleToggleRule = (ruleId: number) => {
    setAlertRules(prev => prev.map(rule => 
      rule.id === ruleId ? { ...rule, enabled: !rule.enabled } : rule
    ));
  };

  const handleCreateRule = () => {
    if (newRule.name && newRule.value) {
      const rule: AlertRule = {
        id: Date.now(),
        name: newRule.name,
        type: newRule.type || 'price',
        symbol: newRule.symbol,
        condition: newRule.condition || 'above',
        value: newRule.value,
        enabled: newRule.enabled || true,
        notificationMethod: newRule.notificationMethod || 'both'
      };
      
      setAlertRules(prev => [...prev, rule]);
      setNewRule({
        name: '',
        type: 'price',
        symbol: 'BTC-USD',
        condition: 'above',
        value: 0,
        enabled: true,
        notificationMethod: 'both'
      });
      setShowNewRuleForm(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'border-red-500 bg-red-900/20';
      case 'warning': return 'border-yellow-500 bg-yellow-900/20';
      case 'success': return 'border-green-500 bg-green-900/20';
      case 'info': return 'border-blue-500 bg-blue-900/20';
      default: return 'border-gray-500 bg-gray-900/20';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'success': return '✅';
      case 'info': return 'ℹ️';
      default: return '🔔';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'price': return '💰';
      case 'pnl': return '📊';
      case 'risk': return '⚡';
      case 'system': return '⚙️';
      case 'strategy': return '🎯';
      default: return '🔔';
    }
  };

  return (
    <div className="p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Alerts & Notifications</h1>
          <p className="text-gray-400">
            Manage alerts and notification rules
            {unreadCount > 0 && (
              <span className="ml-2 px-2 py-1 bg-red-600 text-white rounded-full text-xs">
                {unreadCount} unread
              </span>
            )}
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {unreadCount > 0 && (
            <button 
              onClick={handleMarkAllRead}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Mark All Read
            </button>
          )}
          <button 
            onClick={() => setShowNewRuleForm(true)}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            New Alert Rule
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-800 rounded-lg p-1">
        <button
          onClick={() => setSelectedTab('alerts')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedTab === 'alerts'
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Active Alerts ({filteredAlerts.filter(a => a.isActive).length})
        </button>
        <button
          onClick={() => setSelectedTab('rules')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedTab === 'rules'
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Alert Rules ({alertRules.filter(r => r.enabled).length} active)
        </button>
      </div>

      {selectedTab === 'alerts' && (
        <>
          {/* Alert Filters */}
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-400">Filter:</span>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-1 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
            >
              <option value="all">All Types</option>
              <option value="price">Price</option>
              <option value="pnl">P&L</option>
              <option value="risk">Risk</option>
              <option value="system">System</option>
              <option value="strategy">Strategy</option>
            </select>
          </div>

          {/* Alerts List */}
          <div className="space-y-3">
            {filteredAlerts.map((alert) => (
              <Card 
                key={alert.id}
                className={`${getSeverityColor(alert.severity)} ${
                  !alert.isRead ? 'ring-2 ring-blue-500/50' : ''
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className="text-xl">
                        {getTypeIcon(alert.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className="font-medium text-white">{alert.title}</h3>
                          {alert.symbol && (
                            <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                              {alert.symbol}
                            </span>
                          )}
                          <span className="text-lg">{getSeverityIcon(alert.severity)}</span>
                        </div>
                        <p className="text-sm text-gray-300 mt-1">{alert.message}</p>
                        <div className="text-xs text-gray-500 mt-2">
                          {new Date(alert.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {!alert.isRead && (
                        <button
                          onClick={() => handleMarkAsRead(alert.id)}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                        >
                          Mark Read
                        </button>
                      )}
                      <div className={`w-2 h-2 rounded-full ${
                        alert.isActive ? 'bg-green-400' : 'bg-gray-400'
                      }`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {selectedTab === 'rules' && (
        <>
          {/* Alert Rules */}
          <div className="space-y-3">
            {alertRules.map((rule) => (
              <Card key={rule.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="text-xl">{getTypeIcon(rule.type)}</div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="font-medium text-white">{rule.name}</h3>
                          {rule.symbol && (
                            <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                              {rule.symbol}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-400">
                          Alert when {rule.type} is {rule.condition} {rule.value}
                          {rule.type === 'price' && ' USD'}
                          {rule.type === 'risk' && rule.value < 1 && ' correlation'}
                        </p>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="text-xs text-gray-500">
                            Notify via: {rule.notificationMethod}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => handleToggleRule(rule.id)}
                        className={`w-10 h-6 rounded-full transition-colors relative ${
                          rule.enabled ? 'bg-green-600' : 'bg-gray-600'
                        }`}
                      >
                        <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                          rule.enabled ? 'translate-x-5' : 'translate-x-1'
                        }`} />
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* New Rule Form Modal */}
      {showNewRuleForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <h3 className="text-lg font-semibold text-white">Create New Alert Rule</h3>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Rule Name
                </label>
                <input
                  type="text"
                  value={newRule.name || ''}
                  onChange={(e) => setNewRule(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                  placeholder="e.g., BTC Price Alert"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Alert Type
                </label>
                <select
                  value={newRule.type || 'price'}
                  onChange={(e) => setNewRule(prev => ({ ...prev, type: e.target.value as any }))}
                  className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                >
                  <option value="price">Price</option>
                  <option value="pnl">P&L</option>
                  <option value="risk">Risk</option>
                  <option value="system">System</option>
                </select>
              </div>

              {newRule.type === 'price' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Symbol
                  </label>
                  <select
                    value={newRule.symbol || 'BTC-USD'}
                    onChange={(e) => setNewRule(prev => ({ ...prev, symbol: e.target.value }))}
                    className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                  >
                    <option value="BTC-USD">BTC-USD</option>
                    <option value="ETH-USD">ETH-USD</option>
                    <option value="LINK-USD">LINK-USD</option>
                  </select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Condition
                  </label>
                  <select
                    value={newRule.condition || 'above'}
                    onChange={(e) => setNewRule(prev => ({ ...prev, condition: e.target.value }))}
                    className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                  >
                    <option value="above">Above</option>
                    <option value="below">Below</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Value
                  </label>
                  <input
                    type="number"
                    value={newRule.value || ''}
                    onChange={(e) => setNewRule(prev => ({ ...prev, value: parseFloat(e.target.value) || 0 }))}
                    className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                    placeholder="0"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Notification Method
                </label>
                <select
                  value={newRule.notificationMethod || 'both'}
                  onChange={(e) => setNewRule(prev => ({ ...prev, notificationMethod: e.target.value as any }))}
                  className="w-full p-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm"
                >
                  <option value="email">Email Only</option>
                  <option value="push">Push Only</option>
                  <option value="both">Email & Push</option>
                </select>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4">
                <button
                  onClick={() => setShowNewRuleForm(false)}
                  className="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg text-sm font-medium transition-colors hover:bg-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateRule}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Create Rule
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}