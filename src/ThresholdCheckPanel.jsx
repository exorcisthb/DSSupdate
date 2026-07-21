import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, AlertCircle, Info } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export default function ThresholdCheckPanel({ category }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!category) return;
    setLoading(true);
    const url = `${API_BASE_URL}/api/threshold/check?category=${encodeURIComponent(category)}`;
    fetch(url)
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [category]);

  if (!category) return null;

  return (
    <div className="rounded-xl border border-teal-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <Info className="w-4 h-4 text-teal-600" />
        <span className="text-xs font-bold text-teal-800 uppercase tracking-wider">
          Kiểm tra ngưỡng — {category}
        </span>
      </div>
      {loading ? (
        <div className="text-xs text-gray-500 animate-pulse">Đang kiểm tra ngưỡng...</div>
      ) : data ? (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-3">
            <div className="px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200 text-center min-w-[100px]">
              <div className="text-xs font-bold text-emerald-700">{data.pass_all_count}</div>
              <div className="text-[9px] text-gray-500">Đạt cả 4</div>
            </div>
            <div className="px-3 py-2 rounded-lg bg-yellow-50 border border-yellow-200 text-center min-w-[100px]">
              <div className="text-xs font-bold text-yellow-700">{data.pass_most_count}</div>
              <div className="text-[9px] text-gray-500">Đạt ≥3/4</div>
            </div>
            <div className="px-3 py-2 rounded-lg bg-gray-50 border border-gray-200 text-center min-w-[100px]">
              <div className="text-xs font-bold text-gray-700">{data.total_products}</div>
              <div className="text-[9px] text-gray-500">Tổng SP</div>
            </div>
          </div>
          {data.products && data.products.length > 0 && (
            <div className="max-h-40 overflow-y-auto space-y-1">
              {data.products.slice(0, 10).map((p, i) => (
                <div key={i} className="flex items-center gap-2 text-[10px] p-1.5 rounded bg-gray-50 border border-gray-100">
                  <span className={`flex-shrink-0 ${p.meets_all ? 'text-emerald-500' : p.meets_most ? 'text-yellow-500' : 'text-red-500'}`}>
                    {p.meets_all ? <CheckCircle2 className="w-3.5 h-3.5" /> : p.meets_most ? <AlertCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                  </span>
                  <span className="truncate flex-grow text-gray-700">{p.product_name?.slice(0, 50)}</span>
                  <span className="font-mono text-gray-400 flex-shrink-0">{p.thresholds.pass_rate}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${p.platform === 'Lazada' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'}`}>
                    {p.platform}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="text-xs text-gray-400">Chọn ngách hàng (L2) ở bộ lọc để kiểm tra ngưỡng</div>
      )}
    </div>
  );
}
