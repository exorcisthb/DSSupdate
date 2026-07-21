import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Area, AreaChart, ReferenceLine
} from 'recharts';
import { TrendingUp, AlertCircle, Info, Zap, Star } from 'lucide-react';
import RegressionPredictor from './RegressionPredictor';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

const formatNumber = (val) => new Intl.NumberFormat('vi-VN').format(val);
const formatCurrency = (val) => {
  if (val >= 1_000_000_000) return (val / 1_000_000_000).toFixed(2) + ' tỷ đ';
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + ' triệu đ';
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val).replace('₫', 'đ');
};

// ── ASG2 Q2 Regression Model Coefficients ─────────────────────────────────────
const REGRESSION_MODEL = {
  intercept: 2.4146,
  beta_price: -1.3132e-6,
  beta_authentic: 0.7983,
  beta_delivery: 1.4037e-4,
  beta_price_auth: 3.5816e-7,
  r_squared: 0.71,   // approximate from ASG2
};

export default function ForecastTab() {
  const [forecasts, setForecasts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(0);
  const [daysAhead, setDaysAhead] = useState(30);
  const [showCI, setShowCI] = useState(true);

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
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-3"></div>
          <p className="text-gray-500 text-sm font-mono">Đang chạy mô hình Linear Regression...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-red-200 bg-red-50">
        <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
        <p className="text-center text-red-600 font-medium">{error}</p>
      </div>
    );
  }

  if (!forecasts || forecasts.length === 0) {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-gray-200 bg-white">
        <p className="text-center text-gray-400">Không đủ dữ liệu lịch sử để dự báo</p>
      </div>
    );
  }

  const currentForecast = forecasts[selectedCategory];

  // Build chart data: historical (blue) + forecast (orange) + CI bands
  const lastHistoricalDate = currentForecast.historical[currentForecast.historical.length - 1]?.date;
  const chartData = [
    ...currentForecast.historical.map(d => ({
      date: d.date.slice(5),  // MM-DD
      historical: d.sold_count,
      forecast: null,
      upper: null,
      lower: null,
    })),
    ...currentForecast.forecast.map(d => ({
      date: d.date.slice(5),
      historical: null,
      forecast: d.sold_count,
      upper: d.sold_count_upper,
      lower: d.sold_count_lower,
    })),
  ];

  const m = REGRESSION_MODEL;

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="glass-panel p-5 rounded-2xl border border-teal-200 bg-white">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold font-mono tracking-wider uppercase text-gray-800 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-teal-500" />
              Predictive Demand Forecast — Tab 4
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Dự báo sold_count theo <strong>ASG2 Q2</strong> — Linear Regression với 95% CI trên 9,625 bản ghi lịch sử
            </p>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <label className="text-xs text-gray-500 font-mono">Horizon:</label>
            <select
              value={daysAhead}
              onChange={(e) => setDaysAhead(Number(e.target.value))}
              className="px-3 py-2 rounded-lg text-xs custom-input font-medium border border-emerald-200"
            >
              <option value={7}>7 ngày</option>
              <option value={14}>14 ngày</option>
              <option value={30}>30 ngày</option>
              <option value={60}>60 ngày</option>
            </select>
            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input
                type="checkbox"
                checked={showCI}
                onChange={e => setShowCI(e.target.checked)}
                className="accent-teal-500 rounded w-3.5 h-3.5"
              />
              <span className="text-gray-600 font-mono">95% CI</span>
            </label>
          </div>
        </div>
      </div>

      {/* ASG2 Q2 Regression Model Card */}
      <div className="glass-panel p-5 rounded-2xl border border-teal-200 bg-gradient-to-r from-teal-50 to-emerald-50">
        <h3 className="text-xs font-bold font-mono uppercase text-teal-800 mb-3 flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5" /> Mô hình Interaction Regression (ASG2 Q2)
        </h3>
        <div className="font-mono text-xs bg-white/70 border border-teal-200 rounded-xl p-4 mb-4 text-gray-700 leading-relaxed">
          <span className="text-teal-700 font-bold">ln(sold_count + 1)</span> = {m.intercept}
          <span className="text-blue-600"> + ({m.beta_price.toExponential(4)})</span> × Price
          <span className="text-emerald-600"> + ({m.beta_authentic})</span> × is_authentic
          <span className="text-orange-600"> + ({m.beta_delivery.toExponential(4)})</span> × delivery_days
          <span className="text-purple-600"> + ({m.beta_price_auth.toExponential(4)})</span> × (Price × is_authentic)
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div className="bg-white/80 rounded-lg p-2.5 border border-emerald-200">
            <div className="text-[10px] font-semibold uppercase text-gray-500 mb-1">β₁ Price</div>
            <div className="font-mono font-bold text-blue-600">{m.beta_price.toExponential(4)}</div>
            <div className="text-[10px] text-gray-500">Đường cầu giảm giá</div>
          </div>
          <div className="bg-white/80 rounded-lg p-2.5 border border-emerald-200">
            <div className="text-[10px] font-semibold uppercase text-gray-500 mb-1">β₂ is_authentic</div>
            <div className="font-mono font-bold text-emerald-600">+{m.beta_authentic}</div>
            <div className="text-[10px] text-gray-500">Official Store × e^0.8 ≈ <strong>2.2×</strong> sales</div>
          </div>
          <div className="bg-white/80 rounded-lg p-2.5 border border-emerald-200">
            <div className="text-[10px] font-semibold uppercase text-gray-500 mb-1">β₃ Delivery</div>
            <div className="font-mono font-bold text-orange-600">{m.beta_delivery.toExponential(4)}</div>
            <div className="text-[10px] text-gray-500">Tác động nhỏ ở phạm vi này</div>
          </div>
          <div className="bg-white/80 rounded-lg p-2.5 border border-emerald-200">
            <div className="text-[10px] font-semibold uppercase text-gray-500 mb-1">β₄ Interaction</div>
            <div className="font-mono font-bold text-purple-600">+{m.beta_price_auth.toExponential(4)}</div>
            <div className="text-[10px] text-gray-500">Official nhạy giá ít hơn −27%</div>
          </div>
        </div>
        {/* is_authentic highlight */}
        <div className="mt-3 flex items-center gap-2 bg-emerald-100 border border-emerald-300 rounded-lg px-3 py-2">
          <Star className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <p className="text-xs text-emerald-800">
            <strong>Insight Q2:</strong> Badge "Hàng chính hãng" (is_authentic = 1) mang lại lợi thế doanh số
            <strong> 2.2 lần</strong> so với regular store — đây là rào cản lớn nhất cần vượt qua bằng chiến lược giá &amp; review.
          </p>
        </div>
      </div>

      {/* ASG2 Q2 Interactive Predictor */}
      <RegressionPredictor model={m} />

      {/* Category selector */}
      <div className="flex gap-2 flex-wrap">
        {forecasts.map((f, idx) => (
          <button
            key={idx}
            onClick={() => setSelectedCategory(idx)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              selectedCategory === idx
                ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/20'
                : 'bg-white text-gray-600 hover:bg-teal-50 border border-emerald-200'
            }`}
          >
            {f.category}
          </button>
        ))}
      </div>

      {/* Summary KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-2xl border border-emerald-200 bg-white">
          <div className="text-xs uppercase text-gray-500 font-semibold mb-2">Lượng bán hiện tại</div>
          <div className="text-2xl font-bold font-mono text-gray-800">
            {formatNumber(currentForecast.summary.current_sold)}
          </div>
          <div className="text-[10px] text-gray-500 mt-1">sold_count (ngày gần nhất)</div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-teal-200 bg-teal-50">
          <div className="text-xs uppercase text-teal-600 font-semibold mb-2">Dự báo {daysAhead} ngày</div>
          <div className="text-2xl font-bold font-mono text-teal-700">
            {formatNumber(currentForecast.summary.predicted_sold_30d)}
          </div>
          <div className="text-[10px] text-gray-500 mt-1">sold_count dự kiến</div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-emerald-200 bg-white">
          <div className="text-xs uppercase text-gray-500 font-semibold mb-2">Tốc độ tăng trưởng</div>
          <div className={`text-2xl font-bold font-mono ${
            currentForecast.summary.growth_rate_pct >= 0 ? 'text-emerald-600' : 'text-red-500'
          }`}>
            {currentForecast.summary.growth_rate_pct > 0 ? '+' : ''}{currentForecast.summary.growth_rate_pct}%
          </div>
          <div className="text-[10px] text-gray-500 mt-1">trong {daysAhead} ngày tới</div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-emerald-200 bg-white">
          <div className="text-xs uppercase text-gray-500 font-semibold mb-2">Tăng trưởng trung bình</div>
          <div className="text-2xl font-bold font-mono text-gray-700">
            {formatNumber(currentForecast.summary.avg_daily_growth)}
          </div>
          <div className="text-[10px] text-gray-500 mt-1">units/ngày</div>
        </div>
      </div>

      {/* Main Forecast Chart */}
      <div className="glass-panel p-6 rounded-2xl border border-emerald-200 shadow-xl bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold font-mono uppercase text-gray-700">
            {currentForecast.category} — Sold Count: Lịch sử + Dự báo {daysAhead} ngày
          </h3>
          {showCI && (
            <span className="text-[10px] text-gray-400 italic">Vùng xanh nhạt = 95% CI (±20%)</span>
          )}
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
              <defs>
                <linearGradient id="colorHist" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0d9488" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#0d9488" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorCI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0d9488" stopOpacity={0.12} />
                  <stop offset="95%" stopColor="#0d9488" stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#d1fae5" />
              <XAxis
                dataKey="date"
                stroke="#6b7280"
                fontSize={9}
                interval="preserveStartEnd"
              />
              <YAxis stroke="#6b7280" fontSize={9} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #d1fae5',
                  borderRadius: '8px',
                  fontSize: '11px'
                }}
                formatter={(value, name) => {
                  if (value === null) return [null, name];
                  const labels = {
                    historical: 'Lịch sử',
                    forecast: 'Dự báo',
                    upper: 'CI trên (95%)',
                    lower: 'CI dưới (95%)',
                  };
                  return [formatNumber(value), labels[name] || name];
                }}
              />
              <Legend
                iconSize={8}
                iconType="circle"
                wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }}
              />

              {/* Historical area */}
              <Area
                type="monotone"
                dataKey="historical"
                stroke="#3b82f6"
                fill="url(#colorHist)"
                strokeWidth={2}
                dot={{ r: 3, fill: '#3b82f6' }}
                name="Lịch sử"
                connectNulls={false}
              />

              {/* 95% CI bands (only when showCI) */}
              {showCI && (
                <>
                  <Area
                    type="monotone"
                    dataKey="upper"
                    stroke="transparent"
                    fill="url(#colorCI)"
                    strokeWidth={0}
                    name="CI trên (95%)"
                    connectNulls={false}
                  />
                  <Area
                    type="monotone"
                    dataKey="lower"
                    stroke="transparent"
                    fill="#fff"
                    strokeWidth={0}
                    name="CI dưới (95%)"
                    connectNulls={false}
                  />
                </>
              )}

              {/* Forecast line */}
              <Area
                type="monotone"
                dataKey="forecast"
                stroke="#0d9488"
                fill="url(#colorForecast)"
                strokeWidth={2}
                strokeDasharray="6 3"
                dot={{ r: 2, fill: '#0d9488' }}
                name="Dự báo"
                connectNulls={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap items-center gap-6 text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-blue-500 rounded"></div>
            <span>Dữ liệu lịch sử (products_tiki_history)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-teal-500 rounded" style={{ borderTop: '2px dashed #0d9488', background: 'none' }}></div>
            <span>Dự báo — Linear Regression (ASG2 Q2)</span>
          </div>
          {showCI && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-3 rounded" style={{ background: 'rgba(13,148,136,0.15)', border: '1px solid rgba(13,148,136,0.3)' }}></div>
              <span>95% Confidence Interval (±20%)</span>
            </div>
          )}
          <div className="ml-auto italic text-gray-400">
            Dữ liệu lịch sử: {currentForecast.historical.length} ngày — Nguồn: 9,625 bản ghi tiki_history
          </div>
        </div>
      </div>

      {/* Inventory Planning Note */}
      <div className="glass-panel p-4 rounded-2xl border border-amber-200 bg-amber-50">
        <div className="flex items-start gap-3">
          <Zap className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-amber-800 mb-1 font-mono">Hướng dẫn lập kế hoạch tồn kho (ASG3 Tab 4)</h4>
            <p className="text-xs text-amber-700 leading-relaxed">
              Nếu biểu đồ dự báo cho thấy sold_count tăng đột biến trong {daysAhead} ngày tới, hãy đặt hàng <strong>trước 10–14 ngày</strong> để tránh hết hàng.
              Sử dụng đường CI trên (95%) làm kịch bản "worst-case demand" khi hoạch định tồn kho an toàn.
            </p>
          </div>
        </div>
      </div>

    </div>
  );
}
