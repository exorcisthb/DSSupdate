import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, Cell, ZAxis
} from 'recharts';
import {
  TrendingUp, AlertTriangle, DollarSign, Target, Award, Info,
  ChevronDown, ChevronUp, Activity
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const formatCurrency = (val) => {
  if (!val && val !== 0) return '—';
  if (val >= 1_000_000_000) return (val / 1_000_000_000).toFixed(2) + ' tỷ';
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + ' tr';
  if (val >= 1_000) return (val / 1_000).toFixed(0) + ' K';
  return val.toLocaleString('vi-VN');
};

const DECISION_CONFIG = {
  'ĐẦU TƯ MẠNH': { color: '#10b981', bg: 'bg-emerald-50', border: 'border-emerald-300', text: 'text-emerald-700' },
  'ĐẦU TƯ CÓ KIỂM SOÁT': { color: '#f59e0b', bg: 'bg-amber-50', border: 'border-amber-300', text: 'text-amber-700' },
  'DUY TRÌ': { color: '#3b82f6', bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-700' },
  'THEO DÕI': { color: '#8b5cf6', bg: 'bg-purple-50', border: 'border-purple-300', text: 'text-purple-700' },
  'THOÁT / TÁI CẤU TRÚC': { color: '#ef4444', bg: 'bg-red-50', border: 'border-red-300', text: 'text-red-700' },
};

export default function StrategyDashboard() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortField, setSortField] = useState('growth_rate_pct');
  const [sortAsc, setSortAsc] = useState(false);
  const [selectedL1, setSelectedL1] = useState('All');

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/category/insights`)
      .then(r => r.json())
      .then(d => {
        if (d.error) throw new Error(d.error);
        setData(d);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const l1Options = ['All', ...new Set(data.map(d => d.category_l1))];

  const filtered = data.filter(d => selectedL1 === 'All' || d.category_l1 === selectedL1);

  const sorted = [...filtered].sort((a, b) => {
    const va = a[sortField] ?? 0;
    const vb = b[sortField] ?? 0;
    return sortAsc ? va - vb : vb - va;
  });

  const toggleSort = (field) => {
    if (sortField === field) setSortAsc(!sortAsc);
    else { setSortField(field); setSortAsc(false); }
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return null;
    return sortAsc ? <ChevronUp className="w-3 h-3 inline" /> : <ChevronDown className="w-3 h-3 inline" />;
  };

  // Scatter data for growth vs risk
  const scatterData = filtered.map(d => ({
    x: d.risk_score,
    y: d.growth_rate_pct,
    z: d.rev_per_sku,
    name: d.category_l2,
    decision: d.decision,
    profit: d.profit_proxy,
  }));

  // Top growing
  const topGrowing = [...filtered].sort((a, b) => b.growth_rate_pct - a.growth_rate_pct).slice(0, 10);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-3"></div>
          <p className="text-gray-500 text-sm">Đang phân tích dữ liệu ngành hàng...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 rounded-2xl border border-red-200 bg-red-50">
        <p className="text-center text-red-600 font-medium">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="rounded-2xl border-2 border-indigo-200 bg-gradient-to-r from-indigo-50 to-blue-50 p-5 shadow-md">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center flex-shrink-0">
            <Target className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-indigo-800 font-mono">Bảng điều khiển Chiến lược & Quyết định</h3>
            <p className="text-xs text-indigo-700 mt-0.5">
              Tăng trưởng (5 ngày) × Rủi ro (rating, delivery, chính hãng) × Lợi nhuận ước tính.
              Dữ liệu từ lịch sử Tiki 5 ngày gần nhất (17/07 – 21/07/2026).
            </p>
          </div>
        </div>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-emerald-200 p-4 shadow-sm">
          <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Nên đầu tư</div>
          <div className="text-2xl font-bold font-mono text-emerald-600">
            {data.filter(d => d.decision === 'ĐẦU TƯ MẠNH').length}
          </div>
          <div className="text-[10px] text-gray-500">ngành tăng trưởng cao, rủi ro thấp</div>
        </div>
        <div className="bg-white rounded-xl border border-amber-200 p-4 shadow-sm">
          <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Đầu tư có kiểm soát</div>
          <div className="text-2xl font-bold font-mono text-amber-600">
            {data.filter(d => d.decision === 'ĐẦU TƯ CÓ KIỂM SOÁT').length}
          </div>
          <div className="text-[10px] text-gray-500">tăng trưởng nóng, rủi ro cao</div>
        </div>
        <div className="bg-white rounded-xl border border-blue-200 p-4 shadow-sm">
          <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Duy trì</div>
          <div className="text-2xl font-bold font-mono text-blue-600">
            {data.filter(d => d.decision === 'DUY TRÌ').length}
          </div>
          <div className="text-[10px] text-gray-500">tăng trưởng ổn định, rủi ro thấp</div>
        </div>
        <div className="bg-white rounded-xl border border-red-200 p-4 shadow-sm">
          <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Thoát / Tái cấu trúc</div>
          <div className="text-2xl font-bold font-mono text-red-600">
            {data.filter(d => d.decision === 'THOÁT / TÁI CẤU TRÚC').length}
          </div>
          <div className="text-[10px] text-gray-500">suy giảm hoặc rủi ro quá cao</div>
        </div>
      </div>

      {/* L1 Filter */}
      <div className="flex gap-2 flex-wrap">
        {l1Options.map(opt => (
          <button key={opt}
            onClick={() => setSelectedL1(opt)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              selectedL1 === opt
                ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20'
                : 'bg-white text-gray-600 hover:bg-indigo-50 border border-indigo-200'
            }`}
          >
            {opt === 'All' ? 'Tất cả' : opt}
          </button>
        ))}
      </div>

      {/* Growth vs Risk Scatter Matrix */}
      {scatterData.length > 0 && (
        <div className="bg-white rounded-2xl border border-indigo-200 p-5 shadow-sm">
          <h4 className="text-xs font-bold font-mono text-indigo-800 mb-3 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" /> Ma trận Tăng trưởng × Rủi ro
          </h4>
          <div className="text-[10px] text-gray-500 mb-3">Kích thước bong bóng = Doanh thu/SKU. Màu sắc = Quyết định.</div>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 10, right: 30, bottom: 30, left: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" dataKey="x" name="Risk Score" label={{ value: 'Rủi ro →', position: 'bottom', offset: -10, style: { fontSize: 11, fill: '#6b7280' } }} tick={{ fontSize: 10 }} domain={[0, 100]} />
              <YAxis type="number" dataKey="y" name="Growth %" label={{ value: 'Tăng trưởng % →', angle: -90, position: 'insideLeft', style: { fontSize: 11, fill: '#6b7280', textAnchor: 'middle' } }} tick={{ fontSize: 10 }} />
              <ZAxis type="number" dataKey="z" range={[60, 400]} />
              <Tooltip
                formatter={(value, name) => {
                  if (name === 'x') return [value, 'Rủi ro'];
                  if (name === 'y') return [value.toFixed(1) + '%', 'Tăng trưởng'];
                  if (name === 'z') return [formatCurrency(value), 'Rev/SKU'];
                  return [value, name];
                }}
                labelFormatter={(idx) => scatterData[idx]?.name || ''}
              />
              <Scatter data={scatterData.map((d, i) => ({ ...d, idx: i }))} dataKey="y" xKey="x" zKey="z" fill="#8884d8">
                {scatterData.map((entry, index) => (
                  <Cell key={index} fill={DECISION_CONFIG[entry.decision]?.color || '#6b7280'} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          {/* Legend */}
          <div className="flex flex-wrap gap-3 mt-3">
            {Object.entries(DECISION_CONFIG).map(([key, cfg]) => (
              <div key={key} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cfg.color }} />
                <span className="text-[10px] text-gray-600">{key}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Growing Bar Chart */}
      {topGrowing.length > 0 && (
        <div className="bg-white rounded-2xl border border-indigo-200 p-5 shadow-sm">
          <h4 className="text-xs font-bold font-mono text-indigo-800 mb-3 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5" /> Top 10 ngành tăng trưởng nhanh nhất
          </h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topGrowing} margin={{ top: 5, right: 20, bottom: 60, left: 20 }} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10 }} domain={[0, 'auto']} tickFormatter={(v) => v + '%'} />
              <YAxis type="category" dataKey="category_l2" width={160} tick={{ fontSize: 10 }} />
              <Tooltip formatter={(value) => [value.toFixed(2) + '%', 'Tăng trưởng 5 ngày']} />
              <Bar dataKey="growth_rate_pct" radius={[0, 4, 4, 0]}>
                {topGrowing.map((entry, idx) => (
                  <Cell key={idx} fill={DECISION_CONFIG[entry.decision]?.color || '#6366f1'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Category Ranking Table */}
      <div className="bg-white rounded-2xl border border-indigo-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-indigo-100 flex items-center justify-between">
          <h4 className="text-xs font-bold font-mono text-indigo-800 flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5" /> Xếp hạng ngành hàng chi tiết
          </h4>
          <span className="text-[10px] text-gray-500">{sorted.length} ngành</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-indigo-50 text-[10px] text-gray-600 uppercase font-semibold">
                <th className="py-3 px-4 text-left">Ngành hàng</th>
                <th className="py-3 px-3 text-right cursor-pointer select-none hover:text-indigo-700" onClick={() => toggleSort('growth_rate_pct')}>
                  Tăng trưởng <SortIcon field="growth_rate_pct" />
                </th>
                <th className="py-3 px-3 text-right cursor-pointer select-none hover:text-indigo-700" onClick={() => toggleSort('risk_score')}>
                  Rủi ro <SortIcon field="risk_score" />
                </th>
                <th className="py-3 px-3 text-right cursor-pointer select-none hover:text-indigo-700" onClick={() => toggleSort('profit_proxy')}>
                  Lợi nhuận <SortIcon field="profit_proxy" />
                </th>
                <th className="py-3 px-3 text-right cursor-pointer select-none hover:text-indigo-700" onClick={() => toggleSort('rev_per_sku')}>
                  Rev/SKU <SortIcon field="rev_per_sku" />
                </th>
                <th className="py-3 px-3 text-right cursor-pointer select-none hover:text-indigo-700" onClick={() => toggleSort('opportunity_score')}>
                  Cơ hội <SortIcon field="opportunity_score" />
                </th>
                <th className="py-3 px-3 text-center">Số lượng bán</th>
                <th className="py-3 px-4 text-center">Quyết định</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-indigo-100">
              {sorted.map((item, idx) => {
                const cfg = DECISION_CONFIG[item.decision] || DECISION_CONFIG['THEO DÕI'];
                return (
                  <tr key={idx} className="hover:bg-indigo-50/50 transition duration-150">
                    <td className="py-2.5 px-4">
                      <span className="font-semibold text-gray-800">{item.category_l2}</span>
                      <span className="text-[9px] text-gray-400 block">{item.category_l1}</span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono tabular-nums">
                      <span className={item.growth_rate_pct >= 0 ? 'text-emerald-600' : 'text-red-500'}>
                        {item.growth_rate_pct >= 0 ? '+' : ''}{item.growth_rate_pct}%
                      </span>
                      <span className="text-[9px] text-gray-400 block">{item.growth_label}</span>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <span className={`font-mono font-semibold ${
                        item.risk_level === 'Cao' ? 'text-red-600' :
                        item.risk_level === 'Trung bình' ? 'text-amber-600' : 'text-emerald-600'
                      }`}>
                        {item.risk_score}
                      </span>
                      <span className="text-[9px] text-gray-400 block">{item.risk_level}</span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-blue-600 font-semibold">
                      {formatCurrency(item.profit_proxy)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-gray-700">
                      {formatCurrency(item.rev_per_sku)}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <span className={`font-mono font-bold ${
                        item.opportunity_score >= 60 ? 'text-emerald-600' :
                        item.opportunity_score >= 35 ? 'text-amber-600' : 'text-gray-400'
                      }`}>
                        {item.opportunity_score.toFixed(1)}
                      </span>
                      <span className="text-[9px] text-gray-400 block" title="Rev/SKU norm | Sold share | Dom advantage">
                        {item.rev_sku_norm_pct?.toFixed(0) || '0'}% / {item.sold_share_pct?.toFixed(1) || '0'}% / {item.dom_advantage_pct?.toFixed(0) || '0'}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-gray-600">
                      {item.tiki_sold.toLocaleString('vi-VN')}
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${cfg.bg} ${cfg.text} ${cfg.border} border`}>
                        {item.decision}
                      </span>
                      <div className="text-[9px] text-gray-500 mt-0.5 max-w-[160px] leading-tight">{item.decision_detail}</div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Methodology Note */}
      <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-4">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5" />
          <div className="text-[10px] text-indigo-700 leading-relaxed">
            <strong>Phương pháp tính:</strong><br />
            • <strong>Tăng trưởng</strong> = Tốc độ tăng trưởng sold_count trung bình mỗi ngày từ 5 ngày lịch sử Tiki (17–21/07/2026). Công thức: (sold_ngày_cuối / sold_ngày_đầu)^(1/số_ngày) − 1.<br />
            • <strong>Rủi ro</strong> = Điểm tổng hợp từ (rating thấp: 0–40đ) + (giao hàng chậm: 0–30đ) + (thống trị chính hãng: 0–20đ) + (giảm giá sâu: 0–10đ). Thang 0–100.<br />
            • <strong>Lợi nhuận ước tính</strong> = Rev/SKU × (1 − tỉ lệ giảm giá). Chưa có dữ liệu chi phí thực tế (COGS, phí vận hành).<br />
            • <strong>Tỉ lệ hoàn hàng</strong> hiện chưa có trong cơ sở dữ liệu. Rủi ro được ước lượng qua các chỉ số proxy.
          </div>
        </div>
      </div>

      {/* Q1 Opportunity Score Explanation */}
      <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4">
        <div className="flex items-start gap-2">
          <Award className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div className="text-[10px] text-emerald-800 leading-relaxed">
            <strong>OPPORTUNITY SCORE (ASG2 Q1) — Cơ hội cho Seller nhỏ</strong><br />
            <strong>Cơ hội</strong> = 0.4 × RevSKU_norm + 0.3 × SoldShare + 0.3 × (1 − OfficialDom).<br />
            • <strong>RevSKU_norm</strong> (% đầu tiên): Doanh thu/SKU đã chuẩn hóa (cao = ngách có doanh thu tốt).<br />
            • <strong>SoldShare</strong> (% giữa): Thị phần sản lượng bán của ngách (cao = nhu cầu lớn).<br />
            • <strong>DomAdvantage</strong> (% cuối): (1 − OfficialDom) — ngách ít bị áp đảo bởi hàng chính hãng thì seller nhỏ dễ cạnh tranh.<br />
            <strong>Cách xem:</strong> Sắp xếp bảng theo cột "Cơ hội" giảm dần → ngách đầu bảng là tốt nhất cho seller nhỏ.
          </div>
        </div>
      </div>

    </div>
  );
}
