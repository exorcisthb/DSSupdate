import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { Zap, TrendingUp, DollarSign, Target, Award } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

const formatNumber = (val) => new Intl.NumberFormat('vi-VN').format(val);
const formatCurrency = (val) => {
  if (val >= 1000000000) return (val / 1000000000).toFixed(2) + ' tỷ đ';
  if (val >= 1000000) return (val / 1000000).toFixed(1) + ' triệu đ';
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val).replace('₫', 'đ');
};

export default function WhatIfTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState(0);

  useEffect(() => {
    fetchWhatIf();
  }, []);

  const fetchWhatIf = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/whatif`);
      if (!response.ok) throw new Error('Failed to fetch what-if scenarios');
      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-red-900 bg-red-900/10">
        <p className="text-center text-red-400">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const currentScenario = data.scenarios[selectedScenario];
  
  // Prepare comparison data
  const comparisonData = data.scenarios.map(s => ({
    name: s.scenario_name,
    'Revenue Increase': s.impact.revenue_increase,
    'Sold Increase': s.impact.sold_increase * 1000, // Scale for visibility
    'Market Share Gain': s.impact.market_share_gain * 1000000 // Scale for visibility
  }));

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-900">
        <h2 className="text-lg font-bold font-mono tracking-wider uppercase text-slate-200 flex items-center gap-2">
          <Zap className="w-5 h-5 text-orange-500" />
          What-If Scenario Analysis
        </h2>
        <p className="text-sm text-slate-400 mt-1">Simulate business decisions and predict KPI impact</p>
      </div>

      {/* Scenario selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {data.scenarios.map((s, idx) => (
          <button
            key={idx}
            onClick={() => setSelectedScenario(idx)}
            className={`glass-panel p-4 rounded-xl text-left transition-all ${
              selectedScenario === idx
                ? 'border-2 border-orange-500 bg-orange-500/10'
                : 'border border-slate-900 hover:border-slate-800'
            }`}
          >
            <div className="text-sm font-bold text-slate-200 mb-2">{s.scenario_name}</div>
            <div className="text-xs text-slate-400">
              Revenue: <span className="text-emerald-400 font-mono">+{(s.impact.revenue_increase_pct).toFixed(1)}%</span>
            </div>
          </button>
        ))}
      </div>

      {/* Selected scenario details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left: Details */}
        <div className="lg:col-span-1 space-y-4">
          
          {/* Parameters card */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-900">
            <h3 className="text-sm font-bold font-mono uppercase text-slate-300 mb-3 flex items-center gap-2">
              <Target className="w-4 h-4 text-orange-500" />
              Scenario Parameters
            </h3>
            <div className="space-y-2 text-sm">
              {Object.entries(currentScenario.parameters).map(([key, value]) => (
                <div key={key} className="flex justify-between py-2 border-b border-slate-900">
                  <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="font-mono text-slate-200">
                    {Array.isArray(value) ? `${value.length} items` : value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Baseline vs Predicted */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-900">
            <h3 className="text-sm font-bold font-mono uppercase text-slate-300 mb-3">
              Baseline vs Predicted
            </h3>
            <div className="space-y-3 text-sm">
              <div>
                <div className="text-xs text-slate-500 mb-1">Revenue</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-slate-400">{formatCurrency(currentScenario.baseline.tiki_revenue)}</span>
                  <span className="text-orange-500">→</span>
                  <span className="text-emerald-400 font-bold">{formatCurrency(currentScenario.predicted.tiki_revenue)}</span>
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Sold Count</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-slate-400">{formatNumber(currentScenario.baseline.tiki_sold)}</span>
                  <span className="text-orange-500">→</span>
                  <span className="text-emerald-400 font-bold">{formatNumber(currentScenario.predicted.tiki_sold)}</span>
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Market Share</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-slate-400">{currentScenario.baseline.market_share_pct}%</span>
                  <span className="text-orange-500">→</span>
                  <span className="text-emerald-400 font-bold">{currentScenario.predicted.market_share_pct}%</span>
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Right: Impact metrics */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* Impact cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="glass-panel p-5 rounded-2xl border border-slate-900">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-emerald-500" />
                <span className="text-xs uppercase text-slate-400 font-semibold">Revenue Impact</span>
              </div>
              <div className="text-3xl font-bold font-mono text-emerald-400 mb-1">
                +{formatCurrency(currentScenario.impact.revenue_increase)}
              </div>
              <div className="text-sm text-slate-500">
                +{currentScenario.impact.revenue_increase_pct}% increase
              </div>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-slate-900">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-blue-500" />
                <span className="text-xs uppercase text-slate-400 font-semibold">Sales Impact</span>
              </div>
              <div className="text-3xl font-bold font-mono text-blue-400 mb-1">
                +{formatNumber(currentScenario.impact.sold_increase)}
              </div>
              <div className="text-sm text-slate-500">
                +{currentScenario.impact.sold_increase_pct}% increase
              </div>
            </div>
          </div>

          {/* Comparison chart */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-900">
            <h3 className="text-sm font-bold font-mono uppercase text-slate-300 mb-4">
              Scenario Comparison
            </h3>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis 
                    dataKey="name" 
                    stroke="#64748b" 
                    fontSize={10}
                    angle={-15}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#0f172a', 
                      border: '1px solid #1e293b',
                      borderRadius: '8px'
                    }}
                    formatter={(value, name) => {
                      if (name === 'Revenue Increase') return [formatCurrency(value), name];
                      return [formatNumber(value / 1000), name];
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
                  <Bar dataKey="Revenue Increase" fill="#10b981" name="Revenue Impact (VND)" />
                  <Bar dataKey="Sold Increase" fill="#3b82f6" name="Sold Impact (k units)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      </div>

      {/* Recommendations */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-900 bg-gradient-to-r from-orange-500/5 to-transparent">
        <div className="flex items-start gap-3">
          <Award className="w-6 h-6 text-orange-500 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-sm font-bold text-slate-200 mb-2">AI Recommendations</h3>
            <p className="text-sm text-slate-400 mb-3">
              Based on scenario analysis, the <strong className="text-orange-400">{data.comparison.best_for_revenue}</strong> scenario 
              provides the highest revenue potential with minimal risk.
            </p>
            <p className="text-sm text-slate-400">
              For maximum market share growth, consider the <strong className="text-blue-400">{data.comparison.best_for_market_share}</strong> strategy.
            </p>
          </div>
        </div>
      </div>

    </div>
  );
}
