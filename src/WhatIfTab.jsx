import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Cell
} from 'recharts';
import {
  Zap, TrendingUp, DollarSign, Target, Award, Info,
  CheckCircle2, ChevronRight, ArrowRight
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

const formatCurrency = (val) => {
  if (!val && val !== 0) return '—';
  if (val >= 1_000_000_000) return (val / 1_000_000_000).toFixed(2) + ' tỷ đ';
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(0) + ' triệu đ';
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })
    .format(val).replace('₫', 'đ');
};

const SCENARIO_COLORS = {
  base: { bg: 'bg-teal-50', border: 'border-teal-300', accent: '#0d9488', badge: 'bg-teal-500 text-white' },
  budget_cut: { bg: 'bg-red-50', border: 'border-red-300', accent: '#ef4444', badge: 'bg-red-500 text-white' },
  budget_expand: { bg: 'bg-emerald-50', border: 'border-emerald-300', accent: '#10b981', badge: 'bg-emerald-500 text-white' },
  fee_change: { bg: 'bg-amber-50', border: 'border-amber-300', accent: '#f59e0b', badge: 'bg-amber-500 text-white' },
};

const CATEGORY_COLORS = [
  '#0d9488', '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'
];

const ACTION_LABEL = {
  base: 'Cơ bản',
  budget_cut: '−20% Ngân sách',
  budget_expand: '+30% Ngân sách',
  fee_change: 'Tăng phí sàn',
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
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-3"></div>
          <p className="text-gray-500 text-sm">Đang chạy mô hình LP Capital Allocation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-red-200 bg-red-50">
        <p className="text-center text-red-600 font-medium">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const current = data.scenarios[selectedScenario];
  const scenId = current.scenario_id;
  const colors = SCENARIO_COLORS[scenId] || SCENARIO_COLORS.base;

  // Chart data: allocation per category
  const chartData = current.allocation.map((a, i) => ({
    name: a.category.replace("Men's ", ''),
    allocated: a.allocated / 1_000_000,
    roi: a.roi,
    expected: a.expected_return / 1_000_000,
    fill: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
  }));

  // Comparison chart: portfolio ROI across scenarios
  const comparisonData = data.scenarios.map(s => ({
    name: ACTION_LABEL[s.scenario_id] || s.scenario_name,
    'ROI danh mục': s.summary.portfolio_roi,
    'Lợi nhuận kỳ vọng (tỷ đ)': s.summary.expected_total_return / 1_000_000_000,
  }));

  return (
    <div className="space-y-6">

      {/* Header + Model Info */}
      <div className="glass-panel p-5 rounded-2xl border border-teal-200 bg-white">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold font-mono tracking-wider uppercase text-gray-800 flex items-center gap-2">
              <Zap className="w-5 h-5 text-teal-500" />
              Capital Allocator — What-If Scenarios
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Mô hình LP tối ưu phân bổ vốn theo <strong>ASG2 Câu hỏi 5</strong>
            </p>
          </div>

          {/* LP Model Info box */}
          <div className="bg-teal-50 border border-teal-200 rounded-xl px-4 py-3 text-xs text-gray-700 min-w-[260px]">
            <div className="font-bold text-teal-700 font-mono mb-1.5 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5" /> Mô hình LP (ASG2 Q5)
            </div>
            <div className="space-y-0.5 font-mono">
              <div><span className="text-gray-500">Mục tiêu:</span> max Σ(ROI<sub>i</sub> × Alloc<sub>i</sub>)</div>
              <div><span className="text-gray-500">Ràng buộc:</span> Σ(Alloc<sub>i</sub>) ≤ Budget</div>
              <div><span className="text-gray-500">Safety stock:</span> ≥ 10M VND/danh mục</div>
              <div><span className="text-gray-500">Cap:</span> ≤ 500M VND/danh mục</div>
            </div>
          </div>
        </div>
      </div>

      {/* Scenario Selector */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {data.scenarios.map((s, idx) => {
          const sid = s.scenario_id;
          const col = SCENARIO_COLORS[sid] || SCENARIO_COLORS.base;
          const isActive = selectedScenario === idx;
          return (
            <button
              key={idx}
              onClick={() => setSelectedScenario(idx)}
              className={`rounded-xl p-4 text-left transition-all border-2 ${
                isActive
                  ? `${col.bg} ${col.border} shadow-lg scale-[1.02]`
                  : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-md'
              }`}
            >
              <div className={`text-[10px] font-bold font-mono tracking-wider px-2 py-0.5 rounded-full w-fit mb-2 ${
                isActive ? col.badge : 'bg-gray-100 text-gray-500'
              }`}>
                {ACTION_LABEL[sid] || s.scenario_name}
              </div>
              <div className={`text-base font-bold font-mono ${isActive ? 'text-gray-900' : 'text-gray-700'}`}>
                {s.parameters.budget_vnd}
              </div>
              <div className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                ROI: <span className="font-bold text-gray-700">{s.summary.portfolio_roi.toFixed(2)}×</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Scenario Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left: Description + Summary KPIs */}
        <div className="space-y-4">

          {/* Description */}
          <div className={`glass-panel p-4 rounded-2xl border ${colors.border} ${colors.bg}`}>
            <h3 className="text-xs font-bold font-mono uppercase text-gray-700 mb-2 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5 text-teal-600" /> Mô tả kịch bản
            </h3>
            <p className="text-xs text-gray-600 leading-relaxed">{current.description}</p>
          </div>

          {/* KPI Cards */}
          <div className="glass-panel p-4 rounded-2xl border border-emerald-200 bg-white space-y-3">
            <h3 className="text-xs font-bold font-mono uppercase text-gray-700">Kết quả dự kiến</h3>

            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-xs text-gray-500">Tổng ngân sách</span>
              <span className="font-bold font-mono text-sm text-teal-700">{formatCurrency(current.budget)}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-xs text-gray-500">Portfolio ROI</span>
              <span className="font-bold font-mono text-sm text-emerald-600">{current.summary.portfolio_roi.toFixed(2)}×</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-xs text-gray-500">Lợi nhuận kỳ vọng</span>
              <span className="font-bold font-mono text-sm text-gray-800">{formatCurrency(current.summary.expected_total_return)}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-xs text-gray-500">Danh mục ưu tiên #1</span>
              <span className="font-bold text-xs text-teal-700">{current.summary.top_category}</span>
            </div>
          </div>

          {/* Allocation table */}
          <div className="glass-panel rounded-2xl border border-gray-200 bg-white overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
              <h3 className="text-xs font-bold font-mono uppercase text-gray-700">Phân bổ vốn chi tiết</h3>
            </div>
            <div className="divide-y divide-gray-50">
              {current.allocation.map((a, i) => (
                <div key={i} className="px-4 py-2.5 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }}
                    />
                    <span className="text-xs font-medium text-gray-700 truncate">
                      {a.category.replace("Men's ", '')}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-xs font-mono text-gray-500">ROI {a.roi.toFixed(2)}×</span>
                    <span className="text-xs font-bold font-mono text-teal-700 w-20 text-right">
                      {formatCurrency(a.allocated)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Charts */}
        <div className="lg:col-span-2 space-y-4">

          {/* Bar chart: allocation per category */}
          <div className="glass-panel p-5 rounded-2xl border border-emerald-200 bg-white">
            <h3 className="text-sm font-bold font-mono uppercase text-gray-700 mb-4">
              Phân bổ vốn — {current.scenario_name}
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d1fae5" />
                  <XAxis
                    dataKey="name"
                    stroke="#6b7280"
                    fontSize={10}
                    angle={-15}
                    textAnchor="end"
                    height={50}
                  />
                  <YAxis
                    stroke="#6b7280"
                    fontSize={10}
                    tickFormatter={(v) => `${v}M`}
                  />
                  <Tooltip
                    formatter={(value, name) => [
                      name === 'allocated' ? `${value.toFixed(0)} triệu đ` : `${value.toFixed(2)}×`,
                      name === 'allocated' ? 'Vốn phân bổ' : 'ROI'
                    ]}
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #d1fae5',
                      borderRadius: '8px',
                      fontSize: '11px'
                    }}
                  />
                  <Bar dataKey="allocated" name="Vốn (triệu đ)" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Comparison chart: all scenarios */}
          <div className="glass-panel p-5 rounded-2xl border border-emerald-200 bg-white">
            <h3 className="text-sm font-bold font-mono uppercase text-gray-700 mb-4">
              So sánh 4 kịch bản — Portfolio ROI
            </h3>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData} margin={{ top: 5, right: 20, left: 0, bottom: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d1fae5" />
                  <XAxis
                    dataKey="name"
                    stroke="#6b7280"
                    fontSize={9}
                    angle={-10}
                    textAnchor="end"
                    height={50}
                  />
                  <YAxis stroke="#6b7280" fontSize={9} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #d1fae5',
                      borderRadius: '8px',
                      fontSize: '11px'
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '8px' }} />
                  <Bar dataKey="ROI danh mục" fill="#0d9488" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="Lợi nhuận kỳ vọng (tỷ đ)" fill="#10b981" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Best Scenario Panel */}
      <div className="glass-panel p-5 rounded-2xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-teal-50">
        <div className="flex items-start gap-3">
          <Award className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div className="flex-grow">
            <h3 className="text-sm font-bold text-gray-800 mb-2 font-mono">
              Khuyến nghị từ mô hình LP (ASG2 Q5)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="bg-white/70 rounded-xl p-3 border border-emerald-200">
                <div className="text-xs font-semibold text-emerald-700 mb-1 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> ROI tổng danh mục cao nhất
                </div>
                <div className="font-bold text-gray-800">{data.comparison.best_for_roi}</div>
              </div>
              <div className="bg-white/70 rounded-xl p-3 border border-teal-200">
                <div className="text-xs font-semibold text-teal-700 mb-1 flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5" /> Lợi nhuận tuyệt đối cao nhất
                </div>
                <div className="font-bold text-gray-800">{data.comparison.best_for_return}</div>
              </div>
            </div>
            <div className="mt-3 text-xs text-gray-600 bg-white/60 rounded-lg p-3 border border-emerald-100 leading-relaxed">
              <strong className="text-emerald-700">Insight chính:</strong> {data.comparison.key_insight}
            </div>
          </div>
        </div>
      </div>

      {/* LP Reference Data */}
      {data.model_reference && (
        <div className="glass-panel p-4 rounded-2xl border border-gray-200 bg-gray-50">
          <h4 className="text-xs font-bold font-mono uppercase text-gray-600 mb-3 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-gray-400" /> Thông số mô hình LP (ASG2 Q5)
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <div className="font-semibold text-gray-700 mb-1">Hàm mục tiêu</div>
              <code className="bg-white px-2 py-1 rounded border border-gray-200 text-teal-700">
                {data.model_reference.objective}
              </code>
            </div>
            <div>
              <div className="font-semibold text-gray-700 mb-1">Ràng buộc</div>
              <ul className="space-y-0.5 text-gray-600">
                {data.model_reference.constraints.map((c, i) => (
                  <li key={i} className="flex items-center gap-1">
                    <ChevronRight className="w-3 h-3 text-teal-500" /> {c}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="font-semibold text-gray-700 mb-1">ROI weights</div>
              <ul className="space-y-0.5 text-gray-600">
                {Object.entries(data.model_reference.roi_weights).map(([k, v]) => (
                  <li key={k} className="flex items-center justify-between">
                    <span>{k.replace("Men's ", '')}</span>
                    <span className="font-bold text-emerald-600">{v.toFixed(2)}×</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
