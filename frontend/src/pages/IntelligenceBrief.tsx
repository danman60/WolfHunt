// 🐺 WOLF PACK INTELLIGENCE BRIEF - Dedicated Page
// Comprehensive AI-powered trading intelligence dashboard

import React from 'react';
import { WolfPackDashboard, LiveAlertBanner } from '../components/WolfPack/WolfPackIntelligence';

export function IntelligenceBrief() {
  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="border-b border-gray-700 pb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center text-2xl">
            🐺
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">
              Wolf Pack Intelligence Brief
            </h1>
            <p className="text-gray-400 mt-1">
              AI-powered multi-agent trading intelligence • Real-time market analysis
            </p>
          </div>
        </div>
      </div>

      {/* Live Alert Banner */}
      <LiveAlertBanner />

      {/* Main Wolf Pack Dashboard */}
      <WolfPackDashboard />

      {/* Additional Intelligence Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        
        {/* Market Context Panel */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            🌍 Market Context
          </h3>
          <div className="space-y-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Global Sentiment:</span>
              <span className="text-green-400 font-semibold">Bullish</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Volatility Regime:</span>
              <span className="text-yellow-400 font-semibold">Elevated</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Market Phase:</span>
              <span className="text-blue-400 font-semibold">Risk-On</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Crypto Dominance:</span>
              <span className="text-purple-400 font-semibold">BTC: 52.3%</span>
            </div>
          </div>
        </div>

        {/* Wolf Pack Status */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            ⚡ Wolf Pack Status
          </h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-300">All agents active and hunting</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
              <span className="text-sm text-gray-300">Data streams healthy</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-purple-400 rounded-full"></div>
              <span className="text-sm text-gray-300">Signal quality: High</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
              <span className="text-sm text-gray-300">Risk management: Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Intelligence Summary */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          📋 Intelligence Summary
        </h3>
        <div className="prose prose-invert max-w-none">
          <p className="text-gray-300 leading-relaxed">
            The Wolf Pack has identified <strong className="text-green-400">multiple convergence signals</strong> across 
            ETH, LINK, and WBTC. Technical analysis indicates strong bullish momentum with sentiment 
            analysis confirming positive market psychology. 
          </p>
          <p className="text-gray-300 leading-relaxed mt-3">
            <strong className="text-blue-400">Key Opportunities:</strong> LINK showing exceptional strength with 
            74.1/100 sentiment score and technical breakout patterns. ETH approaching resistance 
            levels with high probability support bounce scenario.
          </p>
          <p className="text-gray-300 leading-relaxed mt-3">
            <strong className="text-yellow-400">Risk Assessment:</strong> Current market conditions favor 
            controlled position increases with tight risk management. Volatility elevated but 
            directional bias remains positive.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center py-6 border-t border-gray-700">
        <p className="text-gray-500 text-sm">
          🐺 Wolf Pack Intelligence • Multi-Agent AI Trading System • 
          <span className="text-green-400 ml-2">Status: Hunting Alpha</span>
        </p>
      </div>
    </div>
  );
}