import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, Calendar, AlertCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

const formatNumber = (val) => new Intl.NumberFormat('vi-VN').format(val);
const formatCurrency = (val) => {
  if (val >= 1000000000) return (val / 1000000000).toFixed(2) + ' tỷ đ';
  if (val >= 1000000) return (val / 1000000).toFixed(1) + ' triệu đ';
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val).replace('₫', 'đ');
};

export default function ForecastTab() {
  const [forecasts, setForecasts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(0);
  const [daysAhead, setDaysAhead] = useState(30);

  useEffect(() => {
    fetchForecasts();
  }, [daysAhead]);

  const fetchForecasts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/forecast?top_n=5&days=${daysAhead}`);
      if (!response.ok) throw new Error('Failed to fetch forecasts');
      const data = await response.json();
      setForecasts(data.forecasts);
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
        <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
        <p className="text-center text-red-400">{error}</p>
      </div>
    );
  }

  if (!forecasts || forecasts.length === 0) {
    return (
      <div className="glass-panel p-6 rounded-2xl">
        <p className="text-center text-slate-400">Insufficient data for forecasting</p>
      </div>
    );
  }

  const currentForecast = forecasts[selectedCategory];
  
  // Combine historical + forecast data for chart
  const chartData = [
    ...currentForecast.historical.map(d => ({ ...d, type: 'historical' })),
    ...currentForecast.forecast.map(d => ({ ...d, type: 'forecast' }))
  ];

  return (
    <div className="space-y-6">
      
      {/* Header with controls */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-900 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-lg font-bold font-mono tracking-wider uppercase text-slate-200 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-orange-500" />
            Predictive Analytics - Time Series Forecasting
          </h2>
          <p className="text-sm text-slate-400 mt-1">Dự đoán sold_count và revenue dựa trên historical trends</p>
        </div>
        
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400">Forecast horizon:</label>
          <select 
            value={daysAhead}
            onChange={(e) => setDaysAhead(Number(e.target.value))}
            className="px-3 py-2 rounded-lg text-xs custom-input font-medium"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
          </select>
        </div>
      </div>

      {/* Category selector */}
      <div className="flex gap-2 flex-wrap">
        {forecasts.map((f, idx) => (
          <button
            key={idx}
            onClick={() => setSelectedCategory(idx)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              selectedCategory === idx
                ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/20'
                : 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800'
            }`}
          >
            {f.category}
          </button>
        ))}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-2xl border border-slate-900">
          <div className="text-xs uppercase text-slate-400 font-semibold mb-2">Current Sold</div>
          <div className="text-2xl font-bold font-mono text-slate-100">{formatNumber(currentForecast.summary.current_sold)}</div>
        </div>
        
        <div className="glass-panel p-4 rounded-2xl border border-slate-900">
          <div className="text-xs uppercase text-slate-400 font-semibold mb-2">Predicted ({daysAhead}d)</div>
          <div className="text-2xl font-bold font-mono text-orange-400">{formatNumber(currentForecast.summary.predicted_sold_30d)}</div>
        </div>
        
        <div className="glass-panel p-4 rounded-2xl border border-slate-900">
          <div className="text-xs uppercase text-slate-400 font-semibold mb-2">Growth Rate</div>
          <div className={`text-2xl font-bold font-mono ${currentForecast.summary.growth_rate_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {currentForecast.summary.growth_rate_pct > 0 ? '+' : ''}{currentForecast.summary.growth_rate_pct}%
          </div>
        </div>
        
        <div className="glass-panel p-4 rounded-2xl border border-slate-900">
          <div className="text-xs uppercase text-slate-400 font-semibold mb-2">Avg Daily Growth</div>
          <div className="text-2xl font-bold font-mono text-slate-100">{formatNumber(currentForecast.summary.avg_daily_growth)}</div>
        </div>
      </div>

      {/* Chart */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-900 shadow-2xl">
        <h3 className="text-sm font-bold font-mono uppercase text-slate-300 mb-4">
          Sold Count: Historical + Forecast
        </h3>
        
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorHistorical" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
              <YAxis stroke="#64748b" fontSize={10} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#0f172a', 
                  border: '1px solid #1e293b',
                  borderRadius: '8px'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="sold_count" 
                stroke="#3b82f6" 
                fill="url(#colorHistorical)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        <div className="mt-4 pt-4 border-t border-slate-900 flex items-center gap-6 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span className="text-slate-400">Historical Data</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span className="text-slate-400">Forecast (Linear Regression)</span>
          </div>
          <div className="ml-auto text-slate-500 italic">
            Note: 95% confidence intervals shown as shaded area
          </div>
        </div>
      </div>

    </div>
  );
}
