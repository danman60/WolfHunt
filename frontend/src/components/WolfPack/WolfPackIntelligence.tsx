// 🐺 WOLF PACK UNIFIED INTELLIGENCE DASHBOARD
// React components for the ultimate crypto trading command center

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../ui/Card';
import { apiService } from '../../services/api';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  DollarSign,
  Zap,
  Brain,
  Eye
} from 'lucide-react';

// 🎯 Type definitions for our intelligence data
interface StrategyAdjustment {
  adjustment_type: string;
  target_crypto: string;
  current_value: number;
  suggested_value: number;
  confidence: number;
  justification: string;
  expected_impact: string;
  risk_assessment: string;
}

interface UnifiedIntelligence {
  timestamp: string;
  eth_intelligence: CryptoIntelligence;
  link_intelligence: CryptoIntelligence;
  wbtc_intelligence: CryptoIntelligence;
  portfolio_signals: PortfolioSignals;
  strategy_suggestions: StrategyAdjustment[];
  market_context: MarketContext;
  system_health: SystemHealth;
}

interface CryptoIntelligence {
  price: number;
  technical_score: number;
  sentiment_score: number;
  signal_strength: string;
  volume_ratio: number;
  confidence_level: number;
  dominant_narrative: string;
  pattern_detected: string;
}

interface PortfolioSignals {
  overall_sentiment: number;
  technical_strength: number;
  volume_activity: number;
  signal_convergence: number;
  active_opportunities: number;
}

interface MarketContext {
  overall_trend: string;
  volatility_regime: string;
  sentiment_regime: string;
}

interface SystemHealth {
  quant_status: string;
  snoop_status: string;
  sage_status: string;
  brief_status: string;
  last_update: string;
  data_freshness: string;
  api_health: string;
}

// 🚀 Main Wolf Pack Intelligence Dashboard
export const WolfPackDashboard: React.FC = () => {
  const [intelligence, setIntelligence] = useState<UnifiedIntelligence | null>(null);
  const [liveSignals, setLiveSignals] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSuggestion, setSelectedSuggestion] = useState<StrategyAdjustment | null>(null);

  // 📡 Fetch Wolf Pack intelligence data
  const fetchIntelligence = async () => {
    try {
      const data = await apiService.getUnifiedIntelligence();
      setIntelligence(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchLiveSignals = async () => {
    try {
      const data = await apiService.getLiveSignals();
      setLiveSignals(data);
    } catch (err) {
      console.warn('Live signals API not available - using empty data');
      setLiveSignals([]);
    }
  };

  // 💰 Execute strategy suggestion
  const executeSuggestion = async (suggestion: StrategyAdjustment, approved: boolean) => {
    try {
      const result = await apiService.executeStrategySuggestion({
        suggestion_id: Math.random(), // Would be real ID in production
        approved,
        suggestion_data: suggestion
      });
      
      // Show feedback to user
      if (approved) {
        alert(`✅ Strategy executed: ${result.message}`);
      } else {
        alert(`❌ Strategy rejected: ${result.message}`);
      }
      
      // Refresh intelligence data
      fetchIntelligence();
    } catch (err) {
      alert('❌ Execution failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  // 🔄 Auto-refresh data
  useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      await fetchIntelligence();
      // await fetchLiveSignals(); // API not implemented
      setLoading(false);
    };

    fetchInitialData();

    // Refresh intelligence every 60 seconds (reduced from 30s)
    const intelligenceInterval = setInterval(fetchIntelligence, 60000);
    // Refresh live signals every 15 seconds (reduced from 5s to reduce API load)
    // Disable live signals polling since API is not implemented
    // const signalsInterval = setInterval(fetchLiveSignals, 15000);

    return () => {
      clearInterval(intelligenceInterval);
      // clearInterval(signalsInterval);
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-lg font-semibold">🐺 The Wolf Pack is hunting for alpha...</p>
        </div>
      </div>
    );
  }

  if (error || !intelligence) {
    return (
      <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <span className="text-red-300">🚨 Wolf Pack intelligence unavailable: {error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-white">
      {/* 🎯 PACK STATUS HEADER */}
      <PackStatusHeader 
        systemHealth={intelligence.system_health}
        portfolioSignals={intelligence.portfolio_signals}
        marketContext={intelligence.market_context}
      />

      {/* 📊 LIVE INTELLIGENCE GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <CryptoIntelligenceCard 
          crypto="ETH" 
          intelligence={intelligence.eth_intelligence}
          liveData={liveSignals?.signals?.ETH}
        />
        <CryptoIntelligenceCard 
          crypto="LINK" 
          intelligence={intelligence.link_intelligence}
          liveData={liveSignals?.signals?.LINK}
        />
        <CryptoIntelligenceCard 
          crypto="WBTC" 
          intelligence={intelligence.wbtc_intelligence}
          liveData={liveSignals?.signals?.WBTC}
        />
      </div>

      {/* 🧠 AI STRATEGY SUGGESTIONS */}
      <StrategySuggestionsPanel 
        suggestions={intelligence.strategy_suggestions}
        onExecute={executeSuggestion}
      />

      {/* 📈 PORTFOLIO PERFORMANCE METRICS */}
      <PortfolioMetricsPanel />
    </div>
  );
};

// 🎯 Pack Status Header Component
const PackStatusHeader: React.FC<{
  systemHealth: SystemHealth;
  portfolioSignals: PortfolioSignals;
  marketContext: MarketContext;
}> = ({ systemHealth, portfolioSignals, marketContext }) => {
  // Get overall API health status
  const getApiHealthStatus = () => {
    const apiHealth = systemHealth.api_health || 'UNKNOWN';
    const dataFreshness = systemHealth.data_freshness || 'UNKNOWN';
    
    if (apiHealth === 'OPERATIONAL' && dataFreshness === 'LIVE') {
      return { color: 'bg-green-500', text: 'LIVE DATA', tooltip: 'All APIs operational with live data' };
    } else if (apiHealth === 'OPERATIONAL') {
      return { color: 'bg-yellow-500', text: 'MIXED DATA', tooltip: 'APIs operational, some fallback data' };
    } else {
      return { color: 'bg-red-500', text: 'API ISSUES', tooltip: 'API connectivity issues' };
    }
  };

  const apiStatus = getApiHealthStatus();
  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center text-xl">
            🐺
          </div>
          <div>
            <h2 className="text-xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent">
              WOLF PACK INTELLIGENCE STATUS
            </h2>
            <p className="text-sm text-gray-400">Multi-Agent AI Trading Intelligence • GMX on Arbitrum</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">
              {portfolioSignals.technical_strength.toFixed(1)}
            </div>
            <div className="text-sm text-gray-400">Technical Strength</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">
              {portfolioSignals.overall_sentiment.toFixed(1)}
            </div>
            <div className="text-sm text-gray-400">Sentiment Score</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">
              {portfolioSignals.active_opportunities}
            </div>
            <div className="text-sm text-gray-400">Active Opportunities</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">
              {marketContext.overall_trend}
            </div>
            <div className="text-sm text-gray-400">Market Trend</div>
          </div>
        </div>
        
        <div className="flex items-center gap-4 flex-wrap">
          {/* Prominent API Data Quality Indicator */}
          <div className={`px-3 py-1 rounded-full text-xs font-bold text-white ${apiStatus.color} flex items-center gap-2`} 
               title={apiStatus.tooltip}>
            <div className={`w-2 h-2 rounded-full ${apiStatus.color === 'bg-green-500' ? 'animate-pulse bg-white' : 'bg-gray-300'}`} />
            📊 {apiStatus.text}
          </div>
          
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            systemHealth.quant_status === 'ACTIVE' ? 'bg-green-600' : 'bg-red-600'
          }`}>
            🔢 The Quant: {systemHealth.quant_status}
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            systemHealth.snoop_status === 'ACTIVE' ? 'bg-green-600' : 'bg-red-600'
          }`}>
            🕵️ The Snoop: {systemHealth.snoop_status}
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            systemHealth.sage_status === 'ACTIVE' ? 'bg-green-600' : 'bg-red-600'
          }`}>
            🔮 The Sage: {systemHealth.sage_status}
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            systemHealth.brief_status === 'ACTIVE' ? 'bg-green-600' : 'bg-red-600'
          }`}>
            📋 The Brief: {systemHealth.brief_status}
          </div>
          <div className="px-3 py-1 bg-slate-600 rounded-full text-xs">
            📡 Last Update: {new Date(systemHealth.last_update).toLocaleTimeString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// 📊 Individual Crypto Intelligence Card
const CryptoIntelligenceCard: React.FC<{
  crypto: string;
  intelligence: CryptoIntelligence;
  liveData?: any;
}> = ({ crypto, intelligence, liveData }) => {
  const getSignalColor = (score: number) => {
    if (score > 70) return 'text-green-400';
    if (score > 30) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSignalIcon = (score: number) => {
    if (score > 70) return <TrendingUp className="h-4 w-4" />;
    if (score > 30) return <Activity className="h-4 w-4" />;
    return <TrendingDown className="h-4 w-4" />;
  };

  const getSignalStrengthColor = (strength: string) => {
    switch (strength) {
      case 'VERY_STRONG': return 'bg-green-600';
      case 'STRONG': return 'bg-green-500';
      case 'MODERATE': return 'bg-yellow-500';
      case 'WEAK': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const displayPrice = liveData?.price || intelligence.price || 0;
  const dataQuality = intelligence.data_quality || 'UNKNOWN';

  // Determine data quality color and icon
  const getDataQualityIndicator = (quality: string) => {
    switch (quality) {
      case 'LIVE_DATA':
        return { color: 'bg-green-500', icon: '🔴', text: 'LIVE', tooltip: 'Real-time market data' };
      case 'LIVE_PRICE_FALLBACK_INDICATORS':
        return { color: 'bg-yellow-500', icon: '🟡', text: 'LIVE PRICE', tooltip: 'Live prices, fallback indicators' };
      case 'FALLBACK_DATA':
        return { color: 'bg-red-500', icon: '🔴', text: 'FALLBACK', tooltip: 'Using cached/fallback data' };
      default:
        return { color: 'bg-gray-500', icon: '❓', text: 'UNKNOWN', tooltip: 'Data quality unknown' };
    }
  };

  const qualityIndicator = getDataQualityIndicator(dataQuality);

  return (
    <Card className="bg-slate-800 border-slate-700 hover:border-slate-600 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold">{crypto}</span>
          <div className="flex items-center gap-2">
            {getSignalIcon(intelligence.technical_score)}
            <span className="text-sm text-gray-400">
              ${displayPrice.toFixed(2)}
            </span>
            
            {/* Enhanced Data Quality Indicator */}
            <div className={`px-2 py-1 rounded-full text-xs font-bold text-white ${qualityIndicator.color} flex items-center gap-1`} 
                 title={qualityIndicator.tooltip}>
              <div className={`w-2 h-2 rounded-full ${dataQuality === 'LIVE_DATA' || dataQuality === 'LIVE_PRICE_FALLBACK_INDICATORS' ? 'animate-pulse bg-white' : 'bg-gray-300'}`} />
              {qualityIndicator.text}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 🎯 SIGNAL CONVERGENCE */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm">Technical Signal</span>
            <span className={`font-semibold ${getSignalColor(intelligence.technical_score)}`}>
              {intelligence.technical_score?.toFixed(1) || '50.0'}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                intelligence.technical_score > 70 ? 'bg-green-400' : 
                intelligence.technical_score > 30 ? 'bg-yellow-400' : 'bg-red-400'
              }`}
              style={{ width: `${Math.max(5, intelligence.technical_score || 50)}%` }}
            />
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm">Sentiment Signal</span>
            <span className={`font-semibold ${getSignalColor(intelligence.sentiment_score)}`}>
              {intelligence.sentiment_score?.toFixed(1) || '50.0'}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                intelligence.sentiment_score > 70 ? 'bg-green-400' : 
                intelligence.sentiment_score > 30 ? 'bg-yellow-400' : 'bg-red-400'
              }`}
              style={{ width: `${Math.max(5, intelligence.sentiment_score || 50)}%` }}
            />
          </div>
        </div>

        {/* 📈 KEY METRICS */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-gray-400">Volume:</span>
            <span className={`ml-1 font-semibold ${intelligence.volume_ratio > 1.5 ? 'text-green-400' : 'text-gray-300'}`}>
              {intelligence.volume_ratio?.toFixed(1) || '1.0'}x
            </span>
          </div>
          <div>
            <span className="text-gray-400">Confidence:</span>
            <span className="ml-1 font-semibold text-blue-400">
              {((intelligence.confidence_level || 0.5) * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* 📊 PATTERN AND NARRATIVE */}
        <div className="space-y-2 text-xs">
          <div>
            <span className="text-gray-400">Pattern:</span>
            <span className="ml-1 text-purple-400">
              {intelligence.pattern_detected || 'Normal'}
            </span>
          </div>
          <div>
            <span className="text-gray-400">Narrative:</span>
            <span className="ml-1 text-cyan-400">
              {intelligence.dominant_narrative || 'Mixed'}
            </span>
          </div>
        </div>

        {/* 🚨 SIGNAL STRENGTH BADGE */}
        <div className="flex justify-center">
          <div className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getSignalStrengthColor(intelligence.signal_strength)}`}>
            {intelligence.signal_strength || 'NEUTRAL'}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// 🧠 AI Strategy Suggestions Panel
const StrategySuggestionsPanel: React.FC<{
  suggestions: StrategyAdjustment[];
  onExecute: (suggestion: StrategyAdjustment, approved: boolean) => void;
}> = ({ suggestions, onExecute }) => {
  const [expandedSuggestion, setExpandedSuggestion] = useState<number | null>(null);

  if (!suggestions || suggestions.length === 0) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            🧠 AI Strategy Engine
          </h3>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-400">
            <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>The Wolf Pack is monitoring... No immediate adjustments recommended.</p>
            <p className="text-sm mt-2">Current allocations appear optimal based on signal convergence.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            🧠 AI Strategy Engine
          </h3>
          <div className="px-3 py-1 bg-slate-600 rounded-full text-xs">
            {suggestions.length} Suggestions
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {suggestions.map((suggestion, index) => (
          <div key={index} className="border border-slate-600 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${
                  suggestion.adjustment_type === 'allocation_increase' ? 'bg-green-500' : 
                  suggestion.adjustment_type === 'allocation_decrease' ? 'bg-red-500' : 
                  suggestion.adjustment_type === 'risk_adjustment' ? 'bg-yellow-500' : 'bg-purple-500'
                }`} />
                <div>
                  <div className="font-semibold">
                    {suggestion.target_crypto} - {suggestion.adjustment_type.replace('_', ' ').toUpperCase()}
                  </div>
                  <div className="text-sm text-gray-400">
                    {suggestion.current_value.toFixed(1)}% → {suggestion.suggested_value.toFixed(1)}%
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="px-2 py-1 bg-slate-600 rounded text-xs">
                  {(suggestion.confidence * 100).toFixed(0)}% Confidence
                </div>
                <button
                  className="text-gray-400 hover:text-white transition-colors"
                  onClick={() => setExpandedSuggestion(expandedSuggestion === index ? null : index)}
                >
                  {expandedSuggestion === index ? '▼' : '▶'}
                </button>
              </div>
            </div>

            {expandedSuggestion === index && (
              <div className="space-y-3 bg-slate-900 p-4 rounded-lg">
                <div>
                  <div className="text-sm font-semibold text-green-400 mb-1">📊 JUSTIFICATION:</div>
                  <div className="text-sm text-gray-300">{suggestion.justification}</div>
                </div>
                
                <div>
                  <div className="text-sm font-semibold text-blue-400 mb-1">💰 EXPECTED IMPACT:</div>
                  <div className="text-sm text-gray-300">{suggestion.expected_impact}</div>
                </div>
                
                <div>
                  <div className="text-sm font-semibold text-yellow-400 mb-1">⚠️ RISK ASSESSMENT:</div>
                  <div className="text-sm text-gray-300">{suggestion.risk_assessment}</div>
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm flex items-center gap-1"
                    onClick={() => onExecute(suggestion, true)}
                  >
                    <CheckCircle className="h-4 w-4" />
                    Execute Strategy
                  </button>
                  <button
                    className="border border-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded text-sm"
                    onClick={() => onExecute(suggestion, false)}
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

// 📈 Portfolio Performance Metrics Panel
const PortfolioMetricsPanel: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await apiService.getPerformanceMetrics();
        setMetrics(data);
      } catch (err) {
        console.warn('Failed to fetch performance metrics:', err);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  if (!metrics) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-slate-700 rounded w-1/4"></div>
            <div className="space-y-2">
              <div className="h-3 bg-slate-700 rounded"></div>
              <div className="h-3 bg-slate-700 rounded w-5/6"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader>
        <h3 className="text-lg font-semibold">📈 WOLF PACK PERFORMANCE METRICS</h3>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* 🎯 SIGNAL ACCURACY */}
          <div className="space-y-3">
            <h4 className="font-semibold text-green-400">🎯 Signal Accuracy</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Technical Signals</span>
                <span className="font-semibold">{metrics.signal_accuracy.technical_signals.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Sentiment Signals</span>
                <span className="font-semibold">{metrics.signal_accuracy.sentiment_signals.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Combined Signals</span>
                <span className="font-semibold text-green-400">{metrics.signal_accuracy.combined_signals.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* 💰 PORTFOLIO PERFORMANCE */}
          <div className="space-y-3">
            <h4 className="font-semibold text-blue-400">💰 Portfolio Performance</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">7D Return</span>
                <span className="font-semibold text-green-400">+{metrics.portfolio_performance.total_return_7d.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">30D Return</span>
                <span className="font-semibold text-green-400">+{metrics.portfolio_performance.total_return_30d.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Sharpe Ratio</span>
                <span className="font-semibold">{metrics.portfolio_performance.sharpe_ratio.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Win Rate</span>
                <span className="font-semibold">{metrics.portfolio_performance.win_rate.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* ⚡ SYSTEM EFFICIENCY */}
          <div className="space-y-3">
            <h4 className="font-semibold text-purple-400">⚡ System Efficiency</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Uptime</span>
                <span className="font-semibold">{metrics.system_efficiency.uptime.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Response Time</span>
                <span className="font-semibold">{metrics.system_efficiency.avg_response_time}ms</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Success Rate</span>
                <span className="font-semibold text-green-400">
                  {((metrics.system_efficiency.successful_updates / (metrics.system_efficiency.successful_updates + metrics.system_efficiency.failed_updates)) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Wolf Pack Status</span>
                <span className={`font-semibold ${metrics.system_efficiency.wolf_pack_status === 'HUNTING' ? 'text-green-400' : 'text-yellow-400'}`}>
                  {metrics.system_efficiency.wolf_pack_status}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// 🚨 Real-time Alert Component
export const LiveAlertBanner: React.FC = () => {
  const [alerts, setAlerts] = useState<string[]>([]);

  useEffect(() => {
    // Simulate live alerts based on market conditions
    const checkForAlerts = async () => {
      try {
        // In a real implementation, this would fetch from your alerts endpoint
        const mockAlerts = [
          "🚀 WBTC showing exceptional bullish convergence - 89% confidence",
          "⚡ ETH volume spike detected - 2.1x normal volume",
          "📈 Portfolio up 15.8% this week - Wolf Pack hunting alpha!"
        ];
        
        // Randomly show alerts
        if (Math.random() > 0.7) {
          setAlerts([mockAlerts[Math.floor(Math.random() * mockAlerts.length)]]);
        } else {
          setAlerts([]);
        }
      } catch (err) {
        console.warn('Alert check failed:', err);
      }
    };

    checkForAlerts();
    const interval = setInterval(checkForAlerts, 15000); // Check every 15 seconds
    return () => clearInterval(interval);
  }, []);

  if (alerts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {alerts.slice(0, 3).map((alert, index) => (
        <div key={index} className="bg-slate-900/95 border border-green-500 text-white max-w-md p-3 rounded-lg backdrop-blur">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-green-400" />
            <div className="text-sm">{alert}</div>
          </div>
        </div>
      ))}
    </div>
  );
};